import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)  # git clone 直後でも instance/ がなければ自動作成


def _resolve_database_uri() -> str:
    """DATABASE_URL があればそれを使う(Postgres想定)。未設定ならローカルSQLite。
    Render等の一部プロバイダは postgres:// 形式で渡してくるが、SQLAlchemy 2.x は
    postgresql:// を要求するため正規化する。
    """
    url = os.getenv("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return f"sqlite:///{BASE_DIR / 'instance' / 'dev.db'}"


class Config:
    # 本番では必ず環境変数で指定すること。未設定なら毎起動ごとにランダム生成（セッション無効化）
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_COST = int(os.getenv("BCRYPT_COST", 12))  # 開発でも12推奨（遅く感じたら下げて）
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    WTF_CSRF_ENABLED = True
    TIMEZONE = "Asia/Tokyo"
    LOGIN_MAX_ATTEMPTS = 5        # この回数失敗で短期ロック
    LOGIN_LOCK_MINUTES = 15       # 短期ロック時間（分）
    # 本番では必ず環境変数で指定すること。未設定の場合はプッシュ通知機能が無効になる
    VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
    VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
    VAPID_CLAIMS = {"sub": f"mailto:{os.getenv('VAPID_CONTACT_EMAIL', 'admin@example.com')}"}
    # メール通知。MAIL_SERVER と MAIL_DEFAULT_SENDER 両方未設定なら送信スキップ
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
