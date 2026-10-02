from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View

from cart.models import Cart

from .forms import CheckoutForm
from .models import Order, OrderItem, OrderStatusEvent, Payment


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.warning(request, "Ваш кошик порожній.")
        return redirect("cart:view_cart")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    shipping_full_name=form.cleaned_data["shipping_full_name"],
                    shipping_address=form.cleaned_data["shipping_address"],
                    shipping_city=form.cleaned_data["shipping_city"],
                    shipping_postal_code=form.cleaned_data["shipping_postal_code"],
                    shipping_phone=form.cleaned_data["shipping_phone"],
                    total_price=cart.total_price,
                    status=Order.Status.PROCESSING,
                )
                for item in cart.items.select_related("product"):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        unit_price=item.product.price,
                        quantity=item.quantity,
                    )

                card_number = form.cleaned_data.get("demo_card_number", "")
                masked = f"**** **** **** {card_number[-4:]}" if card_number else ""
                Payment.objects.create(
                    order=order,
                    method=form.cleaned_data["payment_method"],
                    status=Payment.Status.SUCCEEDED,
                    masked_reference=masked,
                    amount=cart.total_price,
                )
                OrderStatusEvent.objects.create(
                    order=order,
                    status=Order.Status.PROCESSING,
                    note="Замовлення оформлено та оплачено (демо-оплата).",
                    location="Склад Velore, Київ",
                )
                cart.items.all().delete()

            messages.success(request, f"Замовлення {order.number} успішно створено!")
            return redirect("orders:order_detail", number=order.number)
    else:
        form = CheckoutForm()

    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")


class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    slug_field = "number"
    slug_url_kwarg = "number"

    def get_object(self, queryset=None):
        return get_object_or_404(Order.objects.prefetch_related("items", "status_events"), number=self.kwargs["number"])

    def test_func(self) -> bool:
        order = self.get_object()
        user = self.request.user
        return order.user_id == user.pk or user.is_staff or user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["timeline"] = list(Order.Status.choices)
        return context


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)


class StaffOrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = "orders/staff_order_list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        return Order.objects.select_related("user").prefetch_related("items")


class UpdateOrderStatusView(StaffRequiredMixin, View):
    def post(self, request, number):
        order = get_object_or_404(Order, number=number)
        new_status = request.POST.get("status")
        note = request.POST.get("note", "")
        location = request.POST.get("location", "")

        if new_status not in Order.Status.values:
            messages.error(request, "Невідомий статус.")
            return redirect("orders:staff_order_list")

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        OrderStatusEvent.objects.create(order=order, status=new_status, note=note, location=location)

        messages.success(request, f"Статус замовлення {order.number} оновлено.")
        return redirect("orders:staff_order_list")
