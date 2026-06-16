# Generation Justice

Python/FastAPI membership hub for the Generation Justice project.

## Run

1. Double-click `run_site.bat`.
2. Open the address shown in the terminal, usually `http://127.0.0.1:8000`.

If port `8000` is busy, the launcher automatically tries `8001`.

## Deploy Online

Use the files added for hosting:

- `Procfile` - Heroku-style hosts.
- `render.yaml` - Render.
- `railway.json` - Railway.
- `Dockerfile` - Docker hosting.
- `start.sh` - Linux start script.
- `VPS_DEPLOYMENT.md` - VPS + domain + nginx + SSL guide.
- `IMENA_DOMAIN_SETUP.md` - IMENA.ua domain connection guide.
- `CLIENT_HANDOFF.md` - handoff notes for the client.
- `deploy/` - systemd, nginx, VPS setup, and backup scripts.
- `DEPLOYMENT.md` - step-by-step deployment notes.

Most hosts need this start command:

`python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

## Demo Login

- Email: `demo@generationjustice.org`
- Password: `demo123`

Organizer demo for comment moderation:

- Email: `organizer@generationjustice.org`
- Password: `organizer123`

Admin demo for main project leadership:

- Email: `admin@generationjustice.org`
- Password: `admin123`

## What Works

- Logo and color palette matched to the Generation Justice seal.
- Membership application with address, email, phone, country, organization, interests, and password.
- Code of Conduct page.
- Four membership levels: Ambassador, Active Ambassador, Senior Ambassador, Country Lead.
- Automatic registration number and printable certificate of membership.
- Certificates page with a placeholder for the basic certificate artwork.
- Members-only access for hub pages.
- Discussion topics with detailed replies.
- Organizer-level comment deletion.
- Separate Member, Organizer, and Admin login buttons.
- Essay competition page with monthly winners and member essay submission.
- Live lesson page with Zoom/YouTube transfer links.
- Country internship projects and volunteer registration.
- Free courses, article submissions, monthly magazine, books, and panel discussions.
- Broadcast center for site announcements.

## Files

- `main.py` - backend, database setup, routes, and API.
- `templates/` - HTML page fragments.
- `static/css/styles.css` - visual design.
- `static/js/app.js` - button behavior and API requests.
- `generation_justice.db` - SQLite database, created automatically.
- `requirements.txt` - Python dependencies.
- `run_site.bat` - Windows launcher.
