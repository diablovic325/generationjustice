# Connecting the Domain on IMENA.ua

Use this guide when the domain is registered at IMENA.ua and the website is hosted on a VPS.

## What You Need First

- The domain name, for example `yourdomain.com`.
- The VPS public IPv4 address, for example `123.123.123.123`.
- SSH access to the VPS.
- The project folder uploaded to `/var/www/generation-justice`.

Important: the domain cannot point to `127.0.0.1` or a local computer. It must point to the public VPS IP.

## 1. Open the IMENA Domain Panel

1. Log in to the IMENA.ua account.
2. Open the domain list.
3. Choose the project domain.
4. Open domain management / DNS management.

In IMENA terms, this is the section where you can change DNS/domain settings and specify the IP address for the domain and subdomains such as `www`.

## 2. Check Where DNS Is Managed

Before editing records, check the domain nameservers.

- If the domain uses IMENA nameservers, edit DNS records inside IMENA.
- If the domain uses Cloudflare or another DNS service, edit DNS records there instead.

Do not edit DNS in two places at once. Only the active nameserver provider matters.

## 3. Add DNS Records

Replace `YOUR_VPS_IP` with the real VPS IP.

| Type | Host / Name | Value / Points to | TTL |
|---|---|---|---|
| A | `@` | `YOUR_VPS_IP` | 3600 |
| A | `www` | `YOUR_VPS_IP` | 3600 |

Alternative for `www`:

| Type | Host / Name | Value / Points to | TTL |
|---|---|---|---|
| CNAME | `www` | `yourdomain.com` | 3600 |

Use either `A www -> YOUR_VPS_IP` or `CNAME www -> yourdomain.com`, not both.

## 4. Remove Conflicting Records

Remove or replace old records for:

- `@`
- `www`

If there are old `AAAA` records and the VPS does not have IPv6 configured, remove those `AAAA` records too.

Do not remove `MX` records unless the client wants to change email hosting.

## 5. Wait for DNS Propagation

DNS can update in 10-60 minutes, but sometimes it can take up to 24 hours.

On Windows, check with:

```powershell
nslookup yourdomain.com
nslookup www.yourdomain.com
```

Both should show the VPS IP.

## 6. Install the Website on the VPS

SSH into the VPS:

```bash
ssh root@YOUR_VPS_IP
```

Upload the project folder to:

```bash
/var/www/generation-justice
```

Then run:

```bash
cd /var/www/generation-justice
sudo DOMAIN=yourdomain.com APP_DIR=/var/www/generation-justice bash deploy/vps-setup.sh
```

Replace `yourdomain.com` with the real domain.

## 7. Add HTTPS / SSL

After DNS points to the VPS:

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Choose the redirect-to-HTTPS option if Certbot asks.

## 8. Final Checks

Open:

```text
https://yourdomain.com
https://www.yourdomain.com
```

Check the service:

```bash
sudo systemctl status generation-justice
curl http://127.0.0.1:8000/health
```

View logs:

```bash
sudo journalctl -u generation-justice -f
```

## Common Problems

### The domain still opens an old site

Old `A` records are probably still active. Remove conflicting `@` or `www` records.

### `www` works but the root domain does not

The `@` record is missing or points to the wrong IP.

### The root domain works but `www` does not

The `www` record is missing or misconfigured.

### Certbot fails

DNS is not pointing to the VPS yet, or ports `80` / `443` are blocked by firewall.

### Email stops working

Someone changed `MX` records. Restore the original email/MX settings.
