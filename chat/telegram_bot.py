import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from accounts.models import User

from .models import ChatMessage, ChatThread
from .telegram import TelegramError, send_message

logger = logging.getLogger(__name__)

LINK_CODE_TTL = timedelta(minutes=15)


def _staff_with_telegram():
    return User.objects.filter(telegram_chat_id__isnull=False).filter(Q(is_staff=True) | Q(is_superuser=True))


def _safe_send(chat_id: int, text: str) -> None:
    try:
        send_message(chat_id, text)
    except (TelegramError, OSError):
        logger.exception("Failed to send Telegram message to %s", chat_id)


def _send_for(user: User | None, chat_id: int, text: str) -> None:
    """Send a (lazy, to-be-translated) string using the recipient's saved
    language, falling back to the site default for not-yet-linked chats."""
    language = user.language if user is not None else settings.LANGUAGE_CODE
    with translation.override(language):
        _safe_send(chat_id, str(text))


def notify_new_customer_message(thread: ChatThread, message: ChatMessage) -> None:
    for staff in _staff_with_telegram():
        with translation.override(staff.language):
            text = _("Чат #{number} від {username}:\n{body}\n\nВідповісти: /reply {number} текст").format(
                number=thread.pk, username=thread.customer.username, body=message.body
            )
        _safe_send(staff.telegram_chat_id, text)


def notify_consultant_message(thread: ChatThread, message: ChatMessage) -> None:
    customer = thread.customer
    if customer.telegram_chat_id:
        with translation.override(customer.language):
            text = _("Консультант: {body}").format(body=message.body)
        _safe_send(customer.telegram_chat_id, text)


def _link_account(chat_id: int, code: str) -> None:
    user = User.objects.filter(telegram_link_code=code).first() if code else None
    expired = user is not None and (
        user.telegram_link_code_created_at is None
        or timezone.now() - user.telegram_link_code_created_at > LINK_CODE_TTL
    )
    if user is None or expired:
        _send_for(None, chat_id, _("Код недійсний або прострочений. Згенеруйте новий на сайті."))
        return

    User.objects.filter(telegram_chat_id=chat_id).update(telegram_chat_id=None)
    user.telegram_chat_id = chat_id
    user.telegram_link_code = ""
    user.telegram_link_code_created_at = None
    user.save(update_fields=["telegram_chat_id", "telegram_link_code", "telegram_link_code_created_at"])
    with translation.override(user.language):
        text = _("Готово! Акаунт {username} прив'язано до Velore.").format(username=user.username)
    _safe_send(chat_id, text)


def _staff_reply(chat_id: int, staff: User, text: str) -> None:
    parts = text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        _send_for(staff, chat_id, _("Формат: /reply <id> <текст>"))
        return

    thread = ChatThread.objects.filter(pk=int(parts[1]), is_open=True).select_related("customer").first()
    if thread is None:
        _send_for(staff, chat_id, _("Відкритий чат із таким id не знайдено."))
        return

    if thread.consultant_id is None:
        thread.consultant = staff
    message = ChatMessage.objects.create(
        thread=thread, sender=ChatMessage.Sender.CONSULTANT, author=staff, body=parts[2].strip()
    )
    thread.save(update_fields=["consultant", "updated_at"])
    notify_consultant_message(thread, message)
    with translation.override(staff.language):
        text = _("Надіслано в чат #{number}.").format(number=thread.pk)
    _safe_send(chat_id, text)


def _list_threads(chat_id: int, staff: User) -> None:
    threads = ChatThread.objects.filter(is_open=True).select_related("customer")[:20]
    if not threads:
        _send_for(staff, chat_id, _("Відкритих чатів немає."))
        return
    lines = [f"#{t.pk} — {t.customer.username}" for t in threads]
    with translation.override(staff.language):
        text = _("Відкриті чати:") + "\n" + "\n".join(lines)
    _safe_send(chat_id, text)


def _customer_message(chat_id: int, user: User, text: str) -> None:
    thread = ChatThread.objects.filter(customer=user, is_open=True).first()
    if thread is None:
        thread = ChatThread.objects.create(customer=user)
    message = ChatMessage.objects.create(
        thread=thread, sender=ChatMessage.Sender.CUSTOMER, author=user, body=text
    )
    thread.save(update_fields=["updated_at"])
    notify_new_customer_message(thread, message)
    _send_for(user, chat_id, _("Повідомлення надіслано консультанту."))


def _help_text(user: User) -> str:
    with translation.override(user.language):
        return (
            _("Команди для консультантів:")
            + "\n/threads — "
            + _("відкриті чати")
            + "\n/reply <id> <текст> — "
            + _("відповісти клієнту")
            + "\n/language <uk|en> — "
            + _("змінити мову")
        )


def _set_language(chat_id: int, user: User, requested: str) -> None:
    available = dict(settings.LANGUAGES)
    requested = requested.strip().lower()
    if not requested:
        with translation.override(user.language):
            options = ", ".join(available)
            text = _("Поточна мова: {language}. Доступні варіанти: {options}.").format(
                language=available.get(user.language, user.language), options=options
            )
        _safe_send(chat_id, text)
        return

    if requested not in available:
        _send_for(user, chat_id, _("Невідома мова. Доступні варіанти: {options}.").format(options=", ".join(available)))
        return

    user.language = requested
    user.save(update_fields=["language"])
    with translation.override(requested):
        text = _("Мову змінено на {language}.").format(language=available[requested])
    _safe_send(chat_id, text)


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
            _send_for(None, chat_id, _("Щоб прив'язати акаунт, відкрийте сторінку «Telegram» на сайті."))
        return

    user = User.objects.filter(telegram_chat_id=chat_id).first()
    if user is None:
        _send_for(None, chat_id, _("Акаунт не прив'язано. Відкрийте сторінку «Telegram» на сайті."))
        return

    if text.startswith("/language"):
        _set_language(chat_id, user, text[len("/language"):])
        return

    is_staff = user.is_staff or user.is_superuser
    if is_staff and text == "/threads":
        _list_threads(chat_id, user)
    elif is_staff and text.startswith("/reply"):
        _staff_reply(chat_id, user, text)
    elif is_staff:
        _safe_send(chat_id, _help_text(user))
    else:
        _customer_message(chat_id, user, text[:1000])
