# PoojaCycle 360

Hackathon prototype for reporting temple/festival waste, collection assignments, traceable processing, artisan material requests, products, simulated orders and recorded outcomes.

## Start on Windows

1. Open PowerShell in `backend` and create a virtual environment: `py -m venv .venv`, then run `.\.venv\Scripts\Activate.ps1`.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Use SQLite for the quickest local preview, or PostgreSQL via Docker Compose. Exact instructions are in [`docs/Database_Setup_Guide.md`](docs/Database_Setup_Guide.md).
4. Run `python -m alembic upgrade head`, then `python -m app.seed_demo`.
5. Start with `python -m uvicorn app.main:app --reload`.
6. Open [the app](http://127.0.0.1:8000/) or [Swagger API docs](http://127.0.0.1:8000/docs).

Original standalone prototype is preserved as `milestone1.html`; the integrated version is in `frontend/index.html` with adapter `frontend/app.js`. Use the server URL instead of `file://`.

## Deliverables and behavior

- PostgreSQL schema and local SQLite fallback; SQLAlchemy models and Alembic migration.
- ER diagram source and rendered SVG; data dictionary and setup documentation.
- Pydantic validation and actual paginated CRUD for every listed resource under `/api/{resource}`; atomic simulated order checkout at `/api/checkout`.
- Frontend form submission for waste reports and artisan profiles, database-backed artisan/product views and impact totals.
- Tests in `backend/tests` for seed data, constraints and basic API operations.
- Running desktop home-screen capture: [`docs/screenshots/home.png`](docs/screenshots/home.png).

All seed records are fictional and visibly labelled `DEMO ONLY`. Dashboard totals include only rows saved to the database and disclose seeded demo data. No environmental savings are inferred. Login and authorization are not implemented; password hashes are never accepted or exposed. No payments are processed.

## Deploy to Render (college demo)

The project includes a Render Blueprint in `render.yaml`. It creates one Python web service and a managed PostgreSQL database in Singapore. The web service runs Alembic migrations, inserts clearly marked fictional `DEMO ONLY` records (idempotently), and serves both the frontend and API from the same URL.

**Free-plan limits:** Render's free PostgreSQL databases expire 30 days after creation and have no backups; the free web service can sleep when idle. Export anything you need to keep before database expiry. Render may ask you to select a plan during setup; do not select a paid plan unless you choose to pay for it.

### Publish and deploy

1. Create a **new private GitHub repository** for this project. Do not use the unrelated remote already configured on this computer.
2. Open PowerShell in the project folder (`C:\Users\erram\OneDrive\Desktop\hac`). Initialize Git only in this folder if it is not already a repository, review `.gitignore`, commit the project, and push to the new repository. Never add `.env`, database files, or credentials.
3. Sign in to Render, choose **New → Blueprint**, and connect the new GitHub repository. Render reads `render.yaml`; review the two resources and ensure both are on the **Free** plan before applying.
4. Wait for the web service to finish deploying. Open the service URL, then check `/api/health` and `/docs`.
5. On `/api/health`, confirm the database field says `postgresql`. The demo catalog should appear on the site. New records are saved to the hosted database.

Render manages the database password and injects its connection URL; no `.env` file or secret belongs in Git. The app converts Render's `postgresql://` URL to the installed psycopg 3 driver automatically. This project has no authentication or authorization, so do not enter real personal data or treat it as a production service.
