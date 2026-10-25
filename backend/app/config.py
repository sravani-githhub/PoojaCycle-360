"""Small environment configuration loader; no settings package required."""
from pathlib import Path
import os

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


def load_env_file() -> None:
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()
_raw_database_url = os.getenv("DATABASE_URL", "sqlite:///./poojacycle360.db")
# Render supplies PostgreSQL URLs as postgresql://; explicitly select psycopg 3.
if _raw_database_url.startswith("postgres://"):
    _raw_database_url = "postgresql://" + _raw_database_url[len("postgres://"):]
DATABASE_URL = (
    "postgresql+psycopg://" + _raw_database_url[len("postgresql://"):]
    if _raw_database_url.startswith("postgresql://")
    else _raw_database_url
)
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",") if x.strip()]
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
