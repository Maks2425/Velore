import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from accounts.models import User

from .models import ChatMessage, ChatThread
from .telegram import TelegramError, send_message

logger = logging.getLogger(__name__)

LINK_CODE_TTL = timedelta(minutes=15)
HELP_TEXT = (
    "Команди для консультантів:\n"
    "/threads — відкриті чати\n"
    "/reply <id> <текст> — відповісти клієнту"
)


def _staff_with_telegram():
    return User.objects.filter(telegram_chat_id__isnull=False).filter(Q(is_staff=True) | Q(is_superuser=True))


def _safe_send(chat_id: int, text: str) -> None:
    try:
        send_message(chat_id, text)
    except (TelegramError, OSError):
        logger.exception("Failed to send Telegram message to %s", chat_id)


def notify_new_customer_message(thread: ChatThread, message: ChatMessage) -> None:
    for staff in _staff_with_telegram():
        _safe_send(
            staff.telegram_chat_id,
            f"Чат #{thread.pk} від {thread.customer.username}:\n{message.body}\n\nВідповісти: /reply {thread.pk} текст",
        )


def notify_consultant_message(thread: ChatThread, message: ChatMessage) -> None:
    customer = thread.customer
    if customer.telegram_chat_id:
        _safe_send(customer.telegram_chat_id, f"Консультант: {message.body}")


def _link_account(chat_id: int, code: str) -> None:
    user = User.objects.filter(telegram_link_code=code).first() if code else None
    expired = user is not None and (
        user.telegram_link_code_created_at is None
        or timezone.now() - user.telegram_link_code_created_at > LINK_CODE_TTL
    )
    if user is None or expired:
        _safe_send(chat_id, "Код недійсний або прострочений. Згенеруйте новий на сайті.")
        return

    User.objects.filter(telegram_chat_id=chat_id).update(telegram_chat_id=None)
    user.telegram_chat_id = chat_id
    user.telegram_link_code = ""
    user.telegram_link_code_created_at = None
    user.save(update_fields=["telegram_chat_id", "telegram_link_code", "telegram_link_code_created_at"])
    _safe_send(chat_id, f"Готово! Акаунт {user.username} прив'язано до Velore.")


def _staff_reply(chat_id: int, staff: User, text: str) -> None:
    parts = text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        _safe_send(chat_id, "Формат: /reply <id> <текст>")
        return

    thread = ChatThread.objects.filter(pk=int(parts[1]), is_open=True).select_related("customer").first()
    if thread is None:
        _safe_send(chat_id, "Відкритий чат із таким id не знайдено.")
        return

    if thread.consultant_id is None:
        thread.consultant = staff
    message = ChatMessage.objects.create(
        thread=thread, sender=ChatMessage.Sender.CONSULTANT, author=staff, body=parts[2].strip()
    )
    thread.save(update_fields=["consultant", "updated_at"])
    notify_consultant_message(thread, message)
    _safe_send(chat_id, f"Надіслано в чат #{thread.pk}.")


def _list_threads(chat_id: int) -> None:
    threads = ChatThread.objects.filter(is_open=True).select_related("customer")[:20]
    if not threads:
        _safe_send(chat_id, "Відкритих чатів немає.")
        return
    lines = [f"#{t.pk} — {t.customer.username}" for t in threads]
    _safe_send(chat_id, "Відкриті чати:\n" + "\n".join(lines))


def _customer_message(chat_id: int, user: User, text: str) -> None:
    thread = ChatThread.objects.filter(customer=user, is_open=True).first()
    if thread is None:
        thread = ChatThread.objects.create(customer=user)
    message = ChatMessage.objects.create(
        thread=thread, sender=ChatMessage.Sender.CUSTOMER, author=user, body=text
    )
    thread.save(update_fields=["updated_at"])
    notify_new_customer_message(thread, message)
    _safe_send(chat_id, "Повідомлення надіслано консультанту.")


def handle_update(update: dict) -> None:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat_id = (message.get("chat") or {}).get("id")
    if not text or chat_id is None:
        return

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            _link_account(chat_id, parts[1].strip())
        else:
            _safe_send(chat_id, "Щоб прив'язати акаунт, відкрийте сторінку «Telegram» на сайті.")
        return

    user = User.objects.filter(telegram_chat_id=chat_id).first()
    if user is None:
        _safe_send(chat_id, "Акаунт не прив'язано. Відкрийте сторінку «Telegram» на сайті.")
        return

    is_staff = user.is_staff or user.is_superuser
    if is_staff and text == "/threads":
        _list_threads(chat_id)
    elif is_staff and text.startswith("/reply"):
        _staff_reply(chat_id, user, text)
    elif is_staff:
        _safe_send(chat_id, HELP_TEXT)
    else:
        _customer_message(chat_id, user, text[:1000])
