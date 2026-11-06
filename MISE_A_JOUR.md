# NAFUV : nouvelle version

Musée virtuel Fuliiru Vira : refonte complète, avec **tout le contenu existant conservé**.

## Ce qui a changé

| Domaine | Avant | Maintenant |
|---|---|---|
| Sécurité | Mots de passe et clé secrète dans `settings.py`, `DEBUG=True` | Tout passe par un fichier `.env` non versionné ; HTTPS et cookies sécurisés en production |
| Contact | Le formulaire envoyait vers un fichier PHP absent | Message enregistré dans l'admin, envoyé par e-mail, avec un filtre anti-spam |
| Dons | Boutons décoratifs, aucun paiement possible | Paiement par carte avec **Stripe Checkout** : montants prédéfinis ou libres, e-mail de remerciement, suivi dans l'admin |
| Langues | Anglais seulement | **Anglais, français et swahili** : interface traduite et contenus saisissables dans les 3 langues |
| Design | Modèle immobilier « EstateAgency » | Identité de musée : papier ivoire, encre terre, ocre, motif textile, visionneuse d'images, lignée royale en frise |
| Contenu fixe | Textes « Background, Mission, Activities », adresse, téléphone écrits en dur | Tout se modifie dans l'admin (**Site settings**), déjà traduit en français et en swahili |
| Erreurs | Erreur 500 pour une adresse inconnue | Vraie page 404, page 500 propre |
| Référencement | Aucune description | Descriptions, Open Graph, `hreflang`, `sitemap.xml`, `robots.txt` |
| Accessibilité | Images sans texte alternatif, menu non accessible | Textes alternatifs, navigation au clavier, lien « aller au contenu », animations réduites si l'utilisateur le demande |
| Qualité | 0 test | 23 tests automatiques |

Les anciennes adresses continuent de fonctionner (`/about`, `/services`, `/gallery_single/3/`…). L'ancienne page `/dialog` redirige vers `/donate`.

---

## 1. Installer en local

```bash
pip install -r requirements.txt
copy .env.example .env          # Windows  (Linux/Mac : cp .env.example .env)
```

Ouvre `.env` et remplis-le. Il faut au minimum `SECRET_KEY`, et pour ta base PostgreSQL locale `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

> **Important :** les anciens mots de passe (base PostgreSQL et base MySQL du cPanel) étaient écrits dans le code. Si ce code a été partagé ou mis sur GitHub, **change ces mots de passe**.

## 2. Mettre à jour la base (sans perte de données)

```bash
python manage.py makemigrations mainApp
python manage.py migrate
```

`makemigrations` crée la migration `0017` : ajout des champs français et swahili, de l'ordre d'affichage, et des nouvelles tables (dons, messages, réglages du site). **Aucune table n'est supprimée ou renommée.** Si la commande pose une question, envoie-la-moi avant de répondre.

**Avant de faire `migrate` en production, fais une sauvegarde de la base.**

## 3. Tester

```bash
python manage.py test mainApp
python manage.py runserver
```

- http://127.0.0.1:8000/ (anglais), `/fr/` (français), `/sw/` (swahili)
- http://127.0.0.1:8000/admin/ → **Site settings** : adresse, réseaux sociaux, textes de la page À propos et de la page Dons
- Pour traduire un contenu (diapo, royaume, galerie…), ouvre-le dans l'admin : les groupes **French version** et **Swahili version** sont repliés en bas de la fiche. Un champ laissé vide affiche le texte anglais.

## 4. Activer les dons Stripe

1. L'association crée un compte sur https://stripe.com (il faut celui de l'association, pas le tien).
2. Dans le tableau de bord Stripe : **Developers → API keys**. Copie la clé secrète (`sk_test_...` pour les essais) dans `.env`, ligne `STRIPE_SECRET_KEY`.
3. **Developers → Webhooks → Add endpoint** :
   - URL : `https://nafuv.org/donate/webhook/`
   - Événements : `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`
   - Copie le « Signing secret » (`whsec_...`) dans `STRIPE_WEBHOOK_SECRET`.
4. Fais un essai avec la carte de test `4242 4242 4242 4242` (n'importe quelle date future et n'importe quel code).
5. Quand tout marche, remplace les clés de test par les clés réelles (`sk_live_...`) et le secret du webhook réel.

Dans **Settings → Emails** de Stripe, active « Successful payments » : Stripe envoie alors lui-même le reçu officiel au donateur.

Tant que `STRIPE_SECRET_KEY` est vide, la page Dons affiche simplement l'e-mail et le téléphone de l'association.

## 5. E-mails réels

Dans `.env`, remplace le mode console par la boîte `info@nafuv.org` de l'hébergeur (exemple dans `.env.example`). Sans ça, les messages du formulaire de contact restent visibles dans l'admin (**Contact messages**), mais ils ne partent pas par e-mail.

## 6. Mettre en production

**Sur le cPanel actuel (MySQL)**, dans le `.env` du serveur :
```
DEBUG=False
DB_ENGINE=mysql
DB_NAME=...  DB_USER=...  DB_PASSWORD=...
STATIC_ROOT=/home/UTILISATEUR/public_html/static/
MEDIA_ROOT=/home/UTILISATEUR/public_html/media/
SITE_URL=https://nafuv.org
```
Puis `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py collectstatic`, et redémarrer l'application Python dans cPanel.

Le fichier `passenger_wsgi.py` du cPanel ne change pas. Son contenu avait été collé par erreur à la fin de `views.py` : je l'ai retiré de là.

**Sur ton VPS** (comme ATLAS) : même méthode qu'ATLAS (Gunicorn, Nginx, certbot), avec `DB_ENGINE=postgresql` et `USE_X_FORWARDED_PROTO=True`.

## 7. Modifier une traduction de l'interface

Les textes fixes (menus, boutons) se trouvent dans `outils/textes_traduits.py`. Corrige le texte, puis lance :
```bash
python outils/traductions.py
```
Les fichiers `locale/fr` et `locale/sw` sont alors régénérés. **Fais relire le swahili par un membre de la communauté.**

---

## Fichiers

- Modifiés : `nafuvWebsite/settings.py`, `urls.py`, `__init__.py`, `mainApp/models.py`, `views.py`, `urls.py`, `admin.py`, `tests.py`, tous les gabarits, `requirements.txt`
- Nouveaux : `mainApp/forms.py`, `stripe_api.py`, `context_processors.py`, `sitemaps.py`, `templatetags/nafuv_tags.py`, `static/nafuv/` (CSS et JS), `templates/donate*.html`, `404.html`, `500.html`, `robots.txt`, `locale/`, `outils/`, `.env.example`, `.gitignore`
- Supprimé : `templates/dialog.html` (remplacé par `donate.html`)
- Le dossier `static/assets/` est conservé (logo, favicon) ; les fichiers Bootstrap et les scripts du modèle d'origine ne sont plus chargés.

Développé par Nami Industries.

---

# Deuxième mise à jour : texte, images, tableau de bord

## Texte mieux aéré
- Les anciens textes saisis sur une seule ligne sont **découpés automatiquement en paragraphes** de quelques phrases.
- La page détail d'un royaume ou d'un programme est construite comme un article : colonne de lecture, lettrine, et image affichée en entier sur le côté avec la fiche de la lignée.
- Mise en forme simple dans l'admin (l'aide s'affiche au-dessus des champs) :
  - une **ligne vide** entre deux paragraphes
  - `## Intertitre`
  - `- élément` pour une liste
  - `**gras**` et `*italique*`

## Images
- Chaque image envoyée dans l'admin est **redressée** (les photos de téléphone qui apparaissaient couchées), **redimensionnée** (2000 px maximum) et **compressée**. Les pages chargent beaucoup plus vite.
- Les visages ne sont plus coupés : cadrage centré vers le haut pour l'équipe et les souverains, et image entière sur la page détail.
- Une image absente ne casse plus la page : un cadre neutre s'affiche à la place.
- **Pour les images déjà en ligne** (fais d'abord une sauvegarde du dossier `media`) :
  ```bash
  python manage.py optimiser_images              # liste ce qui va changer et les fichiers manquants
  python manage.py optimiser_images --appliquer  # traite les images
  ```
  La commande signale aussi les **fichiers manquants** : des images enregistrées dans la base mais absentes du dossier `media`. C'est souvent la vraie cause des images qui n'apparaissent pas en ligne.
- **Images invisibles en production avec `DEBUG=False` ?** Si l'hébergeur ne sert pas le dossier `media`, mets `SERVE_MEDIA=True` dans `.env`.

## Tableau de bord d'administration (`/admin/`)
- **Chiffres** : dons de l'année, du mois et au total ; messages à traiter ; paiements commencés mais pas terminés.
- **Actions rapides** : ajouter une diapo, un royaume ou un programme, une galerie, un membre de l'équipe ; modifier les réglages du site.
- **Traductions à compléter** : pour chaque type de contenu, le nombre d'éléments sans français ou sans swahili, avec un lien vers la liste filtrée.
- **État du site** : Stripe configuré ou non (mode test signalé), e-mails réellement envoyés ou non, mode production.
- **Derniers dons et derniers messages**, et accès à toutes les sections.
- Thème de l'admin aux couleurs NAFUV.

---

# Troisième mise à jour : le tableau de bord NAFUV (`/dashboard/`)

Une application de gestion à part entière, séparée de l'admin Django. L'admin reste disponible en secours, pour les superutilisateurs, via le lien « Advanced admin ».

## Accès
- Adresse : **`/dashboard/`** (en local : http://127.0.0.1:8001/dashboard/)
- Connexion avec l'identifiant **ou** l'e-mail.
- Réservé aux comptes **staff**. Pour donner l'accès à quelqu'un :
  ```bash
  python manage.py createsuperuser        # un administrateur complet
  ```
  ou, dans l'admin avancée → Users, coche **Staff status** sur son compte.
- L'interface est en anglais ou en français selon la langue du navigateur. Le swahili est aussi traduit.

## Ce qu'on y trouve
| Page | Contenu |
|---|---|
| **Vue d'ensemble** | Dons de l'année, du mois et au total ; graphique des 12 derniers mois ; messages à traiter ; état du site (Stripe, e-mails, production) ; avancement des traductions FR/SW ; derniers dons et derniers messages |
| **Diapositives, Présentation, Royaumes et patrimoine, Collections, Équipe** | Liste avec vignettes, recherche, filtres (royaumes / programmes, traductions manquantes), pastilles EN/FR/SW ; fiche d'édition avec **onglets English / Français / Kiswahili**, aperçu de l'image, options, et sur la même page la **lignée royale** ou les **objets d'une collection** |
| **Collections** | **Plusieurs photos d'un coup** par glisser-déposer : le titre est tiré du nom du fichier |
| **Dons** | Filtres (payés, en attente, abandonnés), recherche, total, **export Excel/CSV** |
| **Messages** | Boîte de réception, non-lus mis en avant, « Marquer comme traité », « Répondre par e-mail » |
| **Réglages du site** | Adresse, téléphone, réseaux sociaux, textes des pages À propos et Dons, en 3 langues |
| **Recherche globale** | Dans tout le contenu, les dons et les messages |
| **Mon compte** | Changer son mot de passe |

Le dashboard s'adapte au mobile (menu repliable). Il prévient aussi si on quitte une fiche sans l'avoir enregistrée.

## Installation
Aucune migration : le dashboard utilise les tables existantes.
```bash
python manage.py test mainApp tableau
python manage.py runserver 8001
```
