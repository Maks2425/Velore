import json
import urllib.request

from django.conf import settings


class TelegramError(Exception):
    pass


def _call(method: str, payload: dict, timeout: int = 15):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN is not configured")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.load(response)
    if not body.get("ok"):
        raise TelegramError(body.get("description", "Telegram API error"))
    return body["result"]


def send_message(chat_id: int, text: str) -> None:
    _call("sendMessage", {"chat_id": chat_id, "text": text[:4000]})


def get_updates(offset: int | None) -> list[dict]:
    payload = {"timeout": 30, "allowed_updates": ["message"]}
    if offset is not None:
        payload["offset"] = offset
    return _call("getUpdates", payload, timeout=40)
