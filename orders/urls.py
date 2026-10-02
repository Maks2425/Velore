from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("my-orders/", views.OrderListView.as_view(), name="order_list"),
    path("my-orders/<str:number>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("manage/", views.StaffOrderListView.as_view(), name="staff_order_list"),
    path("manage/<str:number>/status/", views.UpdateOrderStatusView.as_view(), name="update_status"),
]
