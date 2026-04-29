import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)  # git clone 直後でも instance/ がなければ自動作成


class Config:
    # 本番では必ず環境変数で指定すること。未設定なら毎起動ごとにランダム生成（セッション無効化）
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'dev.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_COST = int(os.getenv("BCRYPT_COST", 12))  # 開発でも12推奨（遅く感じたら下げて）
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    WTF_CSRF_ENABLED = True
    TIMEZONE = "Asia/Tokyo"
    LOGIN_MAX_ATTEMPTS = 5        # この回数失敗で短期ロック
    LOGIN_LOCK_MINUTES = 15       # 短期ロック時間（分）
    VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "BDbCMzvIhU_8730uEe1wAXhXuzwlGHTxgDxf0GsAI05c5e1I4LOhMQTdVN1bNFZWAjKttq7MWmDeb1UUF5XtyH0")
    VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIPP6K53OLyvzwHff4hsHjQtux4J77gtWV2QWbDt5AbWwoAoGCCqGSM49\nAwEHoUQDQgAENsIzO8iFT/zvfS4R7XABeFe7PCUYdPGAPF/QawAjTlzl7Ujgs6Ex\nBN1U3Vs0VlYCMq22rsxaYN5vVRQXle3IfQ==\n-----END EC PRIVATE KEY-----")
    VAPID_CLAIMS = {"sub": "mailto:mimo-app@example.com"}
