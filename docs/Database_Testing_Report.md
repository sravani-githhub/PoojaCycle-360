# Testing report

Tests use temporary SQLite databases to avoid touching real data. PostgreSQL execution is not claimed unless stated below.

## Results (25 October 2026)

- Python syntax/import check: passed; 14 SQLAlchemy tables loaded.
- Alembic clean SQLite migration: passed.
- Alembic schema drift check: passed (`No new upgrade operations detected`).
- Fictional seed insertion: passed.
- Pytest: **6 passed**. Coverage includes seed rows, health handler, paginated CRUD/read/update/delete, waste-report create/read, invalid quantity/status, missing foreign key, order subtotal validation, and order checkout with saved item/stock update.
- PostgreSQL: **not run**. PostgreSQL and Docker are not installed in the current environment.
- Browser smoke check: local home and collection pages loaded; API indicator showed connected and the collection table read the fictional demo report from SQLite.
- Screenshot: `docs/screenshots/home.png` is a desktop-sized capture of the running frontend; dashboard screenshot capture was not available in the browser session.

The suite calls FastAPI route handlers against temporary SQLite sessions; it does not claim PostgreSQL or external-network verification.
