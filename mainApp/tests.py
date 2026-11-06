"""
NAFUV tests:  python manage.py test mainApp
"""
import json
from datetime import date
from decimal import Decimal
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from . import stripe_api
from .models import (
    ContactMessage, Donation, Galleries, GalleryImages, SiteSettings, agentsModel, homeSilde, serviceDetail,
    servicesModel, whoWeareHome,
)
from .templatetags.nafuv_tags import tr

STOCKAGE_SIMPLE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
SECRET_WEBHOOK = "whsec_test"


@override_settings(STORAGES=STOCKAGE_SIMPLE, SECURE_SSL_REDIRECT=False, SITE_URL="https://nafuv.test")
class PagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        homeSilde.objects.create(image_pic="images/slide.jpg", span="Welcome", title="Our heritage", details="Uvira",
                                 title_fr="Notre patrimoine")
        cls.who = whoWeareHome.objects.create(title="Who we are", first_paragraph="First.", second_paragraph="Second.")
        cls.royaume = servicesModel.objects.create(
            title="Kingdom of Bufuliiru", details="History.", iskingdom=True, image_pic="images/k.jpg",
            title_sw="Ufalme wa Bufuliiru",
        )
        serviceDetail.objects.create(service=cls.royaume, completeName="Mwami A", yearOfTaken=date(1990, 1, 1),
                                     encore_vivant=True, image="images/r.jpg")
        cls.galerie = Galleries.objects.create(title="Baskets", subtile="Crafts", description="Woven.", image="images/g.jpg")
        GalleryImages.objects.create(gallery=cls.galerie, title="Basket", image="images/b.jpg", description="Old basket")
        agentsModel.objects.create(name="Jane", role="Curator", image_pic="images/j.jpg")

    def test_pages_in_three_languages(self):
        for prefixe in ("", "/fr", "/sw"):
            for nom, args in [("index", []), ("about", []), ("services", []), ("gallery", []), ("agents", []),
                              ("contact", []), ("donate", []), ("service_details", [self.royaume.slug]),
                              ("gallery_single", [self.galerie.pk])]:
                with translation.override("en"):
                    url = prefixe + reverse(nom, args=args)
                reponse = self.client.get(url)
                self.assertEqual(reponse.status_code, 200, url)

    def test_translated_content_and_fallback(self):
        self.assertContains(self.client.get("/fr/"), "Notre patrimoine")
        self.assertContains(self.client.get("/sw/services"), "Ufalme wa Bufuliiru")
        # No French title for the kingdom: the English one is shown
        self.assertContains(self.client.get("/fr/services"), "Kingdom of Bufuliiru")

    def test_interface_is_translated(self):
        self.assertContains(self.client.get("/fr/"), "Faire un don")
        self.assertContains(self.client.get("/sw/"), "Changia")

    def test_slug_created_automatically(self):
        page = servicesModel.objects.create(title="Our Programmes", details="x", image_pic="images/p.jpg")
        self.assertEqual(page.slug, "our-programmes")
        double = servicesModel.objects.create(title="Our Programmes", details="y", image_pic="images/p.jpg")
        self.assertEqual(double.slug, "our-programmes-2")

    def test_lineage_shown(self):
        reponse = self.client.get(reverse("service_details", args=[self.royaume.slug]))
        self.assertContains(reponse, "Mwami A")

    def test_unknown_pages_give_404(self):
        self.assertEqual(self.client.get("/service_details/does-not-exist").status_code, 404)
        self.assertEqual(self.client.get("/gallery_single/9999/").status_code, 404)
        self.assertEqual(self.client.get("/fr/service_details/does-not-exist").status_code, 404)

    def setUp(self):
        # Each test starts in English (a request to /fr/ leaves French active)
        translation.activate("en")

    def test_old_donation_address_redirects(self):
        self.assertRedirects(self.client.get(reverse("dialog")), reverse("donate"), status_code=301)

    def test_sitemap_and_robots(self):
        self.assertContains(self.client.get("/sitemap.xml"), self.royaume.slug)
        self.assertContains(self.client.get("/robots.txt"), "Sitemap: https://nafuv.test/sitemap.xml")

    def test_site_settings_have_translated_defaults(self):
        site = SiteSettings.charger()
        self.assertTrue(site.texte_mission_fr)
        self.assertTrue(site.texte_mission_sw)
        with translation.override("fr"):
            self.assertEqual(tr(site, "slogan"), site.slogan_fr)
        with translation.override("en"):
            self.assertEqual(tr(site, "slogan"), site.slogan)


@override_settings(STORAGES=STOCKAGE_SIMPLE, SECURE_SSL_REDIRECT=False, CONTACT_EMAIL="team@nafuv.test")
class ContactTests(TestCase):
    def test_message_saved_and_sent(self):
        reponse = self.client.post(reverse("contact"), {
            "nom": "Aline", "email": "aline@example.com", "sujet": "A basket", "message": "I have an old basket.",
        })
        self.assertRedirects(reponse, reverse("contact"))
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["team@nafuv.test"])

    def test_spam_robot_ignored(self):
        self.client.post(reverse("contact"), {
            "nom": "Bot", "email": "bot@example.com", "sujet": "Buy", "message": "Spam", "site_web": "http://spam",
        })
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_form(self):
        reponse = self.client.post(reverse("contact"), {"nom": "", "email": "wrong", "sujet": "", "message": ""})
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)


@override_settings(
    STORAGES=STOCKAGE_SIMPLE, SECURE_SSL_REDIRECT=False, SITE_URL="https://nafuv.test",
    STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET=SECRET_WEBHOOK, CONTACT_EMAIL="team@nafuv.test",
)
class DonationTests(TestCase):
    DONNEES = {"montant_choisi": "50", "montant": "", "nom": "Paul", "email": "paul@example.com", "message": "Courage"}

    @mock.patch("mainApp.stripe_api._appel")
    def test_donation_goes_to_stripe(self, appel):
        appel.return_value = {"id": "cs_test_1", "url": "https://checkout.stripe.com/c/pay/cs_test_1"}
        reponse = self.client.post(reverse("donate"), self.DONNEES)
        self.assertRedirects(reponse, "https://checkout.stripe.com/c/pay/cs_test_1", fetch_redirect_response=False)
        don = Donation.objects.get()
        self.assertEqual(don.montant, Decimal("50.00"))
        self.assertEqual(don.stripe_session, "cs_test_1")
        self.assertEqual(don.statut, Donation.EN_ATTENTE)
        methode, chemin, donnees = appel.call_args[0]
        self.assertEqual(chemin, "/checkout/sessions")
        self.assertEqual(donnees["line_items"][0]["price_data"]["unit_amount"], 5000)
        self.assertIn("{CHECKOUT_SESSION_ID}", donnees["success_url"])

    def test_amount_validation(self):
        for montant in ("0", "abc", "999999"):
            reponse = self.client.post(reverse("donate"), {**self.DONNEES, "montant_choisi": "", "montant": montant})
            self.assertEqual(reponse.status_code, 200)
        self.assertEqual(Donation.objects.count(), 0)

    @mock.patch("mainApp.stripe_api._appel", side_effect=stripe_api.StripeErreur("down"))
    def test_stripe_unavailable(self, appel):
        reponse = self.client.post(reverse("donate"), self.DONNEES)
        self.assertRedirects(reponse, reverse("donate"))

    @override_settings(STRIPE_SECRET_KEY="")
    def test_without_stripe_keys(self):
        reponse = self.client.get(reverse("donate"))
        self.assertContains(reponse, "Online donations are coming soon")

    def _webhook(self, evenement, secret=SECRET_WEBHOOK):
        corps = json.dumps(evenement).encode()
        return self.client.post(
            reverse("donation_webhook"), data=corps, content_type="application/json",
            HTTP_STRIPE_SIGNATURE=stripe_api.signer_pour_test(corps, secret),
        )

    def test_webhook_confirms_donation_once(self):
        don = Donation.objects.create(nom="Paul", email="paul@example.com", montant=Decimal("30"), stripe_session="cs_1")
        evenement = {"type": "checkout.session.completed",
                     "data": {"object": {"id": "cs_1", "payment_status": "paid", "payment_intent": "pi_1"}}}
        self.assertEqual(self._webhook(evenement).status_code, 200)
        self._webhook(evenement)  # Stripe may send the same event twice
        don.refresh_from_db()
        self.assertEqual(don.statut, Donation.PAYE)
        self.assertEqual(don.stripe_paiement, "pi_1")
        self.assertEqual(len(mail.outbox), 2)  # thank-you to the donor + notice to the team

    def test_webhook_bad_signature_refused(self):
        evenement = {"type": "checkout.session.completed", "data": {"object": {"id": "cs_1", "payment_status": "paid"}}}
        self.assertEqual(self._webhook(evenement, secret="whsec_other").status_code, 400)

    def test_webhook_expired_session(self):
        don = Donation.objects.create(nom="Paul", email="paul@example.com", montant=Decimal("30"), stripe_session="cs_2")
        self._webhook({"type": "checkout.session.expired", "data": {"object": {"id": "cs_2"}}})
        don.refresh_from_db()
        self.assertEqual(don.statut, Donation.ABANDONNE)

    @mock.patch("mainApp.stripe_api._appel")
    def test_thank_you_page_checks_stripe(self, appel):
        Donation.objects.create(nom="Paul", email="paul@example.com", montant=Decimal("70"), stripe_session="cs_3")
        appel.return_value = {"id": "cs_3", "payment_status": "paid", "payment_intent": "pi_3"}
        reponse = self.client.get(reverse("donate_thanks") + "?session_id=cs_3")
        self.assertContains(reponse, "Thank you, Paul!")
        self.assertEqual(Donation.objects.get().statut, Donation.PAYE)


class StripeSignatureTests(TestCase):
    def test_valid_signature(self):
        corps = b'{"type": "x"}'
        entete = stripe_api.signer_pour_test(corps, "whsec_a", horodatage=1_700_000_000)
        evenement = stripe_api.verifier_webhook(corps, entete, secret="whsec_a", maintenant=1_700_000_010)
        self.assertEqual(evenement["type"], "x")

    def test_old_signature_refused(self):
        corps = b"{}"
        entete = stripe_api.signer_pour_test(corps, "whsec_a", horodatage=1_700_000_000)
        with self.assertRaises(stripe_api.StripeErreur):
            stripe_api.verifier_webhook(corps, entete, secret="whsec_a", maintenant=1_700_009_999)

    def test_nested_encoding(self):
        paires = dict(stripe_api._encoder({"line_items": [{"price_data": {"unit_amount": 500}}], "metadata": {"id": 3}}))
        self.assertEqual(paires["line_items[0][price_data][unit_amount]"], "500")
        self.assertEqual(paires["metadata[id]"], "3")


# ===========================================================================
# Text formatting, image processing, administration dashboard
# ===========================================================================
import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from .texte import mettre_en_forme

MEDIA_TEST = tempfile.mkdtemp()


class TexteTests(TestCase):
    def test_long_one_line_text_is_split_into_paragraphs(self):
        texte = "The kingdom is very old. It was founded long ago by our ancestors. " * 15
        self.assertGreater(mettre_en_forme(texte).count("<p>"), 2)

    def test_headings_lists_bold_and_escaping(self):
        html = mettre_en_forme("## History\nFirst line\n\n- one\n- two\n\n**Bold** <script>")
        self.assertIn("<h3>History</h3>", html)
        self.assertIn("<ul><li>one</li><li>two</li></ul>", html)
        self.assertIn("<strong>Bold</strong>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_each_line_is_a_paragraph(self):
        self.assertEqual(mettre_en_forme("A.\nB."), "<p>A.</p><p>B.</p>")


def _photo_telephone(largeur=4000, hauteur=3000):
    """A large JPEG saved sideways, as phones do (EXIF orientation 6)."""
    from PIL import Image

    image = Image.new("RGB", (largeur, hauteur), (180, 120, 60))
    exif = image.getexif()
    exif[0x0112] = 6
    tampon = io.BytesIO()
    image.save(tampon, "JPEG", exif=exif.tobytes(), quality=95)
    return SimpleUploadedFile("photo.jpg", tampon.getvalue(), content_type="image/jpeg")


@override_settings(STORAGES=STOCKAGE_SIMPLE, MEDIA_ROOT=MEDIA_TEST, SECURE_SSL_REDIRECT=False)
class ImagesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def test_uploaded_photo_is_rotated_and_resized(self):
        from PIL import Image

        slide = homeSilde.objects.create(image_pic=_photo_telephone(), span="a", title="b", details="c")
        with Image.open(slide.image_pic.path) as image:
            self.assertEqual(image.size, (1500, 2000))  # turned upright, longest side 2000 px

    def test_existing_pictures_command(self):
        homeSilde.objects.create(image_pic=_photo_telephone(), span="a", title="b", details="c")
        homeSilde.objects.create(image_pic="images/missing.jpg", span="a", title="b", details="c")
        sortie = io.StringIO()
        call_command("optimiser_images", stdout=sortie)
        self.assertIn("1 missing file", sortie.getvalue())

    def test_page_with_missing_picture_does_not_crash(self):
        servicesModel.objects.create(title="No image", details="x", image_pic="")
        self.assertEqual(self.client.get(reverse("services")).status_code, 200)


@override_settings(STORAGES=STOCKAGE_SIMPLE, SECURE_SSL_REDIRECT=False)
class TableauDeBordTests(TestCase):
    def setUp(self):
        translation.activate("en")
        admin = get_user_model().objects.create_superuser("admin", "admin@nafuv.test", "Motdepasse-2026")
        self.client.force_login(admin)
        servicesModel.objects.create(title="Kingdom", details="Text", iskingdom=True, image_pic="images/k.jpg")
        Donation.objects.create(nom="Paul", email="p@example.com", montant=Decimal("40"), statut=Donation.PAYE,
                                paye_le=timezone.now())
        ContactMessage.objects.create(nom="Aline", email="a@example.com", sujet="Hello", message="Hi")

    def test_dashboard(self):
        reponse = self.client.get("/admin/")
        self.assertContains(reponse, "Museum content")
        self.assertContains(reponse, "Translations to complete")
        self.assertContains(reponse, "$40.00")
        self.assertContains(reponse, "Hello")

    def test_missing_translation_filter(self):
        reponse = self.client.get("/admin/mainApp/servicesmodel/?traduction=fr")
        self.assertContains(reponse, "Kingdom")

    def test_admin_pages_open(self):
        for url in ["/admin/mainApp/servicesmodel/add/", "/admin/mainApp/galleries/add/",
                    "/admin/mainApp/sitesettings/", "/admin/mainApp/donation/", "/admin/mainApp/contactmessage/"]:
            self.assertIn(self.client.get(url, follow=True).status_code, (200,), url)


@override_settings(STORAGES=STOCKAGE_SIMPLE, SECURE_SSL_REDIRECT=False, SITE_URL="https://nafuv.org")
class PartageTests(TestCase):
    """Open Graph tags read by Facebook, WhatsApp, LinkedIn and X."""

    def setUp(self):
        translation.activate("en")
        self.royaume = servicesModel.objects.create(title="Kingdom of Bufuliiru", details="Long history " * 20,
                                                    iskingdom=True, image_pic="images/kingdom.jpg")

    def test_home_uses_branded_image(self):
        reponse = self.client.get("/")
        self.assertContains(reponse, '<meta property="og:image" content="https://nafuv.org/static/nafuv/img/partage.jpg">', html=False)
        self.assertContains(reponse, '<meta property="og:image:width" content="1200">', html=False)
        self.assertContains(reponse, '"@type": "Museum"')

    def test_detail_page_uses_its_own_picture(self):
        reponse = self.client.get(self.royaume.get_absolute_url())
        self.assertContains(reponse, '<meta property="og:image" content="https://nafuv.org/media/images/kingdom.jpg">', html=False)
        self.assertContains(reponse, '<meta property="og:title" content="Kingdom of Bufuliiru · NAFUV">', html=False)
        self.assertContains(reponse, '<meta property="og:type" content="article">', html=False)

    def test_locale_follows_language(self):
        self.assertContains(self.client.get("/fr/"), '<meta property="og:locale" content="fr_FR">', html=False)
        self.assertContains(self.client.get("/sw/"), '<meta property="og:locale" content="sw_KE">', html=False)
