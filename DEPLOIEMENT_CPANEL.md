# NAFUV : déploiement automatique GitHub → cPanel

```
git push (ton PC)
   → GitHub Actions : tests
   → si les tests passent : la version est copiée sur la branche « production »
   → le serveur cPanel vérifie toutes les 5 minutes (tâche cron) et installe la nouvelle version
     (git, pip, migrate, collectstatic, redémarrage)
```
- Si un test échoue, la branche `production` ne change pas : **rien n'est déployé**.
- GitHub ne se connecte jamais au serveur (l'hébergement n'accepte pas le SSH venant de l'extérieur) : c'est le serveur qui récupère la version validée, avec sa clé de lecture seule.
## ceci est un test
## Fichiers
| Fichier | Rôle |
|---|---|
| `.github/workflows/deploy.yml` | Tests, puis copie de la version testée sur la branche `production` |
| `deploy/verifier.sh` | Lancé toutes les 5 minutes par la tâche cron : installe s'il y a du nouveau |
| `deploy/cpanel.sh` | La mise à jour elle-même (peut aussi être lancée à la main) |
| `passenger_wsgi.py` | Point d'entrée de l'application pour cPanel |

## Sur le serveur, jamais dans Git
- `~/nafuv_web/.env` : les secrets (clé Django, base MySQL, Stripe, e-mail)
- `~/.nafuv-deploy.conf` : chemin de l'application, environnement Python, branche (`production`)
- `~/public_html/media` et `~/public_html/static` : images et fichiers statiques
- `~/nafuv-deploiement.log` : le journal des déploiements

## Au quotidien
```bash
git add -A
git commit -m "Ce que j'ai changé"
git push
```
- Les tests sont visibles dans GitHub → onglet **Actions**.
- Le site est à jour au plus tard 5 minutes après la coche verte.
- Journal des déploiements : `tail -n 40 ~/nafuv-deploiement.log`
- Déployer tout de suite, sans attendre : `bash ~/nafuv_web/deploy/cpanel.sh`

## En cas de problème
- **Les tests échouent** : l'onglet Actions montre le test en cause. Le site n'a pas changé.
- **Le site ne se met pas à jour** : `tail -n 40 ~/nafuv-deploiement.log`
- **Le site affiche une erreur** : `tail -n 30 ~/nafuv_web/stderr.log`
- **Revenir à la version précédente** : sur ton PC, `git revert HEAD` puis `git push`.
- **Restaurer les sauvegardes** : `~/sauvegarde_nafuv_web_AAAAMMJJ.tar.gz` (fichiers) et `~/sauvegarde_nafuv_AAAAMMJJ.sql` (base).
