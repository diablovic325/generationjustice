# VPS Deployment Guide

Use this when the client has a domain and wants the site on a real VPS.

## Server Assumption

- Ubuntu 22.04 or 24.04 VPS
- Root or sudo SSH access
- Domain name already purchased

## 1. Point the Domain to the VPS

In the domain DNS panel:

- Add an `A` record for `@` pointing to the VPS public IP.
- Add an `A` record for `www` pointing to the same VPS public IP.

DNS can take minutes or hours to update.

## 2. Upload the Site

Upload the project folder to:

`/var/www/generation-justice`

The folder must contain `main.py`, `requirements.txt`, `templates/`, `static/`, and `deploy/`.

## 3. Run VPS Setup

SSH into the VPS:

```bash
ssh root@YOUR_VPS_IP
```

Go to the project folder:

```bash
cd /var/www/generation-justice
```

Run setup:

```bash
sudo DOMAIN=yourdomain.com APP_DIR=/var/www/generation-justice bash deploy/vps-setup.sh
```

Replace `yourdomain.com` with the real domain.

## 4. Add HTTPS

After DNS points to the VPS:

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 5. Check the Server

```bash
sudo systemctl status generation-justice
curl http://127.0.0.1:8000/health
```

Logs:

```bash
sudo journalctl -u generation-justice -f
```

## 6. Update the Site Later

Upload changed files, then run:

```bash
cd /var/www/generation-justice
sudo systemctl restart generation-justice
```

## 7. Backups

The app uses SQLite. Back up the database:

```bash
sudo APP_DIR=/var/www/generation-justice bash deploy/backup.sh
```

For a high-traffic public system, move from SQLite to PostgreSQL.
