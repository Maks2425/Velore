from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from catalog.models import Brand, Product


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["brands"] = Brand.objects.filter(is_active=True)
        context["featured_products"] = (
            Product.objects.available().with_related().filter(is_featured=True)[:8]
        )
        context["hero_image_url"] = f"{settings.MEDIA_URL}site/runway-hero.jpg"
        return context


@require_POST
def set_language(request):
    """A minimal replacement for django.views.i18n.set_language that also
    persists the choice on the user's account, so Telegram picks it up too.
    """
    language = request.POST.get("language", "")
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"

    response = HttpResponseRedirect(next_url)
    if language in dict(settings.LANGUAGES):
        translation.activate(language)
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language, max_age=settings.LANGUAGE_COOKIE_AGE)
        if request.user.is_authenticated and request.user.language != language:
            request.user.language = language
            request.user.save(update_fields=["language"])
    return response


class RobotsTxtView(TemplateView):
    template_name = "robots.txt"
    content_type = "text/plain"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scheme"] = "https" if self.request.is_secure() else "http"
        context["site_domain"] = self.request.get_host()
        return context
