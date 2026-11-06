import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import stripe_api
from .forms import ContactForm, DonationForm
from .models import (
    Donation, Galleries, GalleryImages, SiteSettings, agentsModel, homeSilde, serviceDetail, servicesModel,
    whoWeareHome, whoWeareHomeimage,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# Museum pages
# ===========================================================================
def index(request):
    return render(request, "index.html", {
        "slideHome": homeSilde.objects.all(),
        "whoWeare": whoWeareHome.objects.first(),
        "singleItem": whoWeareHomeimage.objects.order_by("?").first(),
        "homeService": servicesModel.objects.all()[:6],
        "galleries": Galleries.objects.all()[:3],
        "teams": agentsModel.objects.all()[:4],
        "nb_royaumes": servicesModel.objects.filter(iskingdom=True).count(),
        "nb_objets": GalleryImages.objects.count(),
        "nb_souverains": serviceDetail.objects.count(),
    })


def about(request):
    return render(request, "about.html", {
        "about": whoWeareHome.objects.prefetch_related("images").first(),
        "teams": agentsModel.objects.all(),
    })


def services(request):
    pages = servicesModel.objects.all()
    return render(request, "services.html", {
        "royaumes": [p for p in pages if p.iskingdom],
        "programmes": [p for p in pages if not p.iskingdom],
    })


def service_details(request, slug):
    page = servicesModel.objects.filter(slug=slug).first()
    if page is None:
        return page_not_found(request, None)
    return render(request, "service-details.html", {
        "singleService": page,
        "og_image": page.image_pic,
        "serviceD": page.detail.all() if page.iskingdom else [],
        "services": servicesModel.objects.exclude(pk=page.pk),
    })


def gallery(request):
    return render(request, "gallery.html", {"galleries": Galleries.objects.prefetch_related("images")})


def gallery_single(request, id):
    galerie = get_object_or_404(Galleries, pk=id)
    return render(request, "gallery-single.html", {
        "singleGallery": galerie,
        "og_image": galerie.image,
        "gallery": galerie.images.all(),
        "autres": Galleries.objects.exclude(pk=galerie.pk)[:3],
    })


def agents(request):
    return render(request, "agents.html", {"teams": agentsModel.objects.all()})


# ===========================================================================
# Contact
# ===========================================================================
def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not form.est_robot():
            msg = form.save()
            try:
                send_mail(
                    f"[NAFUV website] {msg.sujet}",
                    f"From: {msg.nom} <{msg.email}>\n\n{msg.message}",
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
            except Exception:
                # The message is saved in the admin even if the e-mail fails
                logger.exception("Contact e-mail not sent (message %s saved in the admin)", msg.pk)
        messages.success(request, _("Thank you! Your message has been sent. We will reply as soon as possible."))
        return redirect("contact")
    return render(request, "contact.html", {"form": form})


# ===========================================================================
# Donations (Stripe Checkout)
# ===========================================================================
def donate(request):
    site = SiteSettings.charger()
    donnees = None
    if request.method == "POST":
        donnees = request.POST.copy()
        # Without JavaScript, the chosen preset amount fills the amount field
        if not donnees.get("montant") and donnees.get("montant_choisi"):
            donnees["montant"] = donnees["montant_choisi"]
    form = DonationForm(donnees, initial={"montant": "50"})

    if request.method == "POST" and form.is_valid():
        if not settings.STRIPE_SECRET_KEY:
            messages.error(request, _("Online donations are not available yet. Please contact us."))
            return redirect("donate")
        don = Donation.objects.create(
            nom=form.cleaned_data["nom"],
            email=form.cleaned_data["email"],
            montant=form.cleaned_data["montant"],
            devise=settings.DONATION_CURRENCY,
            message=form.cleaned_data["message"],
            anonyme=form.cleaned_data["anonyme"],
            langue=(get_language() or "en")[:2],
        )
        base = settings.SITE_URL
        try:
            session = stripe_api.creer_session_don(
                don,
                url_succes=base + reverse("donate_thanks") + "?session_id={CHECKOUT_SESSION_ID}",
                url_annulation=base + reverse("donate") + "?cancelled=1",
                libelle=_("Donation to %(name)s") % {"name": site.nom},
            )
        except stripe_api.StripeErreur as exc:
            logger.error("Stripe session not created for donation %s: %s", don.pk, exc)
            messages.error(request, _("The payment service is unavailable right now. Please try again in a few minutes."))
            return redirect("donate")
        don.stripe_session = session.get("id", "")
        don.save(update_fields=["stripe_session"])
        return redirect(session["url"])

    if request.GET.get("cancelled"):
        messages.info(request, _("Your donation was cancelled. No payment has been taken."))

    return render(request, "donate.html", {
        "form": form,
        "montants": settings.DONATION_AMOUNTS,
        "derniers_dons": Donation.objects.filter(statut=Donation.PAYE, anonyme=False)[:6],
    })


def donate_thanks(request):
    don = None
    session_id = request.GET.get("session_id", "")
    if session_id:
        don = Donation.objects.filter(stripe_session=session_id).first()
        # The webhook usually arrives first; if not, ask Stripe directly
        if don and don.statut != Donation.PAYE and settings.STRIPE_SECRET_KEY:
            try:
                session = stripe_api.lire_session(session_id)
                if session.get("payment_status") == "paid":
                    confirmer_don(don, session.get("payment_intent") or "")
            except stripe_api.StripeErreur as exc:
                logger.warning("Stripe session %s not read: %s", session_id, exc)
    return render(request, "donate_thanks.html", {"don": don})


@csrf_exempt
@require_POST
def donation_webhook(request):
    try:
        evenement = stripe_api.verifier_webhook(request.body, request.headers.get("Stripe-Signature", ""))
    except stripe_api.StripeErreur as exc:
        logger.warning("Stripe webhook refused: %s", exc)
        return HttpResponseBadRequest("invalid signature")

    type_evt = evenement.get("type", "")
    session = evenement.get("data", {}).get("object", {})
    don = Donation.objects.filter(stripe_session=session.get("id", "")).first()

    if don is not None:
        if type_evt in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
            if session.get("payment_status") == "paid":
                confirmer_don(don, session.get("payment_intent") or "")
        elif type_evt in ("checkout.session.expired", "checkout.session.async_payment_failed"):
            Donation.objects.filter(pk=don.pk, statut=Donation.EN_ATTENTE).update(statut=Donation.ABANDONNE)
    return HttpResponse("ok")


def confirmer_don(don, paiement_id=""):
    """Marks the donation as paid (once only) and sends the thank-you e-mails."""
    with transaction.atomic():
        mis_a_jour = Donation.objects.filter(pk=don.pk).exclude(statut=Donation.PAYE).update(
            statut=Donation.PAYE, paye_le=timezone.now(), stripe_paiement=paiement_id,
        )
    if not mis_a_jour:
        return False
    don.refresh_from_db()
    site = SiteSettings.charger()
    montant = f"${don.montant}" if don.devise == "usd" else f"{don.montant} {don.devise.upper()}"
    try:
        send_mail(
            f"Thank you for your donation to {site.nom}",
            f"Dear {don.nom},\n\n"
            f"We have received your donation of {montant}. Thank you for helping us preserve and share the "
            f"heritage of the Fuliiru and Vira peoples.\n\n"
            f"Stripe sends your payment receipt separately.\n\n"
            f"With gratitude,\nThe NAFUV team\n{settings.SITE_URL}",
            settings.DEFAULT_FROM_EMAIL, [don.email], fail_silently=False,
        )
        send_mail(
            f"[NAFUV website] New donation: {montant}",
            f"{don.nom} <{don.email}> donated {montant}.\n"
            f"Anonymous: {'yes' if don.anonyme else 'no'}\nMessage: {don.message or '-'}",
            settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_EMAIL], fail_silently=False,
        )
    except Exception:
        logger.exception("Donation e-mails not sent (donation %s)", don.pk)
    return True


# Old address of the donation page
def dialog(request):
    return redirect("donate", permanent=True)


# ===========================================================================
# Error pages
# ===========================================================================
def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)
