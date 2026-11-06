"""
URLs of the NAFUV website.

English pages have no prefix (/about/), French pages start with /fr/,
Swahili pages with /sw/.
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.static import serve
from django.views.generic import TemplateView

from mainApp.sitemaps import SITEMAPS
from mainApp.views import donation_webhook

admin.site.site_header = "NAFUV administration"
admin.site.site_title = "NAFUV"
admin.site.index_title = "Museum content"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Management application of the museum (team accounts only)
    path("dashboard/", include("tableau.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    # Stripe calls this address directly: no language prefix
    path("donate/webhook/", donation_webhook, name="donation_webhook"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

urlpatterns += i18n_patterns(
    path("", include("mainApp.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    # Hosting where nothing else serves /media/ (some cPanel/Passenger setups):
    # Django serves the uploaded pictures itself.
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

handler404 = "mainApp.views.page_not_found"
handler500 = "mainApp.views.server_error"
