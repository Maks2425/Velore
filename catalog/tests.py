from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Brand, Category, Product, Review, WishlistItem

User = get_user_model()


def make_product(**overrides):
    brand = overrides.pop("brand", None)
    if brand is None:
        brand, _ = Brand.objects.get_or_create(slug="test-brand", defaults={"name": "Test Brand"})
    category = overrides.pop("category", None)
    if category is None:
        category, _ = Category.objects.get_or_create(slug="clothing", defaults={"name": "Одяг"})
    defaults = {
        "brand": brand,
        "category": category,
        "name": "Test Hoodie",
        "slug": "test-hoodie",
        "price": Decimal("1000.00"),
        "stock": 5,
        "sku": "VLR-TEST-HOODIE",
    }
    defaults.update(overrides)
    return Product.objects.create(**defaults)


class ProductQuerySetTests(TestCase):
    def test_available_excludes_out_of_stock_and_inactive(self):
        in_stock = make_product(slug="in-stock", sku="VLR-IN-STOCK")
        make_product(slug="out-of-stock", sku="VLR-OUT", stock=0)
        make_product(slug="inactive", sku="VLR-INACTIVE", is_active=False)

        available_slugs = set(Product.objects.available().values_list("slug", flat=True))

        self.assertEqual(available_slugs, {in_stock.slug})


class ShopViewFilterTests(TestCase):
    def setUp(self):
        self.men_product = make_product(slug="men-jacket", sku="VLR-MEN", gender=Product.Gender.MEN)
        self.women_product = make_product(slug="women-dress", sku="VLR-WOMEN", gender=Product.Gender.WOMEN)
        self.unisex_product = make_product(slug="unisex-cap", sku="VLR-UNISEX", gender=Product.Gender.UNISEX)

    def test_gender_filter_includes_unisex(self):
        response = self.client.get(reverse("catalog:shop"), {"gender": "men"})
        slugs = {p.slug for p in response.context["products"]}
        self.assertEqual(slugs, {self.men_product.slug, self.unisex_product.slug})

    def test_no_filter_returns_everything(self):
        response = self.client.get(reverse("catalog:shop"))
        self.assertEqual(len(response.context["products"]), 3)


class BrandDetailPaginationTests(TestCase):
    def test_products_are_paginated(self):
        brand = Brand.objects.create(name="Paginated Brand", slug="paginated-brand")
        category = Category.objects.create(name="Взуття", slug="shoes")
        for i in range(30):
            make_product(brand=brand, category=category, slug=f"shoe-{i}", sku=f"VLR-SHOE-{i}")

        response = self.client.get(reverse("catalog:brand_detail", kwargs={"brand_slug": brand.slug}))

        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["products"]), 24)


class WishlistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="shopper", email="shopper@example.com", password="pass12345")
        self.product = make_product()

    def test_toggle_requires_login(self):
        url = reverse("catalog:toggle_wishlist", args=[self.product.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_toggle_adds_then_removes(self):
        self.client.force_login(self.user)
        url = reverse("catalog:toggle_wishlist", args=[self.product.pk])

        self.client.post(url)
        self.assertTrue(WishlistItem.objects.filter(user=self.user, product=self.product).exists())

        self.client.post(url)
        self.assertFalse(WishlistItem.objects.filter(user=self.user, product=self.product).exists())

    def test_wishlist_page_lists_only_own_items(self):
        other = User.objects.create_user(username="other", email="other@example.com", password="pass12345")
        WishlistItem.objects.create(user=other, product=self.product)
        self.client.force_login(self.user)

        response = self.client.get(reverse("catalog:wishlist"))

        self.assertEqual(list(response.context["items"]), [])


class ReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reviewer", email="reviewer@example.com", password="pass12345")
        self.product = make_product()

    def test_logged_in_user_can_post_review(self):
        self.client.force_login(self.user)
        url = self.product.get_absolute_url()

        response = self.client.post(url, {"rating": 5, "body": "Чудова якість"})

        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(self.product.average_rating, 5.0)

    def test_second_submission_updates_existing_review_instead_of_duplicating(self):
        self.client.force_login(self.user)
        url = self.product.get_absolute_url()

        self.client.post(url, {"rating": 3, "body": "Непогано"})
        self.client.post(url, {"rating": 4, "body": "Переглянув думку"})

        self.assertEqual(Review.objects.filter(product=self.product, user=self.user).count(), 1)
        self.assertEqual(Review.objects.get(product=self.product, user=self.user).rating, 4)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post(self.product.get_absolute_url(), {"rating": 5, "body": ""})
        self.assertRedirects(response, reverse("accounts:login"))
