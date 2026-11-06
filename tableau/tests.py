"""
Dashboard tests:  python manage.py test tableau
"""
import io
import shutil
import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from mainApp.models import (
    ContactMessage, Donation, Galleries, GalleryImages, SiteSettings, homeSilde, serviceDetail, servicesModel,
)

STOCKAGE_SIMPLE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_TEST = tempfile.mkdtemp()
MDP = "Motdepasse-2026"


def image(nom="photo.jpg", taille=(400, 300)):
    from PIL import Image

    tampon = io.BytesIO()
    Image.new("RGB", taille, (150, 100, 50)).save(tampon, "JPEG")
    return SimpleUploadedFile(nom, tampon.getvalue(), content_type="image/jpeg")


@override_settings(STORAGES=STOCKAGE_SIMPLE, MEDIA_ROOT=MEDIA_TEST, SECURE_SSL_REDIRECT=False)
class TableauTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        translation.activate("en")
        Utilisateur = get_user_model()
        self.equipe = Utilisateur.objects.create_user("derek", "derek@nafuv.test", MDP, is_staff=True, first_name="Derek")
        self.visiteur = Utilisateur.objects.create_user("visiteur", "v@example.com", MDP)
        self.royaume = servicesModel.objects.create(title="Kingdom of Buvira", details="History", iskingdom=True,
                                                    image_pic="images/k.jpg")

    def connecter(self):
        self.client.force_login(self.equipe)

    # --- Access ------------------------------------------------------------------
    def test_login_required(self):
        reponse = self.client.get(reverse("tableau:accueil"))
        self.assertRedirects(reponse, f"{reverse('tableau:connexion')}?next=/dashboard/")

    def test_non_staff_refused(self):
        self.client.force_login(self.visiteur)
        self.assertEqual(self.client.get(reverse("tableau:accueil")).status_code, 403)

    def test_login_with_email(self):
        reponse = self.client.post(reverse("tableau:connexion"), {"identifiant": "derek@nafuv.test", "mot_de_passe": MDP})
        self.assertRedirects(reponse, reverse("tableau:accueil"))

    def test_login_refused_for_visitor(self):
        reponse = self.client.post(reverse("tableau:connexion"), {"identifiant": "visiteur", "mot_de_passe": MDP})
        self.assertEqual(reponse.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout(self):
        self.connecter()
        self.assertRedirects(self.client.post(reverse("tableau:deconnexion")), reverse("tableau:connexion"))

    # --- Pages -------------------------------------------------------------------
    def test_all_pages_open(self):
        self.connecter()
        Donation.objects.create(nom="Paul", email="p@example.com", montant=Decimal("25"), statut=Donation.PAYE,
                                paye_le=timezone.now())
        msg = ContactMessage.objects.create(nom="Aline", email="a@example.com", sujet="Basket", message="Hello")
        urls = [reverse("tableau:accueil"), reverse("tableau:dons"), reverse("tableau:messages"),
                reverse("tableau:message", args=[msg.pk]), reverse("tableau:reglages"), reverse("tableau:compte"),
                reverse("tableau:recherche") + "?q=Bu"]
        for code in ("slides", "presentation", "patrimoine", "galeries", "equipe"):
            urls += [reverse("tableau:liste", args=[code]), reverse("tableau:ajouter", args=[code])]
        urls += [reverse("tableau:modifier", args=["patrimoine", self.royaume.pk]),
                 reverse("tableau:supprimer", args=["patrimoine", self.royaume.pk])]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get(reverse("tableau:accueil")), "$25.00")

    def test_unknown_section(self):
        self.connecter()
        self.assertEqual(self.client.get("/dashboard/unknown/").status_code, 404)

    # --- Content -----------------------------------------------------------------
    def test_create_slide_with_translations(self):
        self.connecter()
        reponse = self.client.post(reverse("tableau:ajouter", args=["slides"]), {
            "image_pic": image(), "span": "Welcome", "title": "Our heritage", "details": "Uvira", "order": 1,
            "span_fr": "Bienvenue", "title_fr": "Notre patrimoine", "details_fr": "", "span_sw": "", "title_sw": "", "details_sw": "",
        })
        self.assertRedirects(reponse, reverse("tableau:liste", args=["slides"]))
        slide = homeSilde.objects.get()
        self.assertEqual(slide.title_fr, "Notre patrimoine")
        self.assertTrue(slide.image_pic.name.startswith("images/"))

    def test_edit_kingdom_and_add_ruler(self):
        self.connecter()
        url = reverse("tableau:modifier", args=["patrimoine", self.royaume.pk])
        reponse = self.client.post(url, {
            "title": "Kingdom of Buvira", "slug": self.royaume.slug, "details": "New history", "iskingdom": "on", "order": 2,
            "title_fr": "Royaume de Buvira", "details_fr": "", "title_sw": "", "details_sw": "",
            "sous-TOTAL_FORMS": "1", "sous-INITIAL_FORMS": "0", "sous-MIN_NUM_FORMS": "0", "sous-MAX_NUM_FORMS": "1000",
            "sous-0-completeName": "Mwami Lenghe", "sous-0-image": image("mwami.jpg"), "sous-0-yearOfTaken": "1980-01-01",
            "sous-0-encore_vivant": "on", "sous-0-yearOfDeath": "",
        })
        self.assertRedirects(reponse, reverse("tableau:liste", args=["patrimoine"]))
        self.royaume.refresh_from_db()
        self.assertEqual(self.royaume.details, "New history")
        self.assertEqual(self.royaume.title_fr, "Royaume de Buvira")
        ruler = serviceDetail.objects.get()
        self.assertEqual(ruler.yearOfTaken, date(1980, 1, 1))

    def test_gallery_with_several_pictures_at_once(self):
        self.connecter()
        reponse = self.client.post(reverse("tableau:ajouter", args=["galeries"]), {
            "title": "Baskets", "subtile": "Crafts", "image": image("cover.jpg"), "description": "Woven", "order": 0,
            "title_fr": "", "subtile_fr": "", "description_fr": "", "title_sw": "", "subtile_sw": "", "description_sw": "",
            "sous-TOTAL_FORMS": "0", "sous-INITIAL_FORMS": "0", "sous-MIN_NUM_FORMS": "0", "sous-MAX_NUM_FORMS": "1000",
            "ajout_photos": [image("old_basket.jpg"), image("royal-drum.jpg")],
            "enregistrer_continuer": "1",
        })
        galerie = Galleries.objects.get()
        self.assertRedirects(reponse, reverse("tableau:modifier", args=["galeries", galerie.pk]))
        self.assertEqual(sorted(GalleryImages.objects.values_list("title", flat=True)), ["Old basket", "Royal drum"])

    def test_invalid_form_shows_errors(self):
        self.connecter()
        reponse = self.client.post(reverse("tableau:ajouter", args=["equipe"]), {"name": ""})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Please correct the errors")

    def test_delete(self):
        self.connecter()
        reponse = self.client.post(reverse("tableau:supprimer", args=["patrimoine", self.royaume.pk]))
        self.assertRedirects(reponse, reverse("tableau:liste", args=["patrimoine"]))
        self.assertFalse(servicesModel.objects.exists())

    def test_list_search_filter_and_missing_translation(self):
        self.connecter()
        servicesModel.objects.create(title="Yearly exhibition", details="x", image_pic="images/e.jpg")
        url = reverse("tableau:liste", args=["patrimoine"])
        self.assertContains(self.client.get(url + "?q=exhib"), "Yearly exhibition")
        self.assertNotContains(self.client.get(url + "?q=exhib"), "Kingdom of Buvira")
        self.assertNotContains(self.client.get(url + "?filtre=royaumes"), "Yearly exhibition")
        self.assertContains(self.client.get(url + "?manque=fr"), "Kingdom of Buvira")

    def test_site_settings(self):
        self.connecter()
        site = SiteSettings.charger()
        donnees = {f: getattr(site, f) for f in [
            "nom", "adresse", "telephone", "email", "horaires", "slogan", "facebook", "instagram", "youtube", "twitter",
            "linkedin", "texte_background", "texte_mission", "texte_activites", "texte_dons"]}
        for c in ["slogan", "horaires", "texte_background", "texte_mission", "texte_activites", "texte_dons"]:
            for l in ("fr", "sw"):
                donnees[f"{c}_{l}"] = getattr(site, f"{c}_{l}")
        donnees["telephone"] = "+1 000 000 0000"
        self.assertRedirects(self.client.post(reverse("tableau:reglages"), donnees), reverse("tableau:reglages"))
        self.assertEqual(SiteSettings.charger().telephone, "+1 000 000 0000")

    # --- Donations and messages ----------------------------------------------------
    def test_donations_csv_export(self):
        self.connecter()
        Donation.objects.create(nom="Paul", email="p@example.com", montant=Decimal("25"), statut=Donation.PAYE,
                                paye_le=timezone.now())
        reponse = self.client.get(reverse("tableau:dons") + "?export=csv")
        self.assertEqual(reponse["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("p@example.com", reponse.content.decode("utf-8-sig"))

    def test_message_marked_as_handled(self):
        self.connecter()
        msg = ContactMessage.objects.create(nom="Aline", email="a@example.com", sujet="Basket", message="Hello")
        self.client.post(reverse("tableau:message", args=[msg.pk]))
        msg.refresh_from_db()
        self.assertTrue(msg.traite)
