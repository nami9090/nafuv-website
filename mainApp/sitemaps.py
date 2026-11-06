from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Galleries, servicesModel


class PagesSitemap(Sitemap):
    priority = 0.8
    i18n = True
    alternates = True

    def items(self):
        return ["index", "about", "services", "gallery", "agents", "contact", "donate"]

    def location(self, item):
        return reverse(item)


class HeritageSitemap(Sitemap):
    priority = 0.7
    i18n = True
    alternates = True

    def items(self):
        return servicesModel.objects.exclude(slug="")


class GalleriesSitemap(Sitemap):
    priority = 0.6
    i18n = True
    alternates = True

    def items(self):
        return Galleries.objects.all()


SITEMAPS = {"pages": PagesSitemap, "heritage": HeritageSitemap, "galleries": GalleriesSitemap}
