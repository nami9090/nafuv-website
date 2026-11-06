from django.conf import settings

from .models import SiteSettings


def site(request):
    return {
        "site": SiteSettings.charger(),
        "dons_actifs": bool(settings.STRIPE_SECRET_KEY),
        "SITE_URL": settings.SITE_URL,
    }
