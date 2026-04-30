"""Application configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _normalize_db_url(url: str) -> str:
    """Railway / Heroku give postgres:// — SQLAlchemy 2.x wants postgresql://."""
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    _db_url = _normalize_db_url(os.environ.get("DATABASE_URL", ""))
    SQLALCHEMY_DATABASE_URI = _db_url or f"sqlite:///{BASE_DIR / 'app.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session / security
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
