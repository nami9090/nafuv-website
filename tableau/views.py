import csv
from datetime import date
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, ImageField, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import Truncator
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from mainApp.models import ContactMessage, Donation, SiteSettings, serviceDetail

from .forms import ConnexionForm, formulaire_pour, sous_formulaires_pour
from .sections import LANGUES, REGLAGES, SECTIONS, etat_traductions

PAR_PAGE = 20


# ===========================================================================
# Access
# ===========================================================================
def equipe_requise(vue):
    """Only active staff accounts may use the dashboard."""
    @wraps(vue)
    def enveloppe(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('tableau:connexion')}?next={request.get_full_path()}")
        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return enveloppe


def connexion(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("tableau:accueil")
    form = ConnexionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        identifiant = form.cleaned_data["identifiant"].strip()
        Utilisateur = get_user_model()
        compte = Utilisateur.objects.filter(email__iexact=identifiant).first() if "@" in identifiant else None
        utilisateur = authenticate(
            request, username=compte.get_username() if compte else identifiant, password=form.cleaned_data["mot_de_passe"],
        )
        if utilisateur is not None and utilisateur.is_staff:
            login(request, utilisateur)
            suivant = request.GET.get("next", "")
            if url_has_allowed_host_and_scheme(suivant, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(suivant)
            return redirect("tableau:accueil")
        messages.error(request, _("Incorrect username or password, or this account has no access to the dashboard."))
    return render(request, "tableau/connexion.html", {"form": form})


@require_POST
def deconnexion(request):
    logout(request)
    messages.success(request, _("You are logged out."))
    return redirect("tableau:connexion")


def _contexte(request, **valeurs):
    valeurs.setdefault("sections", SECTIONS.values())
    valeurs["nb_messages"] = ContactMessage.objects.filter(traite=False).count()
    return valeurs


def _url_image(champ):
    try:
        return champ.url if champ else ""
    except ValueError:
        return ""


# ===========================================================================
# Overview
# ===========================================================================
@equipe_requise
def accueil(request):
    maintenant = timezone.localtime()
    payes = Donation.objects.filter(statut=Donation.PAYE)
    totaux = payes.aggregate(
        total=Sum("montant"), nombre=Count("id"),
        annee=Sum("montant", filter=Q(paye_le__year=maintenant.year)),
        mois=Sum("montant", filter=Q(paye_le__year=maintenant.year, paye_le__month=maintenant.month)),
    )

    # Donations of the last 12 months (bar chart)
    mois = []
    annee, m = maintenant.year, maintenant.month
    for _i in range(12):
        mois.append(date(annee, m, 1))
        m -= 1
        if m == 0:
            annee, m = annee - 1, 12
    mois.reverse()
    par_mois = {
        (l["mois"].year, l["mois"].month): l["total"]
        for l in payes.filter(paye_le__date__gte=mois[0]).annotate(mois=TruncMonth("paye_le"))
        .values("mois").annotate(total=Sum("montant"))
    }
    valeurs = [float(par_mois.get((d.year, d.month), 0) or 0) for d in mois]
    plafond = max(valeurs) or 1
    graphique = [
        {"mois": d, "montant": v, "hauteur": max(round(100 * v / plafond), 2 if v else 0)}
        for d, v in zip(mois, valeurs)
    ]

    # Content and translations
    contenus, traductions = [], []
    for s in SECTIONS.values():
        objets = list(s.modele.objects.all())
        contenus.append({"section": s, "nombre": len(objets)})
        if s.traduits and objets:
            etats = [etat_traductions(s, o) for o in objets]
            traductions.append({
                "section": s, "total": len(objets),
                "fr": round(100 * sum(e["fr"] for e in etats) / len(etats)),
                "sw": round(100 * sum(e["sw"] for e in etats) / len(etats)),
            })

    console = "console" in settings.EMAIL_BACKEND or "locmem" in settings.EMAIL_BACKEND
    stripe_ok = bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET)
    etat = [
        (_("Online donations"), stripe_ok,
         (_("Test mode: no real money is collected") if settings.STRIPE_SECRET_KEY.startswith("sk_test_") else _("Active"))
         if stripe_ok else _("Stripe keys missing in the .env file")),
        (_("E-mails"), not console, _("Sent for real") if not console else _("Not sent: configure SMTP in the .env file")),
        (_("Production mode"), not settings.DEBUG, _("DEBUG off") if not settings.DEBUG else _("DEBUG is on")),
    ]

    return render(request, "tableau/accueil.html", _contexte(
        request,
        dons={"total": totaux["total"] or 0, "nombre": totaux["nombre"], "annee": totaux["annee"] or 0,
              "mois": totaux["mois"] or 0, "attente": Donation.objects.filter(statut=Donation.EN_ATTENTE).count(),
              "derniers": payes.order_by("-paye_le")[:5]},
        graphique=graphique, contenus=contenus, traductions=traductions, etat=etat,
        derniers_messages=ContactMessage.objects.all()[:5],
        nb_souverains=serviceDetail.objects.count(),
    ))


# ===========================================================================
# Content sections (generic)
# ===========================================================================
def _section(code):
    section = SECTIONS.get(code)
    if section is None:
        raise Http404
    return section


@equipe_requise
def liste(request, code):
    section = _section(code)
    objets = section.modele.objects.all()

    q = request.GET.get("q", "").strip()
    if q and section.recherche:
        filtre = Q()
        for champ in section.recherche:
            filtre |= Q(**{f"{champ}__icontains": q})
        objets = objets.filter(filtre)

    filtre_actif = request.GET.get("filtre", "")
    for code_filtre, _libelle, conditions in section.filtres:
        if code_filtre == filtre_actif:
            objets = objets.filter(**conditions)

    manque = request.GET.get("manque", "")
    lignes = []
    for objet in objets:
        etat = etat_traductions(section, objet)
        if manque in ("fr", "sw") and etat.get(manque, True):
            continue
        lignes.append({
            "objet": objet,
            "titre": section.libelle_objet(objet),
            "sous_titre": Truncator(str(getattr(objet, section.sous_titre_champ, "") or "")).chars(70) if section.sous_titre_champ else "",
            "image": _url_image(getattr(objet, section.image, None)) if section.image else "",
            "traductions": etat,
            "ordre": getattr(objet, "order", None),
            "nb_sous": getattr(objet, section.sous_elements.modele._meta.get_field(section.sous_elements.cle).remote_field.related_name).count()
            if section.sous_elements else None,
        })

    page = Paginator(lignes, PAR_PAGE).get_page(request.GET.get("page"))
    return render(request, "tableau/liste.html", _contexte(
        request, section=section, page=page, q=q, filtre_actif=filtre_actif, manque=manque, total=len(lignes),
    ))


def _groupes(section, form):
    """Splits a form into: language tabs, picture, general fields, options."""
    modele = section.modele
    images, options, generaux = [], [], []
    for nom in section.champs:
        if nom in section.traduits:
            continue
        champ_modele = modele._meta.get_field(nom)
        if isinstance(champ_modele, ImageField):
            images.append(form[nom])
        elif champ_modele.get_internal_type() == "BooleanField" or nom == "order":
            options.append(form[nom])
        else:
            generaux.append(form[nom])
    langues = []
    for code, nom in LANGUES:
        champs = [form[c if code == "en" else f"{c}_{code}"] for c in section.traduits]
        if champs:
            langues.append({"code": code, "nom": nom, "champs": champs})
    return {"langues": langues, "images": images, "options": options, "generaux": generaux}


def _ajouts_multiples(request, section, objet):
    se = section.sous_elements
    if not se or not se.ajout_multiple:
        return 0
    n = 0
    for fichier in request.FILES.getlist("ajout_photos"):
        valeurs = {se.cle: objet, se.image: fichier}
        if se.titre_champ:
            nom = fichier.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
            valeurs[se.titre_champ] = (nom[:1].upper() + nom[1:])[:100] or "Photo"
        se.modele.objects.create(**valeurs)
        n += 1
    return n


@equipe_requise
def edition(request, code, pk=None):
    section = _section(code)
    objet = get_object_or_404(section.modele, pk=pk) if pk else None
    Formulaire = formulaire_pour(section)
    SousFormulaires = sous_formulaires_pour(section)

    donnees = (request.POST, request.FILES) if request.method == "POST" else (None, None)
    form = Formulaire(*donnees, instance=objet)
    sous = SousFormulaires(*donnees, instance=objet or section.modele(), prefix="sous") if SousFormulaires else None

    if request.method == "POST" and form.is_valid() and (sous is None or sous.is_valid()):
        with transaction.atomic():
            objet = form.save()
            if sous is not None:
                sous.instance = objet
                sous.save()
            ajoutees = _ajouts_multiples(request, section, objet)
        texte = _("Saved.")
        if ajoutees:
            texte += " " + _("%(n)s picture(s) added.") % {"n": ajoutees}
        messages.success(request, texte)
        if "enregistrer_continuer" in request.POST:
            return redirect("tableau:modifier", code=code, pk=objet.pk)
        return redirect("tableau:liste", code=code)
    if request.method == "POST":
        messages.error(request, _("Please correct the errors shown below."))

    lignes_sous, modele_sous = [], None
    if sous is not None:
        se = section.sous_elements
        vide = sous.empty_form
        modele_sous = {"caches": vide.hidden_fields(), "image": vide[se.image],
                       "autres": [vide[c] for c in se.champs if c != se.image]}
        for f in sous.forms:
            image = _url_image(getattr(f.instance, se.image, None)) if f.instance.pk else ""
            lignes_sous.append({"form": f, "image": image, "champ_image": f[se.image],
                                "autres": [f[c] for c in se.champs if c != se.image]})

    return render(request, "tableau/formulaire.html", _contexte(
        request, section=section, objet=objet, form=form, sous=sous, lignes_sous=lignes_sous, modele_sous=modele_sous,
        groupes=_groupes(section, form),
        apercu=_url_image(getattr(objet, section.image, None)) if objet and section.image else "",
        voir_sur_site=objet.get_absolute_url() if objet and hasattr(objet, "get_absolute_url") else "",
    ))


@equipe_requise
def supprimer(request, code, pk):
    section = _section(code)
    objet = get_object_or_404(section.modele, pk=pk)
    if request.method == "POST":
        libelle = section.libelle_objet(objet)
        objet.delete()
        messages.success(request, _("“%(nom)s” has been deleted.") % {"nom": libelle})
        return redirect("tableau:liste", code=code)
    return render(request, "tableau/supprimer.html", _contexte(request, section=section, objet=objet,
                                                               libelle=section.libelle_objet(objet)))


# ===========================================================================
# Site settings
# ===========================================================================
@equipe_requise
def reglages(request):
    objet = SiteSettings.charger()
    Formulaire = formulaire_pour(REGLAGES)
    form = Formulaire(request.POST or None, instance=objet)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, _("Site settings saved."))
            return redirect("tableau:reglages")
        messages.error(request, _("Please correct the errors shown below."))
    return render(request, "tableau/formulaire.html", _contexte(
        request, section=REGLAGES, objet=objet, form=form, groupes=_groupes(REGLAGES, form), reglages=True,
    ))


# ===========================================================================
# Donations
# ===========================================================================
def _dons_filtres(request):
    dons = Donation.objects.all()
    statut = request.GET.get("statut", "")
    if statut in dict(Donation.STATUTS):
        dons = dons.filter(statut=statut)
    q = request.GET.get("q", "").strip()
    if q:
        dons = dons.filter(Q(nom__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q))
    return dons, statut, q


@equipe_requise
def dons(request):
    liste_dons, statut, q = _dons_filtres(request)
    if request.GET.get("export") == "csv":
        reponse = HttpResponse(content_type="text/csv; charset=utf-8")
        reponse["Content-Disposition"] = f'attachment; filename="nafuv-donations-{date.today():%Y-%m-%d}.csv"'
        reponse.write("﻿")  # opens correctly in Excel
        ecrivain = csv.writer(reponse)
        ecrivain.writerow(["Date", "Paid on", "Name", "E-mail", "Amount", "Currency", "Status", "Anonymous",
                           "Message", "Stripe session", "Stripe payment"])
        for d in liste_dons:
            ecrivain.writerow([
                timezone.localtime(d.cree_le).strftime("%Y-%m-%d %H:%M"),
                timezone.localtime(d.paye_le).strftime("%Y-%m-%d %H:%M") if d.paye_le else "",
                d.nom, d.email, d.montant, d.devise.upper(), d.get_statut_display(), "yes" if d.anonyme else "no",
                d.message, d.stripe_session, d.stripe_paiement,
            ])
        return reponse
    total = liste_dons.filter(statut=Donation.PAYE).aggregate(t=Sum("montant"))["t"] or 0
    page = Paginator(liste_dons, PAR_PAGE).get_page(request.GET.get("page"))
    return render(request, "tableau/dons.html", _contexte(
        request, page=page, statut=statut, q=q, total=total, statuts=Donation.STATUTS,
    ))


# ===========================================================================
# Messages
# ===========================================================================
@equipe_requise
def boite(request):
    liste_messages = ContactMessage.objects.all()
    vue = request.GET.get("vue", "")
    if vue == "a_traiter":
        liste_messages = liste_messages.filter(traite=False)
    elif vue == "traites":
        liste_messages = liste_messages.filter(traite=True)
    q = request.GET.get("q", "").strip()
    if q:
        liste_messages = liste_messages.filter(
            Q(nom__icontains=q) | Q(email__icontains=q) | Q(sujet__icontains=q) | Q(message__icontains=q)
        )
    page = Paginator(liste_messages, PAR_PAGE).get_page(request.GET.get("page"))
    return render(request, "tableau/messages.html", _contexte(request, page=page, vue=vue, q=q))


@equipe_requise
def message(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        msg.traite = not msg.traite
        msg.save(update_fields=["traite"])
        messages.success(request, _("Marked as handled.") if msg.traite else _("Marked as to be handled."))
        return redirect("tableau:message", pk=msg.pk)
    return render(request, "tableau/message.html", _contexte(request, msg=msg))


# ===========================================================================
# Search and account
# ===========================================================================
@equipe_requise
def recherche(request):
    q = request.GET.get("q", "").strip()
    resultats = []
    if len(q) >= 2:
        for s in SECTIONS.values():
            filtre = Q()
            for champ in s.recherche:
                filtre |= Q(**{f"{champ}__icontains": q})
            for objet in s.modele.objects.filter(filtre)[:10]:
                resultats.append({"section": s, "titre": s.libelle_objet(objet),
                                  "url": reverse("tableau:modifier", args=[s.code, objet.pk]),
                                  "image": _url_image(getattr(objet, s.image, None)) if s.image else ""})
        for d in Donation.objects.filter(Q(nom__icontains=q) | Q(email__icontains=q))[:10]:
            resultats.append({"section": None, "type": _("Donation"), "titre": f"{d.nom} · ${d.montant}",
                              "url": f"{reverse('tableau:dons')}?q={d.email}", "image": ""})
        for m in ContactMessage.objects.filter(Q(nom__icontains=q) | Q(sujet__icontains=q) | Q(email__icontains=q))[:10]:
            resultats.append({"section": None, "type": _("Message"), "titre": f"{m.sujet} · {m.nom}",
                              "url": reverse("tableau:message", args=[m.pk]), "image": ""})
    return render(request, "tableau/recherche.html", _contexte(request, q=q, resultats=resultats))


@equipe_requise
def compte(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    for champ in form.fields.values():
        champ.widget.attrs["class"] = "saisie"
    if request.method == "POST" and form.is_valid():
        utilisateur = form.save()
        update_session_auth_hash(request, utilisateur)
        messages.success(request, _("Your password has been changed."))
        return redirect("tableau:compte")
    return render(request, "tableau/compte.html", _contexte(request, form=form))
