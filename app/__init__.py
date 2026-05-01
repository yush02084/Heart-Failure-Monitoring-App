import os
from flask import Flask
from app.extensions import db, login_manager, bcrypt, migrate, csrf, scheduler, mail
from config import Config


def _init_sentry():
    """SENTRY_DSN が設定されていれば例外監視を有効化。医療データ保護のため send_default_pii=False。"""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


def create_app(config_class=Config):
    _init_sentry()

    app = Flask(__name__)
    app.config.from_object(config_class)

    # 拡張機能初期化
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)

    # APScheduler: 毎朝7時JSTに未記録チェック通知
    if not scheduler.running:
        app.config["SCHEDULER_API_ENABLED"] = False
        scheduler.init_app(app)
        from app.core.push_utils import check_and_notify_unrecorded
        scheduler.add_job(
            id="check_unrecorded",
            func=check_and_notify_unrecorded,
            trigger="cron",
            hour=7,
            minute=0,
            timezone="Asia/Tokyo",
            replace_existing=True,
        )
        scheduler.start()

    # Flask-Login ユーザーローダー
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprint 登録
    from app.auth import bp as auth_bp
    from app.watcher import bp as watcher_bp
    from app.parent import bp as parent_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(watcher_bp, url_prefix="/watcher")
    app.register_blueprint(parent_bp, url_prefix="/parent")

    # ルートリダイレクト
    from flask import redirect, url_for
    from flask_login import current_user

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.route("/sw.js")
    def service_worker():
        from flask import send_from_directory
        response = send_from_directory("static", "sw.js")
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    @app.route("/healthz")
    def healthz():
        from sqlalchemy import text
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok"}, 200
        except Exception:
            return {"status": "db_error"}, 503

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return _redirect_by_role(current_user)
        return redirect(url_for("auth.login"))

    def _redirect_by_role(user):
        if user.role == "parent":
            return redirect(url_for("parent.home"))
        return redirect(url_for("watcher.dashboard"))

    # エラーハンドラ
    from flask import render_template as _rt

    @app.errorhandler(404)
    def not_found(e):
        return _rt("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return _rt("errors/500.html"), 500

    # DB初期化（マイグレーション実行後にシード）
    with app.app_context():
        _seed_if_empty()

    return app


def _seed_if_empty():
    """DBが空のときだけデモデータを投入する。
    スキーマ作成は Alembic (flask db upgrade) で行うため、ここでは create_all() を呼ばない。
    Users テーブル未作成の場合は OperationalError が出るが、無視して何もしない。
    """
    from sqlalchemy.exc import OperationalError
    try:
        from app.models.user import User
        if User.query.first():
            return
        from scripts.seed_demo import seed
        seed()
    except OperationalError:
        pass
