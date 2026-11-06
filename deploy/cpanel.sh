#!/usr/bin/env bash
# =============================================================================
# Updates NAFUV on the cPanel hosting from GitHub.
# Launched automatically by deploy/verifier.sh (cron job, every 5 minutes)
# when a new validated version is on the "production" branch, or by hand in
# the cPanel Terminal:
#     bash ~/nafuv_web/deploy/cpanel.sh
#
# The server settings are read from ~/.nafuv-deploy.conf (never in Git):
#     APP_DIR=/home/USER/nafuv_web
#     VENV_ACTIVATE=/home/USER/virtualenv/nafuv_web/3.11/bin/activate
#     BRANCH=production
# =============================================================================
set -euo pipefail

CONF="$HOME/.nafuv-deploy.conf"
if [ ! -f "$CONF" ]; then
    echo "ERROR: $CONF is missing (see DEPLOIEMENT_CPANEL.md)." >&2
    exit 1
fi
# shellcheck disable=SC1090
source "$CONF"
BRANCH="${BRANCH:-production}"

cd "$APP_DIR"
echo "==> $(date '+%Y-%m-%d %H:%M:%S') · deploying $BRANCH in $APP_DIR"

echo "==> Getting the code from GitHub"
git fetch --quiet origin "$BRANCH"
AVANT=$(git rev-parse HEAD)
git reset --hard --quiet "origin/$BRANCH"
APRES=$(git rev-parse HEAD)
echo "    $AVANT -> $APRES"

echo "==> Python environment"
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "==> Database migrations"
python manage.py migrate --noinput

echo "==> Static files"
python manage.py collectstatic --noinput --verbosity 0

echo "==> Configuration check"
python manage.py check --deploy --fail-level ERROR

echo "==> Restarting the application"
mkdir -p tmp
touch tmp/restart.txt

echo "==> Done: NAFUV is up to date ($(git log -1 --format='%h %s'))"
