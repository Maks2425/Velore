from django.conf import settings
from django.db import models
from django.urls import reverse


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="brands/", blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    country = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog:brand_detail", kwargs={"brand_slug": self.slug})

    @property
    def preview_image(self):
        """First product photo, used for the hover preview on the brand card."""
        product = self.products.filter(is_active=True).prefetch_related("images").first()
        image = product.main_image if product else None
        return image.image.url if image else None


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.filter(is_active=True, stock__gt=0)

    def with_related(self):
        return self.select_related("brand", "category").prefetch_related("images")


class Product(models.Model):
    class Gender(models.TextChoices):
        WOMEN = "women", "Жінкам"
        MEN = "men", "Чоловікам"
        UNISEX = "unisex", "Унісекс"

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.UNISEX)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.brand.name} — {self.name}"

    def get_absolute_url(self) -> str:
        return reverse(
            "catalog:product_detail",
            kwargs={"brand_slug": self.brand.slug, "product_slug": self.slug},
        )

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def main_image(self):
        return self.images.first()

    @property
    def average_rating(self) -> float:
        ratings = [review.rating for review in self.reviews.all()]
        return round(sum(ratings) / len(ratings), 1) if ratings else 0.0

    @property
    def review_count(self) -> int:
        return self.reviews.count()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"Image #{self.position} for {self.product.name}"


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    body = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["product", "user"], name="one_review_per_user_per_product"),
        ]

    def __str__(self) -> str:
        return f"{self.user} rated {self.product} {self.rating}/5"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="one_wishlist_entry_per_user_per_product"),
        ]

    def __str__(self) -> str:
        return f"{self.user} ♥ {self.product}"
