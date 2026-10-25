"""Export model DDL for PostgreSQL review; Alembic remains the migration tool."""
from pathlib import Path
import sys
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

backend = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend))
from app.database import Base  # noqa: E402
from app import models  # noqa: E402,F401

parts = [
    "-- Generated from backend/app/models.py using the SQLAlchemy PostgreSQL dialect.",
    "-- Prefer `python -m alembic upgrade head` for managed schema updates.",
]
for table in Base.metadata.sorted_tables:
    parts.append(str(CreateTable(table).compile(dialect=postgresql.dialect())) + ";")
    for index in sorted(table.indexes, key=lambda item: item.name or ""):
        parts.append(str(CreateIndex(index).compile(dialect=postgresql.dialect())) + ";")
output = Path(__file__).with_name("schema.sql")
output.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
print(f"PostgreSQL DDL generated for {len(Base.metadata.tables)} tables.")
