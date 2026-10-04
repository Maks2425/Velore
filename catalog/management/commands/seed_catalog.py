from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Brand, Category, Product, ProductImage

BRANDS = [
    {
        "name": "Bape",
        "slug": "bape",
        "country": "Японія",
        "founded_year": 1993,
        "logo": "",
        "description": "A Bathing Ape (BAPE) — японський стріт-бренд, відомий камуфляжними принтами та культовими кросівками.",
    },
    {
        "name": "Maison Margiela",
        "slug": "maison-margiela",
        "country": "Франція",
        "founded_year": 1988,
        "logo": "brands/maison-margiela_UpHT3tZ.svg",
        "description": "Maison Margiela — дім високої моди, заснований Мартіном Марджела, відомий деконструктивізмом та взуттям Tabi.",
    },
    {
        "name": "Balenciaga",
        "slug": "balenciaga",
        "country": "Іспанія / Франція",
        "founded_year": 1917,
        "logo": "brands/balenciaga_fCxUGlf.svg",
        "description": "Balenciaga — модний дім, заснований Крістобалем Баленсіагою, відомий авангардним кроєм та сучасним стрітвіром.",
    },
    {
        "name": "Dior",
        "slug": "dior",
        "country": "Франція",
        "founded_year": 1946,
        "logo": "brands/dior_cJBZKli.svg",
        "description": "Christian Dior — легендарний дім високої моди, парфумерії та аксесуарів класу люкс.",
    },
]

CATEGORIES = [
    ("Одяг", "clothing"),
    ("Взуття", "shoes"),
    ("Парфуми", "perfume"),
]

# `image` is a file under media/products/ (Wikimedia Commons photos) or None for
# products that still need a photo — those render a branded placeholder until
# a photo is uploaded in the Django admin.
PRODUCTS = [
    # Bape
    {"slug": "bape-camo-hoodie", "brand": "bape", "category": "clothing", "gender": "men", "name": "Bape Camo Hoodie", "price": "8900.00", "stock": 12, "image": "bape-camo-hoodie.jpg"},
    {"slug": "bape-sta-sneakers", "brand": "bape", "category": "shoes", "gender": "unisex", "name": "Bape Sta Sneakers", "price": "11500.00", "stock": 7, "image": "bape-sta-sneakers.jpg"},
    {"slug": "bape-shark-tee", "brand": "bape", "category": "clothing", "gender": "unisex", "name": "Bape Shark Tee", "price": "3900.00", "stock": 15, "image": "bape-shark-tee.jpg"},
    {"slug": "bape-shark-jacket", "brand": "bape", "category": "clothing", "gender": "men", "name": "Bape Shark Jacket", "price": "18500.00", "stock": 4, "image": "bape-shark-jacket.jpg"},
    {"slug": "bape-camo-track-pants", "brand": "bape", "category": "clothing", "gender": "men", "name": "Bape Camo Track Pants", "price": "7200.00", "stock": 9, "image": "bape-camo-track-pants.jpg"},
    {"slug": "bape-shark-hoodie-women", "brand": "bape", "category": "clothing", "gender": "women", "name": "Bape Shark Hoodie", "price": "9400.00", "stock": 6, "image": "bape-shark-hoodie-women.jpg"},
    {"slug": "bape-color-camo-sneakers", "brand": "bape", "category": "shoes", "gender": "women", "name": "Bape Color Camo Sneakers", "price": "12900.00", "stock": 5, "image": "bape-color-camo-sneakers.jpg"},
    {"slug": "bape-ape-head-cap", "brand": "bape", "category": "clothing", "gender": "unisex", "name": "Bape Ape Head Cap", "price": "2400.00", "stock": 20, "image": "bape-ape-head-cap.jpg"},
    # Maison Margiela
    {"slug": "margiela-tabi-boots", "brand": "maison-margiela", "category": "shoes", "gender": "unisex", "name": "Margiela Tabi Boots", "price": "24900.00", "stock": 5, "image": "margiela-tabi-boots.jpg"},
    {"slug": "margiela-semi-couture-top", "brand": "maison-margiela", "category": "clothing", "gender": "women", "name": "Margiela Semi-Couture Top", "price": "9900.00", "stock": 6, "image": "margiela-semi-couture-top.jpg"},
    {"slug": "margiela-trompe-loeil-bodice", "brand": "maison-margiela", "category": "clothing", "gender": "women", "name": "Margiela Trompe-l'Oeil Bodice", "price": "21900.00", "stock": 3, "image": "margiela-trompe-loeil-bodice.jpg"},
    {"slug": "margiela-hair-scarf", "brand": "maison-margiela", "category": "clothing", "gender": "women", "name": "Margiela Hair Scarf", "price": "5400.00", "stock": 10, "image": "margiela-hair-scarf.jpg"},
    {"slug": "margiela-tabi-slip-ons", "brand": "maison-margiela", "category": "shoes", "gender": "women", "name": "Margiela Tabi Slip-Ons", "price": "19800.00", "stock": 4, "image": "margiela-tabi-slip-ons.jpg"},
    {"slug": "margiela-oversized-wool-coat", "brand": "maison-margiela", "category": "clothing", "gender": "men", "name": "Margiela Oversized Wool Coat", "price": "38900.00", "stock": 2, "image": "margiela-oversized-wool-coat.jpg"},
    {"slug": "margiela-replica-edt", "brand": "maison-margiela", "category": "perfume", "gender": "unisex", "name": "Margiela Replica Eau de Toilette", "price": "4600.00", "stock": 18, "image": "margiela-replica-edt.jpg"},
    {"slug": "margiela-replica-sneakers", "brand": "maison-margiela", "category": "shoes", "gender": "unisex", "name": "Margiela Replica Sneakers", "price": "21500.00", "stock": 6, "image": "margiela-replica-sneakers.jpg"},
    {"slug": "margiela-numbers-belt", "brand": "maison-margiela", "category": "clothing", "gender": "unisex", "name": "Margiela Numbers Belt", "price": "6900.00", "stock": 6, "image": "margiela-numbers-belt.jpg"},
    # Balenciaga
    {"slug": "balenciaga-triple-s-sneakers", "brand": "balenciaga", "category": "shoes", "gender": "unisex", "name": "Balenciaga Triple S Sneakers", "price": "28900.00", "stock": 6, "image": "balenciaga-triple-s-sneakers.jpg"},
    {"slug": "balenciaga-high-sneakers", "brand": "balenciaga", "category": "shoes", "gender": "men", "name": "Balenciaga High-Top Sneakers", "price": "31900.00", "stock": 4, "image": "balenciaga-high-sneakers.jpg"},
    {"slug": "balenciaga-arena-sneakers", "brand": "balenciaga", "category": "shoes", "gender": "women", "name": "Balenciaga Arena Sneakers", "price": "26500.00", "stock": 5, "image": "balenciaga-arena-sneakers.jpg"},
    {"slug": "balenciaga-couture-dress", "brand": "balenciaga", "category": "clothing", "gender": "women", "name": "Balenciaga Couture Dress", "price": "42900.00", "stock": 2, "image": "balenciaga-couture-dress.jpg"},
    {"slug": "balenciaga-logo-hoodie", "brand": "balenciaga", "category": "clothing", "gender": "unisex", "name": "Balenciaga Logo Hoodie", "price": "16900.00", "stock": 8, "image": "balenciaga-logo-hoodie.jpg"},
    {"slug": "balenciaga-speed-trainers", "brand": "balenciaga", "category": "shoes", "gender": "women", "name": "Balenciaga Speed Trainers", "price": "21900.00", "stock": 7, "image": "balenciaga-speed-trainers.jpg"},
    {"slug": "balenciaga-political-tee", "brand": "balenciaga", "category": "clothing", "gender": "men", "name": "Balenciaga Campaign Tee", "price": "8900.00", "stock": 11, "image": "balenciaga-political-tee.jpg"},
    # Dior
    {"slug": "dior-sauvage-eau-de-parfum", "brand": "dior", "category": "perfume", "gender": "men", "name": "Dior Sauvage Eau de Parfum", "price": "4900.00", "stock": 20, "image": "dior-sauvage-eau-de-parfum.jpg"},
    {"slug": "dior-parfum-01", "brand": "dior", "category": "perfume", "gender": "women", "name": "Dior Parfum — Edition 01", "price": "5900.00", "stock": 9, "image": "dior-parfum-01.jpg"},
    {"slug": "dior-parfum-02", "brand": "dior", "category": "perfume", "gender": "unisex", "name": "Dior Parfum — Edition 02", "price": "6400.00", "stock": 8, "image": "dior-parfum-02.jpg"},
    {"slug": "dior-parfum-03", "brand": "dior", "category": "perfume", "gender": "women", "name": "Dior Parfum — Edition 03", "price": "7200.00", "stock": 7, "image": "dior-parfum-03.jpg"},
    {"slug": "dior-miss-dior-edp", "brand": "dior", "category": "perfume", "gender": "women", "name": "Miss Dior Eau de Parfum", "price": "5600.00", "stock": 14, "image": "dior-miss-dior-edp.jpg"},
    {"slug": "dior-homme-intense", "brand": "dior", "category": "perfume", "gender": "men", "name": "Dior Homme Intense", "price": "5200.00", "stock": 10, "image": "dior-homme-intense.jpg"},
    {"slug": "dior-b27-sneakers", "brand": "dior", "category": "shoes", "gender": "men", "name": "Dior B27 Sneakers", "price": "34900.00", "stock": 3, "image": "dior-b27-sneakers.jpg"},
    {"slug": "dior-b30-sneakers", "brand": "dior", "category": "shoes", "gender": "men", "name": "Dior B30 Sneakers", "price": "36900.00", "stock": 4, "image": "dior-b30-sneakers.jpg"},
    {"slug": "dior-oblique-blouse", "brand": "dior", "category": "clothing", "gender": "women", "name": "Dior Oblique Silk Blouse", "price": "27900.00", "stock": 4, "image": "dior-oblique-blouse.jpg"},
]


class Command(BaseCommand):
    help = (
        "Idempotently seed brands, categories and products. Products missing from "
        "the list are deactivated, not deleted, so existing orders stay valid."
    )

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
                    "logo": data["logo"],
                    "is_active": True,
                },
            )
            brand_by_slug[data["slug"]] = brand

        category_by_slug = {}
        for name, slug in CATEGORIES:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            category_by_slug[slug] = category

        active_slugs = []
        for data in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "brand": brand_by_slug[data["brand"]],
                    "category": category_by_slug[data["category"]],
                    "gender": data["gender"],
                    "name": data["name"],
                    "price": Decimal(data["price"]),
                    "stock": data["stock"],
                    "sku": f"VLR-{data['slug'][:24].upper()}",
                    "is_active": True,
                    "is_featured": True,
                },
            )
            if data["image"]:
                ProductImage.objects.update_or_create(
                    product=product,
                    position=0,
                    defaults={"image": f"products/{data['image']}", "alt_text": data["name"]},
                )
            else:
                product.images.all().delete()
            active_slugs.append(data["slug"])

        Product.objects.exclude(slug__in=active_slugs).update(is_active=False, is_featured=False)

        self.stdout.write(self.style.SUCCESS(f"Catalog seeded: {len(active_slugs)} active products."))
