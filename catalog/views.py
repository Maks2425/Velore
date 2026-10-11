from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .forms import ProductFilterForm, ReviewForm
from .models import Brand, Product, WishlistItem

PRODUCTS_PER_PAGE = 24


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
    paginate_by = PRODUCTS_PER_PAGE

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
        products = self.get_filtered_products(self.object.products.all())
        paginator = Paginator(products, PRODUCTS_PER_PAGE)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        context["products"] = page_obj
        context["page_obj"] = page_obj
        context["is_paginated"] = page_obj.has_other_pages()
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
        context["reviews"] = self.object.reviews.select_related("user")
        user = self.request.user
        context["user_review"] = (
            self.object.reviews.filter(user=user).first() if user.is_authenticated else None
        )
        context["review_form"] = context.get("review_form") or ReviewForm(instance=context["user_review"])
        if user.is_authenticated:
            context["in_wishlist"] = WishlistItem.objects.filter(user=user, product=self.object).exists()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_authenticated:
            messages.info(request, "Увійдіть в акаунт, щоб залишити відгук.")
            return redirect("accounts:login")

        existing = self.object.reviews.filter(user=request.user).first()
        form = ReviewForm(request.POST, instance=existing)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = self.object
            review.user = request.user
            review.save()
            messages.success(request, "Дякуємо за відгук!")
            return redirect(self.object.get_absolute_url())

        context = self.get_context_data(review_form=form)
        return self.render_to_response(context)


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, f"«{product.name}» видалено з обраного.")
    else:
        messages.success(request, f"«{product.name}» додано в обране.")
    return redirect(request.POST.get("next") or product.get_absolute_url())


class WishlistView(LoginRequiredMixin, ListView):
    template_name = "catalog/wishlist.html"
    context_object_name = "items"

    def get_queryset(self):
        return (
            WishlistItem.objects.filter(user=self.request.user)
            .select_related("product", "product__brand")
            .prefetch_related("product__images")
        )
