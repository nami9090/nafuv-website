from decimal import Decimal, InvalidOperation

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # Hidden field: humans leave it empty, spam robots fill it
    site_web = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = ContactMessage
        fields = ["nom", "email", "sujet", "message"]
        labels = {
            "nom": _("Your name"),
            "email": _("Your e-mail"),
            "sujet": _("Subject"),
            "message": _("Message"),
        }
        widgets = {"message": forms.Textarea(attrs={"rows": 6})}

    def est_robot(self):
        return bool(self.cleaned_data.get("site_web"))


class DonationForm(forms.Form):
    montant = forms.CharField(label=_("Amount (USD)"))
    nom = forms.CharField(label=_("Full name"), max_length=120)
    email = forms.EmailField(label=_("E-mail (for your receipt)"))
    message = forms.CharField(label=_("Message (optional)"), required=False, widget=forms.Textarea(attrs={"rows": 3}))
    anonyme = forms.BooleanField(label=_("Keep my donation anonymous"), required=False)

    def clean_montant(self):
        brut = (self.cleaned_data.get("montant") or "").replace("$", "").replace(",", ".").strip()
        try:
            montant = Decimal(brut).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            raise forms.ValidationError(_("Please enter a valid amount."))
        if montant < settings.DONATION_MIN:
            raise forms.ValidationError(_("The minimum donation is $%(min)s.") % {"min": settings.DONATION_MIN})
        if montant > settings.DONATION_MAX:
            raise forms.ValidationError(
                _("For donations above $%(max)s, please contact us directly.") % {"max": settings.DONATION_MAX}
            )
        return montant
