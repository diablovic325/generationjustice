# Deploy Generation Justice

This project is ready for common Python web hosts such as Render, Railway, Heroku-style platforms, and Docker hosts.

## Recommended: Render

1. Upload this folder to a GitHub repository.
2. Go to Render and create a new Web Service.
3. Connect the repository.
4. Render can use `render.yaml` automatically.

If Render asks for commands manually:

- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

## Railway

Railway can use `railway.json`.

If Railway asks for a start command:

`python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

## Heroku-style Hosts

The `Procfile` contains:

`web: python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

## Docker

Build:

`docker build -t generation-justice .`

Run:

`docker run -p 8000:8000 generation-justice`

## Important Database Note

The site uses SQLite (`generation_justice.db`). It is fine for a school/demo project. On many free hosts, uploaded files can reset after redeploy. For a real public site with permanent member data, use a hosted database such as PostgreSQL.
