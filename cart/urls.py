from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.view_cart, name="view_cart"),
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("item/<int:item_id>/update/", views.update_cart_item, name="update_item"),
    path("item/<int:item_id>/remove/", views.remove_from_cart, name="remove_item"),
]
