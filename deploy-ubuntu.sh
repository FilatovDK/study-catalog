#!/usr/bin/env bash
set -euo pipefail

# Usage: sudo bash deploy-ubuntu.sh [cloud|local]
MODE="${1:-cloud}"
if [[ "$MODE" != cloud && "$MODE" != local ]]; then
  echo "Usage: sudo bash deploy-ubuntu.sh [cloud|local]" >&2
  exit 2
fi
if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 2
fi

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv curl

install -d -m 755 /opt/study-catalog
install -d -o www-data -g www-data -m 700 /var/lib/study-catalog
install -m 644 "$SOURCE_DIR/app.py" "$SOURCE_DIR/auth.py" "$SOURCE_DIR/metrics.py" "$SOURCE_DIR/requirements.txt" /opt/study-catalog/
cp -a "$SOURCE_DIR/templates" "$SOURCE_DIR/static" /opt/study-catalog/

python3 -m venv /opt/study-catalog/.venv
/opt/study-catalog/.venv/bin/python -m pip install --no-cache-dir -r /opt/study-catalog/requirements.txt

if [[ ! -s /var/lib/study-catalog/secret_key ]]; then
  /opt/study-catalog/.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))' > /var/lib/study-catalog/secret_key
fi
chown www-data:www-data /var/lib/study-catalog/secret_key
chmod 600 /var/lib/study-catalog/secret_key

if [[ "$MODE" == local ]]; then
  DISPLAY_MODE="Локальная VM (проверка)"
else
  DISPLAY_MODE="Облачная VM (IaaS)"
fi

cat > /etc/systemd/system/study-catalog.service <<SERVICE
[Unit]
Description=Study Catalog - laboratory work 7
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/study-catalog
Environment="DEPLOYMENT_MODE=$DISPLAY_MODE"
Environment=STUDY_CATALOG_DB=/var/lib/study-catalog/users.db
Environment=STUDY_CATALOG_SECRET_FILE=/var/lib/study-catalog/secret_key
Environment=STUDY_CATALOG_AVATAR_DIR=/var/lib/study-catalog/avatars
ExecStart=/opt/study-catalog/.venv/bin/gunicorn --workers 1 --bind 0.0.0.0:8080 --access-logfile - app:app
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now study-catalog.service
systemctl restart study-catalog.service

for attempt in $(seq 1 45); do
  if curl --fail --silent http://127.0.0.1:8080/health | grep -q '"status":"ok"'; then
    echo "Study Catalog is ready at port 8080."
    exit 0
  fi
  sleep 1
done
systemctl status study-catalog.service --no-pager || true
exit 1
