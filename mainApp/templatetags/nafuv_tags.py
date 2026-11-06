"""
    {% load nafuv_tags %}
    {{ slide|tr:"title" }}   → French / Swahili version if filled, otherwise English
    {{ text|paragraphs }}    → line breaks turned into paragraphs
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from ..texte import mettre_en_forme
from ..texte import resume as resume_texte

register = template.Library()


@register.filter
def tr(obj, champ):
    if obj is None:
        return ""
    langue = (get_language() or "en")[:2]
    if langue != "en":
        valeur = getattr(obj, f"{champ}_{langue}", "")
        if valeur:
            return valeur
    return getattr(obj, champ, "")


@register.filter
def paragraphs(texte):
    """Well-spaced HTML: paragraphs, ## headings, - lists, **bold** (see mainApp/texte.py)."""
    return mark_safe(mettre_en_forme(texte))


@register.filter
def resume(texte, mots=25):
    """Plain-text summary without formatting marks (cards, page descriptions)."""
    return resume_texte(texte, int(mots))


@register.filter
def url_image(champ):
    """Address of an image, or "" if none is attached (instead of a server error)."""
    try:
        return champ.url if champ else ""
    except ValueError:
        return ""


LOCALES_OG = {"en": "en_US", "fr": "fr_FR", "sw": "sw_KE"}


@register.simple_tag
def locale_og(code):
    """Language code as expected by Open Graph (en_US, fr_FR, sw_KE)."""
    return LOCALES_OG.get((code or "en")[:2], "en_US")


@register.filter
def absolu(url):
    """Full address (https://nafuv.org/media/…) required by social networks."""
    from django.conf import settings

    if not url:
        return ""
    url = str(url)
    if url.startswith(("http://", "https://")):
        return url
    return settings.SITE_URL.rstrip("/") + "/" + url.lstrip("/")


@register.simple_tag
def jsonld_musee(site):
    """Structured data (schema.org Museum) read by Google for the knowledge panel."""
    import json

    from django.conf import settings
    from django.templatetags.static import static

    donnees = {
        "@context": "https://schema.org",
        "@type": "Museum",
        "name": site.nom,
        "alternateName": "NAFUV",
        "description": site.slogan,
        "url": settings.SITE_URL,
        "logo": absolu(static("assets/img/museeLogo.png")),
        "image": absolu(static("nafuv/img/partage.jpg")),
        "address": site.adresse,
        "telephone": site.telephone,
        "email": site.email,
        "sameAs": [lien for _nom, lien in site.reseaux],
    }
    texte = json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")
    return mark_safe(f'<script type="application/ld+json">{texte}</script>')


@register.simple_tag(takes_context=True)
def url_langue(context, code):
    """Address of the current page in another language (used by the language switcher)."""
    from django.urls import translate_url

    request = context.get("request")
    if request is None:
        return "/"
    return translate_url(request.get_full_path(), code)
