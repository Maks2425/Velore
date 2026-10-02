from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("brands/", views.BrandListView.as_view(), name="brand_list"),
    path("brands/<slug:brand_slug>/", views.BrandDetailView.as_view(), name="brand_detail"),
    path(
        "brands/<slug:brand_slug>/<slug:product_slug>/",
        views.ProductDetailView.as_view(),
        name="product_detail",
    ),
]
