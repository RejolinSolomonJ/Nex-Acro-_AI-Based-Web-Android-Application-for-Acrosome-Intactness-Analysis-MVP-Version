"""
Application configuration loaded from environment variables.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ── MongoDB ──────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "acrosome_db"

    # ── JWT Auth ─────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-super-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Server ───────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # ── ML Model ─────────────────────────────────────────────
    MODEL_PATH: str = str(BASE_DIR / "ml_models" / "acrosome_cnn_model.h5")
    IMAGE_SIZE: int = 224
    CONFIDENCE_THRESHOLD: float = 0.5

    # ── File Upload ──────────────────────────────────────────
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,bmp,tiff"

    # ── Reports ──────────────────────────────────────────────
    REPORTS_DIR: str = str(BASE_DIR / "reports")

    # ── Encryption ───────────────────────────────────────────
    ENCRYPTION_KEY: str = "default-encryption-key"

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
