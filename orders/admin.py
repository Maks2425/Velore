from django.contrib import admin

from .models import Order, OrderItem, OrderStatusEvent, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderStatusEventInline(admin.TabularInline):
    model = OrderStatusEvent
    extra = 0


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total_price", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "user__username", "user__email")
    inlines = [OrderItemInline, PaymentInline, OrderStatusEventInline]
    list_select_related = ("user",)
