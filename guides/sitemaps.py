from django.contrib.sitemaps import Sitemap

from .models import Category, Guide


class GuideSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Guide.objects.exclude(status="archived")

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Category.objects.all()
