import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView

from .models import ChatMessage, ChatThread
from .services import AIUnavailable, ai_reply

MAX_AI_HISTORY = 12
MAX_BODY_LENGTH = 1000


def _parse_json(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _is_consultant(user) -> bool:
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _can_access(user, thread: ChatThread) -> bool:
    return thread.customer_id == user.pk or _is_consultant(user)


@require_POST
def ai_chat(request):
    payload = _parse_json(request)
    if payload is None or not isinstance(payload.get("messages"), list):
        return HttpResponseBadRequest("Invalid payload")

    history = []
    for item in payload["messages"][-MAX_AI_HISTORY:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            return HttpResponseBadRequest("Invalid message")
        content = str(item.get("content", "")).strip()[:MAX_BODY_LENGTH]
        if content:
            history.append({"role": item["role"], "content": content})

    if not history or history[-1]["role"] != "user":
        return HttpResponseBadRequest("Expected a user message")

    try:
        reply = ai_reply(history)
    except AIUnavailable:
        return JsonResponse({"error": "AI-помічник тимчасово недоступний."}, status=503)
    except Exception:
        return JsonResponse({"error": "Не вдалося отримати відповідь. Спробуйте пізніше."}, status=502)

    return JsonResponse({"reply": reply})


@login_required
@require_POST
def open_thread(request):
    thread = ChatThread.objects.filter(customer=request.user, is_open=True).first()
    if thread is None:
        thread = ChatThread.objects.create(customer=request.user)
    return JsonResponse({"thread_id": thread.pk})


@login_required
@require_GET
def thread_messages(request, thread_id):
    thread = get_object_or_404(ChatThread, pk=thread_id)
    if not _can_access(request.user, thread):
        return JsonResponse({"error": "forbidden"}, status=403)

    after = request.GET.get("after", "0")
    if not after.isdigit():
        return HttpResponseBadRequest("Invalid cursor")

    messages = thread.messages.filter(pk__gt=int(after)).select_related("author")
    return JsonResponse({
        "messages": [
            {
                "id": m.pk,
                "sender": m.sender,
                "body": m.body,
                "author": m.author.get_username() if m.author else "",
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "consultant": thread.consultant.get_username() if thread.consultant else None,
        "is_open": thread.is_open,
    })


@login_required
@require_POST
def send_message(request, thread_id):
    thread = get_object_or_404(ChatThread, pk=thread_id)
    if not _can_access(request.user, thread):
        return JsonResponse({"error": "forbidden"}, status=403)
    if not thread.is_open:
        return JsonResponse({"error": "Чат закрито."}, status=409)

    payload = _parse_json(request)
    body = str((payload or {}).get("body", "")).strip()
    if not body or len(body) > MAX_BODY_LENGTH:
        return HttpResponseBadRequest("Повідомлення порожнє або занадто довге.")

    is_staff_reply = _is_consultant(request.user) and request.user.pk != thread.customer_id
    if is_staff_reply:
        sender = ChatMessage.Sender.CONSULTANT
        if thread.consultant_id is None:
            thread.consultant = request.user
    else:
        sender = ChatMessage.Sender.CUSTOMER

    message = ChatMessage.objects.create(thread=thread, sender=sender, author=request.user, body=body)
    thread.save(update_fields=["consultant", "updated_at"])
    return JsonResponse({"id": message.pk})


class ConsultantRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return _is_consultant(self.request.user)


class InboxView(ConsultantRequiredMixin, ListView):
    model = ChatThread
    template_name = "chat/inbox.html"
    context_object_name = "threads"

    def get_queryset(self):
        return ChatThread.objects.filter(is_open=True).select_related("customer", "consultant")


@login_required
def thread_detail(request, thread_id):
    thread = get_object_or_404(ChatThread.objects.select_related("customer", "consultant"), pk=thread_id)
    if not _can_access(request.user, thread):
        return render(request, "403.html", status=403)
    return render(request, "chat/thread.html", {"thread": thread})
