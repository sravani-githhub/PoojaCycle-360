# Windows setup and run guide

## Fastest local preview (SQLite)

SQLite provides persistent local writes without a separate database installation. It is not PostgreSQL verification.

1. Install Python 3.11 or newer from python.org (the source supports Python 3.14).
2. Open PowerShell and change to the backend folder:

   ```powershell
   cd "$env:USERPROFILE\OneDrive\Desktop\hac\backend"
   ```

3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. It applies only to the current PowerShell window.

4. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   To run the API regression suite at any time, use `python -m pytest -q` from `backend`.

5. With no `backend\.env` file, the app defaults to `sqlite:///./poojacycle360.db`. Apply the migration and insert fictional examples:

   ```powershell
   alembic upgrade head
   python -m app.seed_demo
   ```

6. Start the app from the same backend folder:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```

7. Open the frontend at <http://127.0.0.1:8000/> and API docs at <http://127.0.0.1:8000/docs>. Test `GET /api/health` in Swagger, then create a waste source. The frontend and API share one origin.
8. To inspect saved values by section, run the read-only viewer from `backend`:

   ```powershell
   python view_database.py
   ```

   It groups collection, batch/impact, artisan, Eco Store, order, user, and migration records. Blank optional columns are skipped, and password hashes are never printed. The same database file can be opened with a SQLite viewer if you prefer a graphical table view.

   To confirm the saved waste-report count from a second PowerShell window opened in `backend`:

   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('poojacycle360.db'); print(c.execute('select count(*) from waste_reports').fetchone())"
   ```

   Submit the collection form in the UI and rerun the command; the count should increase.

9. Stop the API with `Ctrl+C`. SQLite data remains in `backend\poojacycle360.db`.

## PostgreSQL with Docker Desktop

Install Docker Desktop for Windows and start its engine. In PowerShell, go to `backend` and copy the example environment file:

```powershell
Copy-Item .env.example .env
```

The example credential is only for a local hackathon container. Change `POSTGRES_PASSWORD` in `.env` before using a shared environment and change the password in `DATABASE_URL` to match. Do not commit `.env`.

Start PostgreSQL:

```powershell
docker compose up -d db
docker compose ps
```

After the health check passes, run the migration, seed, and backend:

```powershell
   alembic upgrade head
python -m app.seed_demo
python -m uvicorn app.main:app --reload
```

Use <http://127.0.0.1:8000/> and <http://127.0.0.1:8000/docs>. Verify a PostgreSQL count directly:

```powershell
docker compose exec db psql -U poojacycle -d poojacycle360 -c "SELECT count(*) FROM waste_reports;"
```

Stop the API with `Ctrl+C`, then stop PostgreSQL while retaining data:

```powershell
docker compose stop db
```

`docker compose down` removes the container but keeps the named volume. `docker compose down -v` erases the local database volume.

## Environment settings and security

- `DATABASE_URL`: PostgreSQL `postgresql+psycopg://...` URL or default local SQLite.
- `CORS_ORIGINS`: comma-separated development origins. The bundled UI is served by FastAPI on the same origin.
- `DEMO_MODE`: local prototype setting; it does not enable authentication.
- `.env` is read from `backend`. Do not place production credentials in the repository or ZIP; `.gitignore` excludes `.env`, the virtual environment, and local database files.

Login, authorization, password handling, email verification, and public deployment controls are not implemented. The organizer/customer profiles used by the demo forms are fictional seed accounts. Do not expose the development server to the public internet.

## API and frontend

Every listed resource has paginated `GET /api/{resource}?limit=50&offset=0`, `POST /api/{resource}`, `GET /api/{resource}/{id}`, `PATCH /api/{resource}/{id}`, and `DELETE /api/{resource}/{id}`. Swagger is at `/docs`. The integrated frontend saves collection requests and artisan profiles, loads artisans and products from the database, displays database-backed totals, and uses atomic simulated checkout. No card data or payment is collected.
