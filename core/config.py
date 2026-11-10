"""
Application configuration settings.
"""
import os
import secrets
import sys
from pathlib import Path


def get_base_dir() -> Path:
    """Return the application directory, taking PyInstaller bundles into account."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


_APP_DIR = get_base_dir()
_DEFAULT_DATA_DIR = _APP_DIR / "data"
_DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DEFAULT_DB_PATH = _DEFAULT_DATA_DIR / "budget.db"


class Settings:
    """Global application settings."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_DEFAULT_DB_PATH.as_posix()}"
    )

    # JWT Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
