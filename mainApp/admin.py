from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ContactMessage, Donation, Galleries, GalleryImages, SiteSettings, agentsModel, homeSilde, serviceDetail,
    servicesModel, whoWeareHome, whoWeareHomeimage,
)


AIDE_TEXTE = (
    "Text formatting: leave an <b>empty line</b> between two paragraphs · start a line with "
    "<b>##</b> for a sub-heading · start lines with <b>-</b> for a list · <b>**bold**</b> · <i>*italic*</i>. "
    "Pictures are automatically turned the right way up, resized and compressed when saved."
)


class TraductionFilter(admin.SimpleListFilter):
    """“Translation missing” filter, used by the links of the dashboard."""

    title = "translation"
    parameter_name = "traduction"

    def __init__(self, request, params, model, model_admin):
        self.model_admin = model_admin
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        return [("fr", "French missing"), ("sw", "Swahili missing")]

    def queryset(self, request, queryset):
        champ = getattr(self.model_admin, "champ_traduit", None)
        if champ and self.value() in ("fr", "sw"):
            return queryset.exclude(**{champ: ""}).filter(**{f"{champ}_{self.value()}": ""})
        return queryset


def groupes(principaux, traduits, autres=()):
    """Main fields, then a collapsible group per translation language."""
    return [
        (None, {"fields": list(principaux) + list(autres), "description": AIDE_TEXTE}),
        ("French version", {"fields": [f"{c}_fr" for c in traduits], "classes": ["collapse"],
                            "description": "Leave empty to show the English text."}),
        ("Swahili version", {"fields": [f"{c}_sw" for c in traduits], "classes": ["collapse"],
                             "description": "Leave empty to show the English text."}),
    ]


def apercu(image, hauteur=60):
    if not image:
        return "—"
    return format_html('<img src="{}" style="height:{}px;border-radius:6px;object-fit:cover">', image.url, hauteur)


# ---------------------------------------------------------------------------
@admin.register(homeSilde)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("miniature", "title", "span", "order")
    list_filter = (TraductionFilter,)
    champ_traduit = "title"
    list_editable = ("order",)
    fieldsets = groupes(["image_pic", "span", "title", "details"], ["span", "title", "details"], ["order"])

    @admin.display(description="image")
    def miniature(self, obj):
        return apercu(obj.image_pic)


class WhoImageInline(admin.TabularInline):
    model = whoWeareHomeimage
    extra = 1


@admin.register(whoWeareHome)
class WhoAdmin(admin.ModelAdmin):
    list_display = ("title",)
    list_filter = (TraductionFilter,)
    champ_traduit = "first_paragraph"
    inlines = [WhoImageInline]
    fieldsets = groupes(["title", "first_paragraph", "second_paragraph"], ["title", "first_paragraph", "second_paragraph"])


class LineageInline(admin.StackedInline):
    model = serviceDetail
    extra = 0
    fields = (("completeName", "image"), ("yearOfTaken", "encore_vivant", "yearOfDeath"))


@admin.register(servicesModel)
class HeritageAdmin(admin.ModelAdmin):
    list_display = ("miniature", "title", "iskingdom", "order")
    list_display_links = ("miniature", "title")
    list_editable = ("order",)
    list_filter = ("iskingdom", TraductionFilter)
    champ_traduit = "details"
    search_fields = ("title", "details")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LineageInline]
    fieldsets = groupes(["title", "slug", "image_pic", "details", "iskingdom"], ["title", "details"], ["order"])

    @admin.display(description="image")
    def miniature(self, obj):
        return apercu(obj.image_pic)


@admin.register(serviceDetail)
class RulerAdmin(admin.ModelAdmin):
    list_display = ("completeName", "service", "yearOfTaken", "yearOfDeath", "encore_vivant")
    list_filter = ("service", "encore_vivant")
    search_fields = ("completeName",)


class GalleryImageInline(admin.StackedInline):
    model = GalleryImages
    extra = 0
    fields = (("image", "title"), "description", ("title_fr", "title_sw"), ("description_fr", "description_sw"))


@admin.register(Galleries)
class GalleryAdmin(admin.ModelAdmin):
    list_filter = (TraductionFilter,)
    champ_traduit = "description"
    list_display = ("miniature", "title", "subtile", "nb_objets", "order")
    list_display_links = ("miniature", "title")
    list_editable = ("order",)
    search_fields = ("title", "description")
    inlines = [GalleryImageInline]
    fieldsets = groupes(["title", "subtile", "image", "description"], ["title", "subtile", "description"], ["order"])

    @admin.display(description="cover")
    def miniature(self, obj):
        return apercu(obj.image)

    @admin.display(description="objects")
    def nb_objets(self, obj):
        return obj.images.count()


@admin.register(GalleryImages)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("miniature", "title", "gallery")
    list_filter = ("gallery", TraductionFilter)
    champ_traduit = "title"
    search_fields = ("title", "description")
    fieldsets = groupes(["gallery", "image", "title", "description", "slug"], ["title", "description"])

    @admin.display(description="image")
    def miniature(self, obj):
        return apercu(obj.image)


@admin.register(agentsModel)
class TeamAdmin(admin.ModelAdmin):
    list_filter = (TraductionFilter,)
    champ_traduit = "role"
    list_display = ("miniature", "name", "role", "order")
    list_display_links = ("miniature", "name")
    list_editable = ("order",)
    fieldsets = groupes(["name", "role", "image_pic", "lien_1", "lien_2", "lien_3", "lien_4"], ["role"], ["order"])

    @admin.display(description="photo")
    def miniature(self, obj):
        return apercu(obj.image_pic)


# ---------------------------------------------------------------------------
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Organisation", {"fields": ["nom", "slogan", "adresse", "telephone", "email", "horaires"]}),
        ("Social networks", {"fields": ["facebook", "instagram", "youtube", "twitter", "linkedin"]}),
        ("Texts", {"fields": ["texte_background", "texte_mission", "texte_activites", "texte_dons"], "description": AIDE_TEXTE}),
        ("French version", {"classes": ["collapse"], "fields": [
            "slogan_fr", "horaires_fr", "texte_background_fr", "texte_mission_fr", "texte_activites_fr", "texte_dons_fr"]}),
        ("Swahili version", {"classes": ["collapse"], "fields": [
            "slogan_sw", "horaires_sw", "texte_background_sw", "texte_mission_sw", "texte_activites_sw", "texte_dons_sw"]}),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        return redirect("admin:mainApp_sitesettings_change", SiteSettings.charger().pk)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("cree_le", "nom", "email", "montant", "devise", "statut", "anonyme")
    list_filter = ("statut", "anonyme", "devise")
    search_fields = ("nom", "email", "stripe_session", "stripe_paiement")
    date_hierarchy = "cree_le"
    readonly_fields = [f.name for f in Donation._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("recu_le", "nom", "email", "sujet", "traite")
    list_filter = ("traite",)
    list_editable = ("traite",)
    search_fields = ("nom", "email", "sujet", "message")
    readonly_fields = ("nom", "email", "sujet", "message", "recu_le")

    def has_add_permission(self, request):
        return False
