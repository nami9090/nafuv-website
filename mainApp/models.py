"""
Content of the NAFUV virtual museum.

IMPORTANT: the existing models keep their class names, table names and
fields, so the content already entered on nafuv.org is preserved. New
fields only (translations, ordering, alt texts) and new models
(site settings, donations, contact messages) are added.
"""
from datetime import date

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

LANGUES_TRADUITES = ("fr", "sw")


def ajouter_traductions(model, champs):
    """
    Adds `<field>_fr` and `<field>_sw` (optional) for each listed field.
    Templates show the version of the visitor's language, or the English
    text when the translation is empty (filter |tr in nafuv_tags).
    """
    for nom in champs:
        base = model._meta.get_field(nom)
        for langue in LANGUES_TRADUITES:
            libelle = f"{base.verbose_name} ({'French' if langue == 'fr' else 'Swahili'})"
            if isinstance(base, models.TextField):
                champ = models.TextField(libelle, blank=True, default="")
            else:
                champ = models.CharField(libelle, max_length=base.max_length, blank=True, default="")
            model.add_to_class(f"{nom}_{langue}", champ)


# ===========================================================================
# Existing content (tables kept as they are)
# ===========================================================================
class homeSilde(models.Model):
    """Home page slideshow."""

    image_pic = models.ImageField("image", upload_to="images/")
    span = models.CharField("small text above the title", max_length=50)
    title = models.CharField("title", max_length=50)
    details = models.CharField("text", max_length=100)
    order = models.PositiveIntegerField("order", default=0)

    class Meta:
        verbose_name = "home slide"
        verbose_name_plural = "home slides"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class whoWeareHome(models.Model):
    title = models.CharField("title", max_length=100)
    first_paragraph = models.CharField("first paragraph", max_length=1000)
    second_paragraph = models.CharField("second paragraph", max_length=1000)

    class Meta:
        verbose_name = "“Who we are” text"
        verbose_name_plural = "“Who we are” text"

    def __str__(self):
        return self.title


class whoWeareHomeimage(models.Model):
    whoWeare = models.ForeignKey(whoWeareHome, on_delete=models.CASCADE, related_name="images", verbose_name="text")
    image = models.ImageField("image", upload_to="images/")

    class Meta:
        verbose_name = "“Who we are” image"
        verbose_name_plural = "“Who we are” images"

    def __str__(self):
        return f"Image for {self.whoWeare.title}"


class servicesModel(models.Model):
    """Heritage pages: kingdoms, collections, programmes."""

    title = models.CharField("title", max_length=100)
    details = models.TextField("text")
    iskingdom = models.BooleanField("this is a kingdom (shows the royal lineage)", default=False)
    image_pic = models.ImageField("image", upload_to="images/")
    slug = models.SlugField("web address", default="", blank=True)
    order = models.PositiveIntegerField("order", default=0)

    class Meta:
        verbose_name = "heritage page (kingdom, programme…)"
        verbose_name_plural = "heritage pages (kingdoms, programmes…)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:45] or "page"
            slug, n = base, 2
            while servicesModel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("service_details", args=[self.slug])


class serviceDetail(models.Model):
    """A ruler in the royal lineage of a kingdom."""

    service = models.ForeignKey(servicesModel, related_name="detail", on_delete=models.CASCADE, verbose_name="kingdom")
    completeName = models.CharField("full name", max_length=100)
    yearOfTaken = models.DateField("start of reign")
    encore_vivant = models.BooleanField("still reigning", default=False)
    yearOfDeath = models.DateField("end of reign", null=True, blank=True)
    image = models.ImageField("portrait", upload_to="images/")

    class Meta:
        verbose_name = "ruler"
        verbose_name_plural = "royal lineage"
        ordering = ["yearOfTaken", "id"]

    def __str__(self):
        if self.encore_vivant:
            annees = date.today().year - self.yearOfTaken.year
            return f"{self.completeName}, reigning since {self.yearOfTaken.year} ({annees} years)"
        if self.yearOfDeath:
            return f"{self.completeName}, {self.yearOfTaken.year}–{self.yearOfDeath.year}"
        return f"{self.completeName}, since {self.yearOfTaken.year}"

    @property
    def annees_regne(self):
        fin = date.today() if self.encore_vivant or not self.yearOfDeath else self.yearOfDeath
        return max(fin.year - self.yearOfTaken.year, 0)


class Galleries(models.Model):
    title = models.CharField("title", max_length=100)
    subtile = models.CharField("subtitle", max_length=100)
    description = models.TextField("description")
    image = models.ImageField("cover image", upload_to="images/")
    order = models.PositiveIntegerField("order", default=0)

    class Meta:
        verbose_name = "gallery"
        verbose_name_plural = "galleries"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("gallery_single", args=[self.pk])


class GalleryImages(models.Model):
    gallery = models.ForeignKey(Galleries, related_name="images", on_delete=models.CASCADE, verbose_name="gallery")
    title = models.CharField("title", max_length=100)
    image = models.ImageField("image", upload_to="images/")
    description = models.TextField("description", blank=True)
    slug = models.SlugField("web address", default="", blank=True)

    class Meta:
        verbose_name = "object / photo"
        verbose_name_plural = "objects / photos"
        ordering = ["id"]

    def __str__(self):
        return self.title or f"Image of {self.gallery}"


class agentsModel(models.Model):
    name = models.CharField("name", max_length=100)
    role = models.CharField("role", max_length=100)
    image_pic = models.ImageField("photo", upload_to="images/")
    lien_1 = models.CharField("X / Twitter link", max_length=100000, blank=True)
    lien_2 = models.CharField("Facebook link", max_length=100000, blank=True)
    lien_3 = models.CharField("Instagram link", max_length=100000, blank=True)
    lien_4 = models.CharField("LinkedIn link", max_length=100000, blank=True)
    order = models.PositiveIntegerField("order", default=0)

    class Meta:
        verbose_name = "team member"
        verbose_name_plural = "team"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


# Old, unused models: kept so that their tables are not deleted.
class address(models.Model):
    name = models.CharField(max_length=100)


class callUs(models.Model):
    name = models.CharField(max_length=100)


class emailUs(models.Model):
    name = models.CharField(max_length=100)


# ===========================================================================
# New: site settings (address, contact, texts of the About page)
# ===========================================================================
TEXTE_BACKGROUND = (
    "Over the past three decades, the migration of people from the land of Uvira, home of the ancestral "
    "kingdoms of the Fuliiru and Vira peoples, to North America has left a cultural vacuum in the minds of a "
    "generation of young men and women. Life experiences in Canada and the United States suggest that this "
    "vacuum may already reach back two generations. Canadians and Americans of Fuliiru-Vira descent are not "
    "only losing the taste of their ancestral languages and traditions; they are also losing track of the "
    "artifacts, proverbs, arts and sculptures inherited from their forefathers. NAFV Int. is dedicated to "
    "collecting, protecting and preserving these cultural writings, objects, photographs, audio recordings, "
    "artworks and social customs."
)
TEXTE_BACKGROUND_FR = (
    "Depuis trois décennies, la migration des habitants de la terre d'Uvira, berceau des royaumes ancestraux "
    "des peuples Fuliiru et Vira, vers l'Amérique du Nord a laissé un vide culturel dans l'esprit de toute une "
    "génération de jeunes femmes et de jeunes hommes. L'expérience vécue au Canada et aux États-Unis laisse "
    "penser que ce vide remonte déjà à deux générations. Les Canadiens et Américains d'ascendance Fuliiru-Vira "
    "perdent non seulement le goût de leurs langues et traditions ancestrales, mais aussi la trace des objets, "
    "proverbes, arts et sculptures hérités de leurs ancêtres. NAFV Int. se consacre à collecter, protéger et "
    "préserver ces écrits, objets, photographies, enregistrements sonores, œuvres d'art et coutumes."
)
TEXTE_BACKGROUND_SW = (
    "Kwa miongo mitatu iliyopita, uhamiaji wa watu kutoka nchi ya Uvira, chimbuko la falme za jadi za watu wa "
    "Fuliiru na Vira, kwenda Amerika Kaskazini umeacha pengo la kitamaduni katika akili za kizazi kizima cha "
    "vijana. Uzoefu wa maisha nchini Kanada na Marekani unaonyesha kwamba pengo hili huenda tayari linagusa "
    "vizazi viwili. Wakanada na Wamarekani wenye asili ya Fuliiru-Vira si tu wanapoteza ladha ya lugha na mila "
    "za mababu zao, bali pia wanapoteza alama za vitu vya sanaa, methali, sanaa na vinyago walivyorithi. "
    "NAFV Int. imejitolea kukusanya, kulinda na kuhifadhi maandishi, vitu, picha, rekodi za sauti, kazi za "
    "sanaa na desturi hizi za kitamaduni."
)
TEXTE_MISSION = (
    "NAFV Int. pursues the mission of collecting, protecting and preserving the heritage inherited from our "
    "ancestors, and of educating its members and communities about the importance of learning about the "
    "cultures, people, lifestyles and practices of the past, so that they can understand the future."
)
TEXTE_MISSION_FR = (
    "NAFV Int. a pour mission de collecter, protéger et préserver le patrimoine hérité de nos ancêtres, et "
    "d'éduquer ses membres et les communautés à l'importance de connaître les cultures, les peuples, les modes "
    "de vie et les pratiques du passé, pour mieux comprendre l'avenir."
)
TEXTE_MISSION_SW = (
    "NAFV Int. ina dhamira ya kukusanya, kulinda na kuhifadhi urithi tulioachiwa na mababu zetu, na kuelimisha "
    "wanachama wake na jamii kuhusu umuhimu wa kujifunza tamaduni, watu, mitindo ya maisha na desturi za zamani, "
    "ili kuelewa siku zijazo."
)
TEXTE_ACTIVITES = (
    "Our main activities are a virtual museum and a physical cultural museum in Uvira, in the Democratic "
    "Republic of the Congo. The virtual museum preserves the culture of the Fuliiru and Vira peoples online, "
    "for education and research. It is also a place where young generations are invited to get involved, "
    "especially during our yearly exhibition at the headquarters."
)
TEXTE_ACTIVITES_FR = (
    "Nos principales activités sont un musée virtuel et un musée culturel physique à Uvira, en République "
    "démocratique du Congo. Le musée virtuel préserve en ligne la culture des peuples Fuliiru et Vira, pour "
    "l'éducation et la recherche. C'est aussi un lieu où les jeunes générations sont invitées à s'impliquer, "
    "notamment lors de notre exposition annuelle au siège."
)
TEXTE_ACTIVITES_SW = (
    "Shughuli zetu kuu ni jumba la makumbusho la mtandaoni na jumba la makumbusho la kitamaduni huko Uvira, "
    "Jamhuri ya Kidemokrasia ya Kongo. Makumbusho ya mtandaoni yanahifadhi utamaduni wa watu wa Fuliiru na Vira "
    "kwa ajili ya elimu na utafiti. Pia ni mahali ambapo vizazi vichanga vinaalikwa kushiriki, hasa wakati wa "
    "maonyesho yetu ya kila mwaka katika makao makuu."
)
TEXTE_DONS = (
    "Your gift helps us collect, preserve and share the heritage of the Fuliiru and Vira peoples: "
    "digitising objects and photographs, recording elders, and supporting the cultural museum in Uvira."
)
TEXTE_DONS_FR = (
    "Votre don nous aide à collecter, préserver et partager le patrimoine des peuples Fuliiru et Vira : "
    "numérisation d'objets et de photographies, enregistrement des anciens et soutien au musée culturel d'Uvira."
)
TEXTE_DONS_SW = (
    "Mchango wako unatusaidia kukusanya, kuhifadhi na kushiriki urithi wa watu wa Fuliiru na Vira: "
    "kuweka vitu na picha katika mfumo wa kidijitali, kurekodi wazee, na kusaidia jumba la makumbusho la Uvira."
)


class SiteSettings(models.Model):
    """One single row, edited in the admin. Empty fields fall back to English."""

    nom = models.CharField("organisation name", max_length=120, default="North America Fuliiru Vira Virtual Museum")
    slogan = models.CharField(
        "tagline", max_length=200, default="Preserving the heritage of the Fuliiru and Vira peoples",
    )
    adresse = models.CharField("address", max_length=255, default="NAFV Int. · 2105 Megan Creek Dr, Little Elm, TX 75068, USA")
    telephone = models.CharField("phone", max_length=40, default="+1 817 881 2876")
    email = models.EmailField("public e-mail", default="info@nafuv.org")
    horaires = models.CharField("opening hours", max_length=120, default="Monday – Saturday · 11 am – 11 pm")

    facebook = models.URLField("Facebook", blank=True)
    instagram = models.URLField("Instagram", blank=True)
    youtube = models.URLField("YouTube", blank=True)
    twitter = models.URLField("X / Twitter", blank=True)
    linkedin = models.URLField("LinkedIn", blank=True)

    texte_background = models.TextField("About page · background", default=TEXTE_BACKGROUND)
    texte_mission = models.TextField("About page · mission", default=TEXTE_MISSION)
    texte_activites = models.TextField("About page · activities", default=TEXTE_ACTIVITES)
    texte_dons = models.TextField("Donate page · introduction", default=TEXTE_DONS)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def charger(cls):
        obj, cree = cls.objects.get_or_create(pk=1)
        if cree:
            # First creation: French and Swahili versions of the default texts
            cls.objects.filter(pk=1).update(
                slogan_fr="Préserver le patrimoine des peuples Fuliiru et Vira",
                slogan_sw="Kuhifadhi urithi wa watu wa Fuliiru na Vira",
                horaires_fr="Du lundi au samedi · 11 h – 23 h",
                horaires_sw="Jumatatu – Jumamosi · saa 5 asubuhi – saa 5 usiku",
                texte_background_fr=TEXTE_BACKGROUND_FR, texte_background_sw=TEXTE_BACKGROUND_SW,
                texte_mission_fr=TEXTE_MISSION_FR, texte_mission_sw=TEXTE_MISSION_SW,
                texte_activites_fr=TEXTE_ACTIVITES_FR, texte_activites_sw=TEXTE_ACTIVITES_SW,
                texte_dons_fr=TEXTE_DONS_FR, texte_dons_sw=TEXTE_DONS_SW,
            )
            obj.refresh_from_db()
        return obj

    @property
    def reseaux(self):
        return [
            (nom, lien)
            for nom, lien in (
                ("facebook", self.facebook), ("instagram", self.instagram), ("youtube", self.youtube),
                ("twitter", self.twitter), ("linkedin", self.linkedin),
            )
            if lien
        ]


# ===========================================================================
# New: donations (Stripe) and contact messages
# ===========================================================================
class Donation(models.Model):
    EN_ATTENTE = "pending"
    PAYE = "paid"
    ABANDONNE = "abandoned"
    STATUTS = [(EN_ATTENTE, "Pending"), (PAYE, "Paid"), (ABANDONNE, "Abandoned")]

    nom = models.CharField("name", max_length=120)
    email = models.EmailField("e-mail")
    montant = models.DecimalField("amount", max_digits=10, decimal_places=2)
    devise = models.CharField("currency", max_length=3, default="usd")
    message = models.TextField("message", blank=True)
    anonyme = models.BooleanField("wishes to stay anonymous", default=False)
    langue = models.CharField("language", max_length=5, default="en")
    statut = models.CharField("status", max_length=10, choices=STATUTS, default=EN_ATTENTE, db_index=True)
    stripe_session = models.CharField("Stripe session", max_length=255, blank=True, db_index=True)
    stripe_paiement = models.CharField("Stripe payment", max_length=255, blank=True)
    cree_le = models.DateTimeField("created", default=timezone.now)
    paye_le = models.DateTimeField("paid", null=True, blank=True)

    class Meta:
        verbose_name = "donation"
        verbose_name_plural = "donations"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.montant} {self.devise.upper()} · {self.nom} · {self.get_statut_display()}"

    @property
    def montant_cents(self):
        return int(self.montant * 100)


class ContactMessage(models.Model):
    nom = models.CharField("name", max_length=120)
    email = models.EmailField("e-mail")
    sujet = models.CharField("subject", max_length=200)
    message = models.TextField("message")
    recu_le = models.DateTimeField("received", default=timezone.now)
    traite = models.BooleanField("handled", default=False)

    class Meta:
        verbose_name = "contact message"
        verbose_name_plural = "contact messages"
        ordering = ["-recu_le"]

    def __str__(self):
        return f"{self.sujet} · {self.nom}"


# ===========================================================================
# French and Swahili versions of the content
# ===========================================================================
ajouter_traductions(homeSilde, ["span", "title", "details"])
ajouter_traductions(whoWeareHome, ["title", "first_paragraph", "second_paragraph"])
ajouter_traductions(servicesModel, ["title", "details"])
ajouter_traductions(Galleries, ["title", "subtile", "description"])
ajouter_traductions(GalleryImages, ["title", "description"])
ajouter_traductions(agentsModel, ["role"])
ajouter_traductions(SiteSettings, ["slogan", "horaires", "texte_background", "texte_mission", "texte_activites", "texte_dons"])
