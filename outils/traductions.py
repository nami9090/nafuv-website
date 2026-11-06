"""
French and Swahili translations of the interface, without GNU gettext (handy on Windows).

    python outils/traductions.py              # writes locale/fr|sw/LC_MESSAGES/django.po and compiles django.mo
    python outils/traductions.py --manquants  # lists the texts not translated yet

1. Extracts the texts from the templates ({% translate %}, {% blocktranslate %})
   and from Python code (_(), gettext(), gettext_lazy()).
2. Takes the translations from outils/textes_traduits.py.
3. Writes django.po (editable with Poedit) and compiles django.mo.

Developed by Nami Industries.
"""
import ast
import re
import struct
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from textes_traduits import TEXTES  # noqa: E402

LANGUES = {"fr": 0, "sw": 1}
EXCLUS = {"venv", ".venv", "node_modules", "productionfiles", "media", "locale", "outils", "migrations"}
FONCTIONS = {"_", "gettext", "gettext_lazy", "ngettext", "ngettext_lazy"}

RE_TRANS = re.compile(r"""\{%\s*(?:translate|trans)\s+(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')(?:\s+(?:as\s+\w+|noop))*\s*%\}""")
RE_BLOC = re.compile(r"\{%\s*blocktranslate\b(.*?)%\}(.*?)\{%\s*endblocktranslate\s*%\}", re.S)
RE_VAR = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def fichiers(motif):
    for f in sorted(RACINE.rglob(motif)):
        if not EXCLUS.intersection(f.relative_to(RACINE).parts):
            yield f


def extraire():
    """Returns {msgid: None} or {(singular, plural): None}, in order of appearance."""
    textes = {}
    for f in fichiers("*.html"):
        contenu = f.read_text(encoding="utf-8")
        for m in RE_TRANS.finditer(contenu):
            textes.setdefault((m.group(1) or m.group(2)).replace('\\"', '"').replace("\\'", "'"), None)
        for m in RE_BLOC.finditer(contenu):
            options, corps = m.group(1), m.group(2)
            corps = RE_VAR.sub(lambda v: f"%({v.group(1)})s", corps)
            if "trimmed" in options:
                corps = " ".join(l.strip() for l in corps.strip().splitlines() if l.strip())
            if "{% plural %}" in corps:
                singulier, pluriel = corps.split("{% plural %}")
                textes.setdefault((singulier, pluriel), None)
            else:
                textes.setdefault(corps, None)
    for f in fichiers("*.py"):
        try:
            arbre = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Call) and getattr(noeud.func, "id", None) in FONCTIONS and noeud.args:
                arg = noeud.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    textes.setdefault(arg.value, None)
    return textes


def echapper(texte):
    return texte.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def ecrire_po(langue, entrees):
    pluriel = "nplurals=2; plural=(n > 1);" if langue == "fr" else "nplurals=2; plural=(n != 1);"
    lignes = [
        'msgid ""', 'msgstr ""',
        f'"Language: {langue}\\n"', '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"', '"Content-Transfer-Encoding: 8bit\\n"',
        f'"Plural-Forms: {pluriel}\\n"', "",
    ]
    for cle, valeur in entrees:
        if isinstance(cle, tuple):
            lignes += [f'msgid "{echapper(cle[0])}"', f'msgid_plural "{echapper(cle[1])}"',
                       f'msgstr[0] "{echapper(valeur[0])}"', f'msgstr[1] "{echapper(valeur[1])}"', ""]
        else:
            lignes += [f'msgid "{echapper(cle)}"', f'msgstr "{echapper(valeur)}"', ""]
    chemin = RACINE / "locale" / langue / "LC_MESSAGES" / "django.po"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text("\n".join(lignes), encoding="utf-8")
    return chemin, pluriel


def ecrire_mo(chemin_po, entrees, pluriel, langue):
    """Compiles a .mo file (GNU gettext format)."""
    catalogue = {"": f"Language: {langue}\nContent-Type: text/plain; charset=UTF-8\nPlural-Forms: {pluriel}\n"}
    for cle, valeur in entrees:
        if isinstance(cle, tuple):
            catalogue["\x00".join(cle)] = "\x00".join(valeur)
        else:
            catalogue[cle] = valeur
    cles = sorted(catalogue)
    ids = b"".join(k.encode() + b"\x00" for k in cles)
    strs = b"".join(catalogue[k].encode() + b"\x00" for k in cles)
    debut = 7 * 4 + 16 * len(cles)
    tables_ids, tables_strs, pos = [], [], 0
    for k in cles:
        tables_ids.append((len(k.encode()), debut + pos)); pos += len(k.encode()) + 1
    pos_strs = debut + len(ids)
    pos = 0
    for k in cles:
        tables_strs.append((len(catalogue[k].encode()), pos_strs + pos)); pos += len(catalogue[k].encode()) + 1
    entete = struct.pack("Iiiiiii", 0x950412DE, 0, len(cles), 7 * 4, 7 * 4 + 8 * len(cles), 0, 0)
    corps = b"".join(struct.pack("ii", *t) for t in tables_ids) + b"".join(struct.pack("ii", *t) for t in tables_strs)
    chemin_po.with_suffix(".mo").write_bytes(entete + corps + ids + strs)


def main():
    textes = extraire()
    manquants = [c for c in textes if c not in TEXTES]
    if "--manquants" in sys.argv:
        for c in manquants:
            print(repr(c))
        print(f"\n{len(manquants)} text(s) not translated out of {len(textes)}.")
        return
    for langue, i in LANGUES.items():
        entrees = []
        for cle in textes:
            if cle in TEXTES:
                valeur = TEXTES[cle][i]
                entrees.append((cle, valeur))
        chemin, pluriel = ecrire_po(langue, entrees)
        ecrire_mo(chemin, entrees, pluriel, langue)
        print(f"{langue}: {len(entrees)} translated, written {chemin.relative_to(RACINE)} and .mo")
    if manquants:
        print(f"{len(manquants)} text(s) without translation (shown in English): python outils/traductions.py --manquants")


if __name__ == "__main__":
    main()
