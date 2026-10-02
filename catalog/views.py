from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Brand, Product


class BrandListView(ListView):
    model = Brand
    template_name = "catalog/brand_list.html"
    context_object_name = "brands"

    def get_queryset(self):
        return Brand.objects.filter(is_active=True)


class BrandDetailView(DetailView):
    model = Brand
    template_name = "catalog/brand_detail.html"
    context_object_name = "brand"
    slug_url_kwarg = "brand_slug"

    def get_queryset(self):
        return Brand.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = (
            Product.objects.available().with_related().filter(brand=self.object)
        )
        context["brands"] = Brand.objects.filter(is_active=True)
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    slug_url_kwarg = "product_slug"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Product.objects.with_related(),
            slug=self.kwargs["product_slug"],
            brand__slug=self.kwargs["brand_slug"],
            is_active=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_products"] = (
            Product.objects.available()
            .with_related()
            .filter(brand=self.object.brand)
            .exclude(pk=self.object.pk)[:4]
        )
        return context
