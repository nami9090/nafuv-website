#!/usr/bin/env bash
# =============================================================================
# Launched every 5 minutes by a cron job on the cPanel hosting:
#   */5 * * * * /bin/bash /home/USER/nafuv_web/deploy/verifier.sh >> /home/USER/nafuv-deploiement.log 2>&1
#
# Looks on GitHub for a new version on the "production" branch (only the
# versions that passed the tests arrive there) and installs it with cpanel.sh.
# When there is nothing new, it does nothing and writes nothing.
# =============================================================================
set -euo pipefail

CONF="$HOME/.nafuv-deploy.conf"
# shellcheck disable=SC1090
source "$CONF"
BRANCH="${BRANCH:-production}"
VERROU="$HOME/.nafuv-deploiement.lock"

# Only one deployment at a time
exec 9>"$VERROU"
if command -v flock >/dev/null 2>&1; then
    flock -n 9 || exit 0
fi

cd "$APP_DIR"
git fetch --quiet origin "$BRANCH"
if [ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$BRANCH")" ]; then
    exit 0  # already up to date
fi

echo ""
echo "############ new validated version found ############"
bash "$APP_DIR/deploy/cpanel.sh"
