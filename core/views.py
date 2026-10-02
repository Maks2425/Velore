from django.views.generic import TemplateView

from catalog.models import Brand, Product


class RobotsTxtView(TemplateView):
    template_name = "robots.txt"
    content_type = "text/plain"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scheme"] = "https" if self.request.is_secure() else "http"
        context["site_domain"] = self.request.get_host()
        return context


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["brands"] = Brand.objects.filter(is_active=True)
        context["featured_products"] = (
            Product.objects.available().with_related().filter(is_featured=True)[:8]
        )
        return context
