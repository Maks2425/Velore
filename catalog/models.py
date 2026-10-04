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


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"Image #{self.position} for {self.product.name}"
