"""
Turns the texts typed in the admin into well-spaced HTML.

Simple formatting rules (shown in the admin):
    empty line          → new paragraph
    ## Heading          → sub-heading
    - item  /  * item   → bulleted list
    **bold**  *italic*

Old texts typed on a single line (before the update, the admin only had
one-line fields) are split automatically into paragraphs of a few
sentences, so that long pages are easy to read.
"""
import re

from django.utils.html import escape

LONGUEUR_PARAGRAPHE = 420      # target length of an automatic paragraph
SEUIL_DECOUPAGE = 600          # a block longer than this, with no line break, is split

RE_PHRASE = re.compile(r"(?<=[.!?…»”\"])\s+(?=[A-ZÀ-ÖØ-Ý0-9«“\"(])")
RE_GRAS = re.compile(r"\*\*(.+?)\*\*")
RE_ITALIQUE = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])")
RE_LISTE = re.compile(r"^\s*[-*•]\s+")


def _en_ligne(texte):
    """Escapes the text, then applies **bold** and *italic*."""
    texte = escape(texte)
    texte = RE_GRAS.sub(r"<strong>\1</strong>", texte)
    texte = RE_ITALIQUE.sub(r"<em>\1</em>", texte)
    return texte


def decouper_en_phrases(bloc):
    """Groups the sentences of a long block into paragraphs of ~LONGUEUR_PARAGRAPHE characters."""
    phrases = [p.strip() for p in RE_PHRASE.split(bloc) if p.strip()]
    paragraphes, courant = [], ""
    for phrase in phrases:
        if courant and len(courant) + len(phrase) > LONGUEUR_PARAGRAPHE:
            paragraphes.append(courant)
            courant = phrase
        else:
            courant = f"{courant} {phrase}".strip()
    if courant:
        paragraphes.append(courant)
    return paragraphes


def mettre_en_forme(texte):
    """Returns the HTML of a text typed in the admin (safe: everything is escaped)."""
    if not texte:
        return ""
    texte = str(texte).replace("\r\n", "\n").replace("\r", "\n").strip()

    # Old one-line texts: automatic paragraphs
    if "\n" not in texte and len(texte) > SEUIL_DECOUPAGE:
        return "".join(f"<p>{_en_ligne(p)}</p>" for p in decouper_en_phrases(texte))

    html, liste, paragraphe = [], [], []

    def fermer_paragraphe():
        if paragraphe:
            html.append("<p>" + "<br>".join(_en_ligne(l) for l in paragraphe) + "</p>")
            paragraphe.clear()

    def fermer_liste():
        if liste:
            html.append("<ul>" + "".join(f"<li>{_en_ligne(l)}</li>" for l in liste) + "</ul>")
            liste.clear()

    lignes = texte.split("\n")
    # A text where every line is a paragraph (typed with a single Enter):
    # each line becomes its own paragraph so that the page stays airy.
    une_ligne_par_paragraphe = "\n\n" not in texte

    for ligne in lignes:
        propre = ligne.strip()
        if not propre:
            fermer_paragraphe()
            fermer_liste()
            continue
        if propre.startswith("## ") or propre.startswith("# "):
            fermer_paragraphe()
            fermer_liste()
            html.append(f"<h3>{_en_ligne(propre.lstrip('#').strip())}</h3>")
            continue
        if RE_LISTE.match(propre):
            fermer_paragraphe()
            liste.append(RE_LISTE.sub("", propre))
            continue
        fermer_liste()
        if une_ligne_par_paragraphe:
            if len(propre) > SEUIL_DECOUPAGE:
                html.extend(f"<p>{_en_ligne(p)}</p>" for p in decouper_en_phrases(propre))
            else:
                html.append(f"<p>{_en_ligne(propre)}</p>")
        else:
            paragraphe.append(propre)

    fermer_paragraphe()
    fermer_liste()
    return "".join(html)


def resume(texte, mots=25):
    """Plain-text summary (formatting marks removed) for cards and descriptions."""
    if not texte:
        return ""
    propre = re.sub(r"[#*•]+", " ", str(texte))
    propre = re.sub(r"\s+", " ", propre).strip()
    morceaux = propre.split(" ")
    return propre if len(morceaux) <= mots else " ".join(morceaux[:mots]) + "…"
