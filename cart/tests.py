from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Brand, Category, Product

from .models import Cart, CartItem

User = get_user_model()


class CartFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", email="buyer@example.com", password="pass12345")
        self.client.force_login(self.user)
        brand = Brand.objects.create(name="Cart Brand", slug="cart-brand")
        category = Category.objects.create(name="Одяг", slug="clothing")
        self.product = Product.objects.create(
            brand=brand, category=category, name="Hoodie", slug="hoodie",
            price=Decimal("1500.00"), stock=3, sku="VLR-CART-HOODIE",
        )

    def test_add_to_cart_creates_item(self):
        self.client.post(reverse("cart:add_to_cart", args=[self.product.pk]))

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 1)
        self.assertEqual(cart.total_price, Decimal("1500.00"))

    def test_adding_twice_increments_quantity_instead_of_duplicating(self):
        url = reverse("cart:add_to_cart", args=[self.product.pk])
        self.client.post(url)
        self.client.post(url)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.get().quantity, 2)
        self.assertEqual(cart.total_price, Decimal("3000.00"))

    def test_update_quantity_to_zero_removes_item(self):
        self.client.post(reverse("cart:add_to_cart", args=[self.product.pk]))
        item = CartItem.objects.get(product=self.product)

        self.client.post(reverse("cart:update_item", args=[item.pk]), {"quantity": 0})

        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_update_quantity_is_capped_at_stock(self):
        self.client.post(reverse("cart:add_to_cart", args=[self.product.pk]))
        item = CartItem.objects.get(product=self.product)

        self.client.post(reverse("cart:update_item", args=[item.pk]), {"quantity": 999})

        item.refresh_from_db()
        self.assertEqual(item.quantity, self.product.stock)

    def test_user_cannot_modify_another_users_cart_item(self):
        other = User.objects.create_user(username="other", email="other2@example.com", password="pass12345")
        other_cart = Cart.objects.create(user=other)
        other_item = CartItem.objects.create(cart=other_cart, product=self.product, quantity=1)

        response = self.client.post(reverse("cart:remove_item", args=[other_item.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=other_item.pk).exists())
