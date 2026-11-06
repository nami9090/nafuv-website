"""
Processes the pictures already on the site (rotation, size, compression).

    python manage.py optimiser_images             # shows what would change, touches nothing
    python manage.py optimiser_images --appliquer # processes the pictures

New versions are saved next to the originals; the originals are kept on the
disk (delete them later by hand if you need the space). Make a backup of the
media folder and of the database first.
"""
from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from mainApp import images


class Command(BaseCommand):
    help = "Turns existing pictures the right way up, resizes and compresses them."

    def add_arguments(self, parser):
        parser.add_argument("--appliquer", action="store_true", help="Really process the pictures.")

    def handle(self, *args, **options):
        appliquer = options["appliquer"]
        traitees = manquantes = deja_bonnes = 0

        for modele in apps.get_app_config("mainApp").get_models():
            champs = images.champs_images(modele)
            if not champs:
                continue
            for objet in modele.objects.all():
                for champ in champs:
                    fichier = getattr(objet, champ.name)
                    if not fichier:
                        continue
                    if not fichier.storage.exists(fichier.name):
                        manquantes += 1
                        self.stdout.write(self.style.WARNING(f"  missing file: {fichier.name} ({modele.__name__} #{objet.pk})"))
                        continue
                    try:
                        with fichier.storage.open(fichier.name, "rb") as f:
                            resultat = images.traiter(f)
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(f"  unreadable: {fichier.name} ({exc})"))
                        continue
                    if resultat is None:
                        deja_bonnes += 1
                        continue
                    traitees += 1
                    contenu, extension = resultat
                    self.stdout.write(f"  {'processed' if appliquer else 'to process'}: {fichier.name}")
                    if appliquer:
                        fichier.save(images.nouveau_nom(fichier.name, extension), ContentFile(contenu), save=False)
                        modele.objects.filter(pk=objet.pk).update(**{champ.name: fichier.name})

        verbe = "processed" if appliquer else "to process"
        self.stdout.write(self.style.SUCCESS(
            f"{traitees} picture(s) {verbe}, {deja_bonnes} already fine, {manquantes} missing file(s)."
        ))
        if not appliquer and traitees:
            self.stdout.write("Run again with --appliquer to process them.")
