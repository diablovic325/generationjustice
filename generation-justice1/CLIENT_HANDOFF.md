# Client Handoff Notes

## Project

Generation Justice membership website.

## Branding

The website uses the Generation Justice seal as the main logo and follows the seal palette:
dark navy, muted gold, white, and light blue-grey backgrounds.

## Purpose

The site is a central members-only hub for:

- Membership applications
- Code of Conduct page
- Automatic registration numbers
- Printable membership certificates
- Four membership participation levels
- Discussion topics and replies
- Essay competitions and monthly winners
- Online broadcast lessons via Zoom or YouTube links
- Internships and country projects
- Free courses
- Article submissions
- Monthly magazine
- Books
- Monthly expert panel discussions
- Site-wide broadcasts

## Demo Login

- Email: `demo@generationjustice.org`
- Password: `demo123`

Organizer demo:

- Email: `organizer@generationjustice.org`
- Password: `organizer123`

Admin demo:

- Email: `admin@generationjustice.org`
- Password: `admin123`

Organizer and Admin accounts can delete comments.

## Membership Levels

1. Ambassador - accepted into the programme, online discussions, events, and competitions.
2. Active Ambassador - contributes discussions, magazine content, and online book content.
3. Senior Ambassador - leads initiatives/events and recruits new members.
4. Country Lead - elite tier, leads activity in their country under Trustee supervision.

## Certificate Artwork

The `/certificates` page includes a placeholder for the basic Ambassador certificate artwork.
Replace that placeholder when the final artwork is supplied.

## VPS Start Command

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Public traffic should go through nginx.

## Health Check

`/health`

## Important Production Note

This is a working FastAPI/SQLite implementation. SQLite is suitable for a small first launch or demonstration.
For heavy public use, switch the database to PostgreSQL and add an admin panel for approvals, editing winners,
managing lessons, and reviewing submissions.
