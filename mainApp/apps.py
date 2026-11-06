from django.apps import AppConfig


class MainappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mainApp"
    verbose_name = "NAFUV museum"

    def ready(self):
        from django.db.models.signals import pre_save

        from . import images

        # Every uploaded picture is turned the right way up, resized and compressed
        for modele in self.get_models():
            if images.champs_images(modele):
                pre_save.connect(images.avant_enregistrement, sender=modele, dispatch_uid=f"images-{modele.__name__}")
