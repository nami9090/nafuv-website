"""
Content sections of the dashboard.

Each section describes one type of content (slides, heritage pages…): which
fields are edited, which ones are translated, which picture is shown, and the
sub-items edited on the same page (royal lineage, objects of a gallery).
The generic views of views.py do the rest: list, search, create, edit, delete.
"""
from dataclasses import dataclass, field

from django.utils.translation import gettext_lazy as _

from mainApp.models import (
    Galleries, GalleryImages, SiteSettings, agentsModel, homeSilde, serviceDetail, servicesModel, whoWeareHome,
    whoWeareHomeimage,
)

LANGUES = [("en", "English"), ("fr", "Français"), ("sw", "Kiswahili")]

# Labels shown in the forms (the model names are kept for the existing database)
LIBELLES = {
    "image_pic": _("Picture"), "image": _("Picture"),
    "span": _("Small text above the title"), "title": _("Title"), "details": _("Text"),
    "order": _("Display order"), "first_paragraph": _("First paragraph"), "second_paragraph": _("Second paragraph"),
    "slug": _("Web address"), "iskingdom": _("This page is a kingdom (shows the royal lineage)"),
    "subtile": _("Subtitle"), "description": _("Description"),
    "name": _("Full name"), "role": _("Role"),
    "lien_1": _("X / Twitter link"), "lien_2": _("Facebook link"), "lien_3": _("Instagram link"), "lien_4": _("LinkedIn link"),
    "completeName": _("Full name"), "yearOfTaken": _("Start of reign"), "encore_vivant": _("Still reigning"),
    "yearOfDeath": _("End of reign"),
    "nom": _("Organisation name"), "slogan": _("Tagline"), "adresse": _("Address"), "telephone": _("Phone"),
    "email": _("Public e-mail"), "horaires": _("Opening hours"),
    "facebook": "Facebook", "instagram": "Instagram", "youtube": "YouTube", "twitter": "X / Twitter", "linkedin": "LinkedIn",
    "texte_background": _("About page: background"), "texte_mission": _("About page: mission"),
    "texte_activites": _("About page: activities"), "texte_dons": _("Donate page: introduction"),
}

AIDES = {
    "details": _("Empty line = new paragraph · ## Heading · - list item · **bold**"),
    "description": _("Empty line = new paragraph · ## Heading · - list item · **bold**"),
    "slug": _("Created automatically from the title if left empty."),
    "order": _("Smaller numbers are shown first."),
    "yearOfDeath": _("Leave empty if the ruler is still reigning."),
}


@dataclass
class SousElements:
    """Items edited on the same page as their parent (royal lineage, objects of a gallery…)."""

    modele: type
    cle: str
    champs: list
    titre: str
    image: str = "image"
    titre_champ: str = "title"
    ajout_multiple: bool = False   # several pictures can be uploaded at once


@dataclass
class Section:
    code: str
    modele: type
    titre: str
    titre_singulier: str
    icone: str
    champs: list
    traduits: list = field(default_factory=list)
    image: str = ""
    titre_champ: str = "title"
    sous_titre_champ: str = ""
    recherche: list = field(default_factory=list)
    sous_elements: SousElements = None
    filtres: list = field(default_factory=list)   # [(code, label, {lookup: value})]
    description: str = ""

    @property
    def champs_formulaire(self):
        return self.champs + [f"{c}_{langue}" for langue in ("fr", "sw") for c in self.traduits]

    def libelle_objet(self, objet):
        return str(getattr(objet, self.titre_champ, "") or objet)


SECTIONS = {
    "slides": Section(
        code="slides", modele=homeSilde, titre=_("Home slides"), titre_singulier=_("slide"), icone="diapo",
        champs=["image_pic", "span", "title", "details", "order"], traduits=["span", "title", "details"],
        image="image_pic", sous_titre_champ="span", recherche=["title", "span", "details"],
        description=_("The large pictures at the top of the home page."),
    ),
    "presentation": Section(
        code="presentation", modele=whoWeareHome, titre=_("Who we are"), titre_singulier=_("presentation text"),
        icone="info", champs=["title", "first_paragraph", "second_paragraph"],
        traduits=["title", "first_paragraph", "second_paragraph"], recherche=["title", "first_paragraph"],
        sous_elements=SousElements(whoWeareHomeimage, "whoWeare", ["image"], _("Pictures"), titre_champ="", ajout_multiple=True),
        description=_("The presentation shown on the home page and the About page."),
    ),
    "patrimoine": Section(
        code="patrimoine", modele=servicesModel, titre=_("Kingdoms & heritage"), titre_singulier=_("heritage page"),
        icone="couronne", champs=["title", "slug", "image_pic", "details", "iskingdom", "order"],
        traduits=["title", "details"], image="image_pic", recherche=["title", "details"],
        sous_elements=SousElements(
            serviceDetail, "service", ["completeName", "image", "yearOfTaken", "encore_vivant", "yearOfDeath"],
            _("Royal lineage"), titre_champ="completeName",
        ),
        filtres=[("royaumes", _("Kingdoms"), {"iskingdom": True}), ("programmes", _("Programmes"), {"iskingdom": False})],
        description=_("The ancestral kingdoms, their royal lineage, and the museum's programmes."),
    ),
    "galeries": Section(
        code="galeries", modele=Galleries, titre=_("Collections"), titre_singulier=_("collection"), icone="galerie",
        champs=["title", "subtile", "image", "description", "order"], traduits=["title", "subtile", "description"],
        image="image", sous_titre_champ="subtile", recherche=["title", "subtile", "description"],
        sous_elements=SousElements(
            GalleryImages, "gallery", ["image", "title", "description", "title_fr", "title_sw", "description_fr", "description_sw"],
            _("Objects & photos"), ajout_multiple=True,
        ),
        description=_("Galleries of objects, photographs and memories."),
    ),
    "equipe": Section(
        code="equipe", modele=agentsModel, titre=_("Team"), titre_singulier=_("team member"), icone="equipe",
        champs=["name", "role", "image_pic", "lien_1", "lien_2", "lien_3", "lien_4", "order"], traduits=["role"],
        image="image_pic", titre_champ="name", sous_titre_champ="role", recherche=["name", "role"],
        description=_("The people behind the museum."),
    ),
}

REGLAGES = Section(
    code="reglages", modele=SiteSettings, titre=_("Site settings"), titre_singulier=_("settings"), icone="reglages",
    champs=["nom", "adresse", "telephone", "email", "horaires", "slogan", "facebook", "instagram", "youtube",
            "twitter", "linkedin", "texte_background", "texte_mission", "texte_activites", "texte_dons"],
    traduits=["slogan", "horaires", "texte_background", "texte_mission", "texte_activites", "texte_dons"],
    titre_champ="nom",
)


def etat_traductions(section, objet):
    """{'fr': True/False, 'sw': True/False} for the main translated field of an object."""
    if not section.traduits:
        return {}
    champ = section.titre_champ if section.titre_champ in section.traduits else section.traduits[0]
    if not getattr(objet, champ, ""):
        return {"fr": True, "sw": True}
    return {langue: bool(getattr(objet, f"{champ}_{langue}", "")) for langue in ("fr", "sw")}
