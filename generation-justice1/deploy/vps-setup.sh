#!/usr/bin/env bash
set -euo pipefail

APP_NAME="generation-justice"
APP_DIR="${APP_DIR:-/var/www/generation-justice}"
DOMAIN="${DOMAIN:-example.com}"
PORT="${PORT:-8000}"
DATABASE_PATH="${DATABASE_PATH:-$APP_DIR/data/generation_justice.db}"

if [ "$DOMAIN" = "example.com" ]; then
    echo "Set DOMAIN before running, for example:"
    echo "sudo DOMAIN=yourdomain.com APP_DIR=/var/www/generation-justice bash deploy/vps-setup.sh"
    exit 1
fi

sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx sqlite3

sudo mkdir -p "$APP_DIR/data" "$APP_DIR/logs" "$APP_DIR/backups"
sudo chown -R "$USER":"$USER" "$APP_DIR"

cd "$APP_DIR"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

sudo chown -R www-data:www-data "$APP_DIR"

sed "s|__APP_DIR__|$APP_DIR|g; s|__PORT__|$PORT|g; s|__DATABASE_PATH__|$DATABASE_PATH|g" \
    "$APP_DIR/deploy/generation-justice.service" | sudo tee "/etc/systemd/system/$APP_NAME.service" >/dev/null

sed "s|__DOMAIN__|$DOMAIN|g; s|__PORT__|$PORT|g" \
    "$APP_DIR/deploy/nginx-generation-justice.conf" | sudo tee "/etc/nginx/sites-available/$APP_NAME" >/dev/null

sudo ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/$APP_NAME"
sudo nginx -t

sudo systemctl daemon-reload
sudo systemctl enable "$APP_NAME"
sudo systemctl restart "$APP_NAME"
sudo systemctl reload nginx

echo "HTTP setup complete."
echo "Next, connect SSL:"
echo "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "Then open: https://$DOMAIN"
