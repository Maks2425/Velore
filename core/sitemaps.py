from django.contrib.sitemaps import Sitemap

from catalog.models import Brand, Product


class BrandSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Brand.objects.filter(is_active=True)

    def lastmod(self, obj):
        return None


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return Product.objects.available().with_related()

    def lastmod(self, obj):
        return obj.updated_at
