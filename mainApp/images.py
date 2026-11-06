"""
Image processing for every picture uploaded in the admin:

  - rotates phone photos the right way up (EXIF orientation), the main cause
    of pictures appearing sideways or upside down on the site;
  - reduces very large photos (max 2000 px on the longest side) so that pages
    load fast even on a mobile connection in Uvira;
  - recompresses them (JPEG quality 85, or PNG when there is transparency);
  (files that are not images are already refused by the admin form.)

Existing pictures can be processed with:
    python manage.py optimiser_images            (see what would change)
    python manage.py optimiser_images --appliquer
"""
import io
import logging
import os

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

TAILLE_MAX = 2000          # pixels, longest side
QUALITE_JPEG = 85


def traiter(fichier, taille_max=TAILLE_MAX):
    """
    Returns (bytes, extension) of the processed image, or None if nothing
    needs to change. Raises ValidationError if the file is not an image.
    """
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        fichier.seek(0)
        image = Image.open(fichier)
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("This file is not a valid image (JPEG, PNG or WebP expected).") from exc

    format_origine = (image.format or "").upper()
    if format_origine == "GIF" and getattr(image, "is_animated", False):
        return None  # animated GIF: kept as it is

    orientation = image.getexif().get(0x0112, 1)
    trop_grande = max(image.size) > taille_max
    if orientation == 1 and not trop_grande and format_origine in ("JPEG", "PNG", "WEBP"):
        fichier.seek(0)
        if len(fichier.read()) <= 1.5 * 1024 * 1024:
            fichier.seek(0)
            return None  # already fine: leave the original untouched

    image = ImageOps.exif_transpose(image)
    if trop_grande:
        image.thumbnail((taille_max, taille_max), Image.LANCZOS)

    transparence = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    sortie = io.BytesIO()
    if transparence:
        image.save(sortie, "PNG", optimize=True)
        extension = ".png"
    else:
        image.convert("RGB").save(sortie, "JPEG", quality=QUALITE_JPEG, optimize=True, progressive=True)
        extension = ".jpg"
    fichier.seek(0)
    return sortie.getvalue(), extension


def nouveau_nom(nom, extension):
    base, _ = os.path.splitext(os.path.basename(nom))
    return f"{base}{extension}"


def traiter_champ(champ):
    """Processes a newly uploaded ImageField file, in place, before it is saved."""
    if not champ or getattr(champ, "_committed", True):
        return  # no file, or a file already stored (not a new upload)
    resultat = traiter(champ.file)
    if resultat is None:
        return
    contenu, extension = resultat
    champ.save(nouveau_nom(champ.name, extension), ContentFile(contenu), save=False)


def champs_images(instance):
    from django.db.models import ImageField

    return [f for f in instance._meta.fields if isinstance(f, ImageField)]


def avant_enregistrement(sender, instance, **kwargs):
    """pre_save signal connected in apps.py for every model of the museum."""
    for champ in champs_images(instance):
        try:
            traiter_champ(getattr(instance, champ.name))
        except Exception:  # never block saving content because of an image
            logger.exception("Image not processed (%s.%s)", sender.__name__, champ.name)
