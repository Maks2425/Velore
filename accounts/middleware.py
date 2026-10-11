from django.conf import settings
from django.utils import translation


class UserLanguageMiddleware:
    """Falls back to the logged-in user's saved language preference when the
    request carries no explicit language cookie yet (e.g. a new browser, or a
    preference set earlier via the Telegram bot's /language command) — so the
    website and Telegram stay in sync. An explicit cookie (set by the
    language switcher) always takes priority; this never overrides it.

    Must run after LocaleMiddleware so its activation wins for this request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and settings.LANGUAGE_COOKIE_NAME not in request.COOKIES:
            translation.activate(request.user.language)
            request.LANGUAGE_CODE = translation.get_language()
        return self.get_response(request)
