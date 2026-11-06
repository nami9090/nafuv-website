"""Figures and shortcuts of the administration dashboard (templates/admin/index.html)."""
from django import template
from django.conf import settings
from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils import timezone

from ..models import (
    ContactMessage, Donation, Galleries, GalleryImages, agentsModel, homeSilde, serviceDetail, servicesModel,
    whoWeareHome,
)

register = template.Library()

# (model, field checked, label) for the "translations to do" block
A_TRADUIRE = [
    (homeSilde, "title", "Home slides"),
    (whoWeareHome, "first_paragraph", "“Who we are” text"),
    (servicesModel, "details", "Heritage pages"),
    (Galleries, "description", "Galleries"),
    (GalleryImages, "title", "Objects / photos"),
    (agentsModel, "role", "Team"),
]


def _url(modele, action="changelist"):
    return reverse(f"admin:{modele._meta.app_label}_{modele._meta.model_name}_{action}")


@register.simple_tag
def tableau_de_bord():
    maintenant = timezone.now()
    payes = Donation.objects.filter(statut=Donation.PAYE)
    totaux = payes.aggregate(
        total=Sum("montant"),
        annee=Sum("montant", filter=Q(paye_le__year=maintenant.year)),
        mois=Sum("montant", filter=Q(paye_le__year=maintenant.year, paye_le__month=maintenant.month)),
        nombre=Count("id"),
    )

    contenus = [
        ("Home slides", homeSilde.objects.count(), homeSilde),
        ("Heritage pages", servicesModel.objects.count(), servicesModel),
        ("Kingdoms", servicesModel.objects.filter(iskingdom=True).count(), servicesModel),
        ("Rulers", serviceDetail.objects.count(), serviceDetail),
        ("Galleries", Galleries.objects.count(), Galleries),
        ("Objects & photos", GalleryImages.objects.count(), GalleryImages),
        ("Team members", agentsModel.objects.count(), agentsModel),
    ]

    traductions = []
    for modele, champ, libelle in A_TRADUIRE:
        base = modele.objects.exclude(**{champ: ""})
        sans_fr = base.filter(**{f"{champ}_fr": ""}).count()
        sans_sw = base.filter(**{f"{champ}_sw": ""}).count()
        if sans_fr or sans_sw:
            url = _url(modele)
            traductions.append({
                "libelle": libelle, "sans_fr": sans_fr, "sans_sw": sans_sw,
                "url_fr": f"{url}?traduction=fr", "url_sw": f"{url}?traduction=sw",
            })

    console = "console" in settings.EMAIL_BACKEND or "locmem" in settings.EMAIL_BACKEND
    etat = [
        ("Online donations (Stripe)", bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET),
         "Active" if settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET else "Not configured: add the Stripe keys to .env"),
        ("E-mails", not console, "Sent for real" if not console else "Not sent (console mode): configure SMTP in .env"),
        ("Production mode", not settings.DEBUG, "DEBUG off" if not settings.DEBUG else "DEBUG is on: turn it off on the live site"),
    ]
    if settings.STRIPE_SECRET_KEY.startswith("sk_test_"):
        etat[0] = ("Online donations (Stripe)", True, "Test mode: no real money is collected")

    return {
        "dons": {
            "total": totaux["total"] or 0, "annee": totaux["annee"] or 0, "mois": totaux["mois"] or 0,
            "nombre": totaux["nombre"], "annee_courante": maintenant.year,
            "attente": Donation.objects.filter(statut=Donation.EN_ATTENTE).count(),
            "derniers": list(payes.order_by("-paye_le")[:6]),
            "url": _url(Donation),
        },
        "messages": {
            "non_traites": ContactMessage.objects.filter(traite=False).count(),
            "derniers": list(ContactMessage.objects.all()[:5]),
            "url": _url(ContactMessage),
        },
        "contenus": [{"libelle": l, "nombre": n, "url": _url(m)} for l, n, m in contenus],
        "traductions": traductions,
        "etat": etat,
        "actions": [
            ("Add a home slide", _url(homeSilde, "add")),
            ("Add a heritage page / kingdom", _url(servicesModel, "add")),
            ("Add a gallery", _url(Galleries, "add")),
            ("Add a team member", _url(agentsModel, "add")),
            ("Edit the site settings", reverse("admin:mainApp_sitesettings_changelist")),
        ],
    }
