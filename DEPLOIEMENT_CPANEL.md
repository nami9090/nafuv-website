# NAFUV : déploiement automatique GitHub → cPanel

```
git push (ton PC)  →  GitHub Actions : tests  →  SSH vers le cPanel  →  deploy/cpanel.sh
                                                   (git pull, pip, migrate, collectstatic, redémarrage)
```
Si un test échoue, **rien n'est déployé** et le site en ligne reste intact.

## Fichiers
| Fichier | Rôle |
|---|---|
| `.github/workflows/deploy.yml` | Tests, puis déploiement à chaque push sur `main` (ou bouton « Run workflow ») |
| `deploy/cpanel.sh` | Mise à jour sur le serveur (lancé par GitHub, ou à la main dans le Terminal) |
| `passenger_wsgi.py` | Point d'entrée de l'application pour cPanel |

## Ce qui reste sur le serveur et n'est jamais dans Git
- `~/nafuv/.env` : les secrets (clé Django, base MySQL, Stripe, e-mail)
- `~/.nafuv-deploy.conf` : le chemin de l'application et de son environnement Python
- le dossier `media` : les images envoyées depuis le site

## Mise en place (une seule fois)
1. **Serveur → GitHub** : clé de déploiement en lecture seule sur le dépôt, puis `git clone`.
2. **Fichiers serveur** : `.env`, `~/.nafuv-deploy.conf`, images `media` récupérées de l'ancienne version.
3. **Setup Python App** : dossier de l'application = le dossier cloné.
4. **GitHub → serveur** : clé SSH autorisée sur le compte cPanel, et 4 secrets dans GitHub
   (`CPANEL_HOST`, `CPANEL_PORT`, `CPANEL_USER`, `CPANEL_SSH_KEY`).
5. Premier déploiement, puis vérification du site.

## Ensuite, au quotidien
```bash
git add -A
git commit -m "Ce que j'ai changé"
git push
```
Suivre le déploiement : GitHub → onglet **Actions**.
Déployer à la main en cas de besoin : `bash ~/nafuv/deploy/cpanel.sh` dans le Terminal cPanel.

## En cas de problème
- **Les tests échouent** : l'onglet Actions montre le test en cause. Le site n'a pas été modifié.
- **Le déploiement échoue** : l'onglet Actions affiche le message de `deploy/cpanel.sh`.
- **Le site affiche une erreur** : dans cPanel, Setup Python App → ouvrir le fichier de log indiqué, ou lancer `python manage.py check` dans le Terminal (environnement activé).
- **Revenir à la version précédente** : sur ton PC, `git revert HEAD` puis `git push`.
