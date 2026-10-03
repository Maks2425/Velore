from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .forms import ProductFilterForm
from .models import Brand, Product


class FilteredProductMixin:
    filter_form_class = ProductFilterForm

    def get_filter_form(self):
        if not hasattr(self, "_filter_form"):
            self._filter_form = self.filter_form_class(self.request.GET or None)
        return self._filter_form

    def get_filtered_products(self, base_queryset):
        form = self.get_filter_form()
        queryset = base_queryset.available().with_related()
        if form.is_valid():
            return form.filter_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.get_filter_form()
        query = self.request.GET.copy()
        query.pop("page", None)
        context["filter_query"] = query.urlencode()
        return context


class ShopView(FilteredProductMixin, ListView):
    model = Product
    template_name = "catalog/shop.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        return self.get_filtered_products(Product.objects.all())


class BrandListView(ListView):
    model = Brand
    template_name = "catalog/brand_list.html"
    context_object_name = "brands"

    def get_queryset(self):
        return Brand.objects.filter(is_active=True)


class BrandDetailView(FilteredProductMixin, DetailView):
    model = Brand
    template_name = "catalog/brand_detail.html"
    context_object_name = "brand"
    slug_url_kwarg = "brand_slug"

    def get_queryset(self):
        return Brand.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = self.get_filtered_products(self.object.products.all())
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

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
