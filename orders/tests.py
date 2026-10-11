from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from cart.models import Cart, CartItem
from catalog.models import Brand, Category, Product

from .models import Order

User = get_user_model()

CHECKOUT_FORM_DATA = {
    "shipping_full_name": "Тест Тестенко",
    "shipping_address": "вул. Хрещатик 1",
    "shipping_city": "Київ",
    "shipping_postal_code": "01001",
    "shipping_phone": "+380501234567",
    "payment_method": "cash_on_delivery",
}


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer", email="customer@example.com", password="pass12345")
        self.client.force_login(self.user)
        brand = Brand.objects.create(name="Order Brand", slug="order-brand")
        category = Category.objects.create(name="Взуття", slug="shoes")
        self.product = Product.objects.create(
            brand=brand, category=category, name="Sneakers", slug="sneakers",
            price=Decimal("2000.00"), stock=2, sku="VLR-ORDER-SNEAKERS",
        )
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_checkout_creates_order_and_decrements_stock(self):
        response = self.client.post(reverse("orders:checkout"), CHECKOUT_FORM_DATA)

        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse("orders:order_detail", kwargs={"number": order.number}))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)
        self.assertEqual(order.total_price, Decimal("4000.00"))
        self.assertFalse(self.cart.items.exists())

    def test_checkout_sends_confirmation_email(self):
        self.client.post(reverse("orders:checkout"), CHECKOUT_FORM_DATA)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("оформлено", mail.outbox[0].subject.lower() + mail.outbox[0].body.lower())

    def test_checkout_blocks_when_stock_is_insufficient(self):
        self.item.quantity = 5
        self.item.save()

        response = self.client.post(reverse("orders:checkout"), CHECKOUT_FORM_DATA)

        self.assertRedirects(response, reverse("cart:view_cart"))
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)
        self.assertTrue(self.cart.items.exists())


class OrderAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", email="owner@example.com", password="pass12345")
        self.stranger = User.objects.create_user(username="stranger", email="stranger@example.com", password="pass12345")
        self.order = Order.objects.create(
            user=self.owner,
            shipping_full_name="Owner",
            shipping_address="Addr",
            shipping_city="City",
            shipping_postal_code="00000",
            shipping_phone="+380000000000",
            total_price=Decimal("100.00"),
        )

    def test_owner_can_view_their_order(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.order.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_other_customer_cannot_view_order(self):
        self.client.force_login(self.stranger)
        response = self.client.get(self.order.get_absolute_url())
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.order.get_absolute_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class StaffStatusUpdateTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="buyer2", email="buyer2@example.com", password="pass12345")
        self.staff = User.objects.create_user(
            username="staffer", email="staffer@example.com", password="pass12345", is_staff=True
        )
        self.order = Order.objects.create(
            user=self.customer,
            shipping_full_name="Buyer",
            shipping_address="Addr",
            shipping_city="City",
            shipping_postal_code="00000",
            shipping_phone="+380000000000",
            total_price=Decimal("100.00"),
        )

    def test_staff_status_update_sends_email_to_customer(self):
        self.client.force_login(self.staff)

        self.client.post(
            reverse("orders:update_status", kwargs={"number": self.order.number}),
            {"status": Order.Status.SHIPPED, "note": "", "location": "Київ"},
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.SHIPPED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.customer.email])

    def test_non_staff_cannot_update_status(self):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("orders:update_status", kwargs={"number": self.order.number}),
            {"status": Order.Status.SHIPPED},
        )

        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING_PAYMENT)
