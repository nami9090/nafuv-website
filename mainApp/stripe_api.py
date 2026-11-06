"""
Minimal Stripe client (Checkout + webhooks), with no extra library.

Stripe Checkout hosts the payment page: card numbers never touch the NAFUV
server. Docs: https://docs.stripe.com/payments/checkout
"""
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

API = "https://api.stripe.com/v1"
TOLERANCE_SECONDES = 300


class StripeErreur(Exception):
    pass


def _encoder(donnees, prefixe=""):
    """Stripe expects nested form fields: line_items[0][price_data][currency]=usd."""
    paires = []
    for cle, valeur in donnees.items():
        nom = f"{prefixe}[{cle}]" if prefixe else str(cle)
        if isinstance(valeur, dict):
            paires.extend(_encoder(valeur, nom))
        elif isinstance(valeur, (list, tuple)):
            for i, element in enumerate(valeur):
                if isinstance(element, dict):
                    paires.extend(_encoder(element, f"{nom}[{i}]"))
                else:
                    paires.append((f"{nom}[{i}]", str(element)))
        elif valeur is not None:
            paires.append((nom, str(valeur).lower() if isinstance(valeur, bool) else str(valeur)))
    return paires


def _appel(methode, chemin, donnees=None):
    corps = urllib.parse.urlencode(_encoder(donnees)).encode() if donnees else None
    requete = urllib.request.Request(f"{API}{chemin}", data=corps, method=methode)
    requete.add_header("Authorization", f"Bearer {settings.STRIPE_SECRET_KEY}")
    requete.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(requete, timeout=20) as reponse:
            return json.loads(reponse.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode()).get("error", {}).get("message", "")
        except Exception:
            detail = ""
        raise StripeErreur(detail or f"HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise StripeErreur(str(exc.reason)) from exc


def creer_session_don(don, url_succes, url_annulation, libelle):
    """Creates a Checkout session for a one-time donation and returns it (dict with 'id' and 'url')."""
    return _appel("POST", "/checkout/sessions", {
        "mode": "payment",
        "submit_type": "donate",
        "customer_email": don.email,
        "client_reference_id": str(don.pk),
        "success_url": url_succes,
        "cancel_url": url_annulation,
        "locale": don.langue if don.langue in ("en", "fr") else "auto",
        "metadata": {"donation_id": don.pk},
        "payment_intent_data": {"description": libelle, "metadata": {"donation_id": don.pk}},
        "line_items": [{
            "quantity": 1,
            "price_data": {
                "currency": don.devise,
                "unit_amount": don.montant_cents,
                "product_data": {"name": libelle},
            },
        }],
    })


def lire_session(session_id):
    return _appel("GET", f"/checkout/sessions/{urllib.parse.quote(session_id)}")


def verifier_webhook(corps, entete_signature, secret=None, maintenant=None):
    """
    Checks the Stripe-Signature header (HMAC SHA-256) and returns the event.
    Raises StripeErreur if the message does not come from Stripe.
    """
    secret = secret or settings.STRIPE_WEBHOOK_SECRET
    if not secret or not entete_signature:
        raise StripeErreur("Missing signature")
    elements = dict(
        morceau.split("=", 1) for morceau in entete_signature.split(",") if "=" in morceau
    )
    horodatage = elements.get("t", "")
    signatures = [v for k, v in (m.split("=", 1) for m in entete_signature.split(",") if "=" in m) if k == "v1"]
    if not horodatage or not signatures:
        raise StripeErreur("Malformed signature")
    attendu = hmac.new(
        secret.encode(), f"{horodatage}.".encode() + corps, hashlib.sha256
    ).hexdigest()
    if not any(hmac.compare_digest(attendu, s) for s in signatures):
        raise StripeErreur("Invalid signature")
    if abs((maintenant or time.time()) - int(horodatage)) > TOLERANCE_SECONDES:
        raise StripeErreur("Signature too old")
    return json.loads(corps.decode())


def signer_pour_test(corps, secret, horodatage=None):
    """Builds a valid Stripe-Signature header (used by the tests)."""
    horodatage = int(horodatage or time.time())
    signature = hmac.new(secret.encode(), f"{horodatage}.".encode() + corps, hashlib.sha256).hexdigest()
    return f"t={horodatage},v1={signature}"
