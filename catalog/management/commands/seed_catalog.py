from decimal import Decimal

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Brand, Category, Product, ProductImage

BRANDS = [
    {
        "name": "Bape",
        "slug": "bape",
        "country": "Японія",
        "founded_year": 1993,
        "logo": "media/brands/bape.png",
        "description": "A Bathing Ape (BAPE) — японський стріт-бренд, відомий камуфляжними принтами та культовими кросівками.",
    },
    {
        "name": "Maison Margiela",
        "slug": "maison-margiela",
        "country": "Франція",
        "founded_year": 1988,
        "logo": "media/brands/maison-margiela.svg",
        "description": "Maison Margiela — дім високої моди, заснований Мартіном Марджела, відомий деконструктивізмом та взуттям Tabi.",
    },
    {
        "name": "Balenciaga",
        "slug": "balenciaga",
        "country": "Іспанія / Франція",
        "founded_year": 1917,
        "logo": "media/brands/balenciaga.svg",
        "description": "Balenciaga — модний дім, заснований Крістобалем Баленсіагою, відомий авангардним крої та сучасним стрітвіром.",
    },
    {
        "name": "Dior",
        "slug": "dior",
        "country": "Франція",
        "founded_year": 1946,
        "logo": "media/brands/dior.svg",
        "description": "Christian Dior — легендарний дім високої моди, парфумерії та аксесуарів класу люкс.",
    },
]

CATEGORIES = [
    ("Одяг", "clothing"),
    ("Взуття", "shoes"),
    ("Парфуми", "perfume"),
]

PRODUCTS = [
    {"brand": "bape", "category": "clothing", "name": "Bape Camo Hoodie", "price": "8900.00", "stock": 12, "image": "media/products/bape-1.jpg"},
    {"brand": "bape", "category": "shoes", "name": "Bape Sta Sneakers", "price": "11500.00", "stock": 7, "image": "media/products/bape-1.jpg"},
    {"brand": "maison-margiela", "category": "shoes", "name": "Margiela Tabi Boots", "price": "24900.00", "stock": 5, "image": "media/products/margiela-1.jpg"},
    {"brand": "maison-margiela", "category": "clothing", "name": "Margiela Deconstructed Coat", "price": "32900.00", "stock": 3, "image": "media/products/margiela-1.jpg"},
    {"brand": "balenciaga", "category": "shoes", "name": "Balenciaga Triple S Sneakers", "price": "28900.00", "stock": 6, "image": "media/products/balenciaga-1.jpg"},
    {"brand": "balenciaga", "category": "clothing", "name": "Balenciaga Oversized Jacket", "price": "35900.00", "stock": 4, "image": "media/products/balenciaga-1.jpg"},
    {"brand": "dior", "category": "perfume", "name": "Dior Sauvage Eau de Parfum", "price": "4900.00", "stock": 20, "image": "media/products/dior-1.jpg"},
    {"brand": "dior", "category": "clothing", "name": "Dior Bar Jacket", "price": "68900.00", "stock": 2, "image": "media/products/dior-1.jpg"},
]


class Command(BaseCommand):
    help = "Seed demo brands, categories and products for the Velore catalog."

    @transaction.atomic
    def handle(self, *args, **options):
        brand_by_slug = {}
        for data in BRANDS:
            brand, _ = Brand.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "country": data["country"],
                    "founded_year": data["founded_year"],
                    "description": data["description"],
                    "is_active": True,
                },
            )
            if not brand.logo:
                with open(data["logo"], "rb") as f:
                    brand.logo.save(data["logo"].split("/")[-1], File(f), save=True)
            brand_by_slug[data["slug"]] = brand

        category_by_slug = {}
        for name, slug in CATEGORIES:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            category_by_slug[slug] = category

        for data in PRODUCTS:
            slug = data["name"].lower().replace(" ", "-")
            sku = f"VLR-{slug[:20].upper()}"
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "brand": brand_by_slug[data["brand"]],
                    "category": category_by_slug[data["category"]],
                    "name": data["name"],
                    "price": Decimal(data["price"]),
                    "stock": data["stock"],
                    "sku": sku,
                    "is_active": True,
                    "is_featured": True,
                },
            )
            if not product.images.exists():
                with open(data["image"], "rb") as f:
                    image = ProductImage(product=product, alt_text=data["name"])
                    image.image.save(data["image"].split("/")[-1], File(f), save=True)

        self.stdout.write(self.style.SUCCESS("Catalog seeded: brands, categories and products are ready."))
