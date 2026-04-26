import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'dev.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_COST = int(os.getenv("BCRYPT_COST", 4))  # 開発:4、本番:12
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
    TIMEZONE = "Asia/Tokyo"
