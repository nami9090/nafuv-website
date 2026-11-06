from django import forms
from django.forms import inlineformset_factory, modelform_factory
from django.utils.translation import gettext_lazy as _

from .sections import AIDES, LIBELLES


def _habiller(formulaire):
    """Labels, help texts and CSS classes for every field of a generated form."""
    for nom, champ in formulaire.fields.items():
        base = nom.rsplit("_", 1)[0] if nom.endswith(("_fr", "_sw")) else nom
        if base in LIBELLES:
            champ.label = LIBELLES[base]
        if base in AIDES and not nom.endswith(("_fr", "_sw")):
            champ.help_text = AIDES[base]
        widget = champ.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "interrupteur")
        elif isinstance(widget, (forms.ClearableFileInput, forms.FileInput)):
            widget.attrs.update({"accept": "image/*", "class": "fichier", "data-apercu": nom})
        elif isinstance(widget, forms.Textarea):
            widget.attrs.update({"class": "saisie", "rows": 8 if base in ("details", "texte_background") else 5})
        elif isinstance(widget, forms.DateInput):
            champ.widget = forms.DateInput(attrs={"type": "date", "class": "saisie"}, format="%Y-%m-%d")
        else:
            widget.attrs.setdefault("class", "saisie")


class FormulaireBase(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _habiller(self)


def formulaire_pour(section):
    return modelform_factory(section.modele, form=FormulaireBase, fields=section.champs_formulaire)


def sous_formulaires_pour(section):
    se = section.sous_elements
    if se is None:
        return None
    return inlineformset_factory(
        section.modele, se.modele, form=FormulaireBase, fk_name=se.cle, fields=se.champs,
        extra=0 if se.ajout_multiple else 1, can_delete=True,
    )


class ConnexionForm(forms.Form):
    identifiant = forms.CharField(label=_("Username or e-mail"), widget=forms.TextInput(attrs={"class": "saisie", "autofocus": True, "autocomplete": "username"}))
    mot_de_passe = forms.CharField(label=_("Password"), widget=forms.PasswordInput(attrs={"class": "saisie", "autocomplete": "current-password"}))
