from django.conf import settings
from django.db import models
from django.urls import reverse

from catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Очікує оплати"
        PROCESSING = "processing", "Комплектується"
        SHIPPED = "shipped", "Відправлено"
        OUT_FOR_DELIVERY = "out_for_delivery", "У дорозі до вас"
        DELIVERED = "delivered", "Доставлено"
        CANCELLED = "cancelled", "Скасовано"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT)
    shipping_full_name = models.CharField(max_length=150)
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_phone = models.CharField(max_length=32)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.number

    def get_absolute_url(self) -> str:
        return reverse("orders:order_detail", kwargs={"number": self.number})

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number() -> str:
        import uuid

        return f"VLR-{uuid.uuid4().hex[:10].upper()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class OrderStatusEvent(models.Model):
    """One row per tracking-timeline step shown on the order tracking page."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_events")
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    note = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.order.number}: {self.status}"


class Payment(models.Model):
    """A simulated payment record. No real payment processor is involved —
    this project never collects or stores full card numbers, CVV, or any
    real financial credentials, only a mock method and a masked reference.
    """

    class Method(models.TextChoices):
        MOCK_CARD = "mock_card", "Банківська картка (демо)"
        MOCK_WALLET = "mock_wallet", "Velore Pay (демо-гаманець)"
        CASH_ON_DELIVERY = "cash_on_delivery", "Оплата при отриманні"

    class Status(models.TextChoices):
        SUCCEEDED = "succeeded", "Успішно"
        FAILED = "failed", "Відхилено"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCEEDED)
    masked_reference = models.CharField(
        max_length=40, blank=True, help_text="e.g. **** **** **** 4242 — demo data only"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Payment for {self.order.number} ({self.get_method_display()})"
