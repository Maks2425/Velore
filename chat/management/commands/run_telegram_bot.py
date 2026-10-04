import logging
import time

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from chat.telegram import TelegramError, get_updates
from chat.telegram_bot import handle_update

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the Velore Telegram bot with long polling (no public URL required)."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("Set TELEGRAM_BOT_TOKEN in .env first.")

        self.stdout.write(self.style.SUCCESS("Telegram bot is running. Press Ctrl+C to stop."))
        offset = None
        while True:
            try:
                updates = get_updates(offset)
            except TelegramError as exc:
                logger.error("Telegram polling failed: %s", exc)
                time.sleep(5)
                continue
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    handle_update(update)
                except Exception:
                    logger.exception("Failed to handle Telegram update %s", update.get("update_id"))
