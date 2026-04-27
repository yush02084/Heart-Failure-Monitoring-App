from flask import Flask
from app.extensions import db, login_manager, bcrypt, migrate, csrf
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 拡張機能初期化
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

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

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return _redirect_by_role(current_user)
        return redirect(url_for("auth.login"))

    def _redirect_by_role(user):
        if user.role == "parent":
            return redirect(url_for("parent.home"))
        return redirect(url_for("watcher.dashboard"))

    # DB初期化（マイグレーション実行後にシード）
    with app.app_context():
        _seed_if_empty()

    return app


def _seed_if_empty():
    """テーブルがなければ作成し、DBが空のときだけデモデータを投入する"""
    from sqlalchemy.exc import OperationalError
    # テーブルが存在しない場合は自動作成（flask db upgrade の代わり）
    db.create_all()
    try:
        from app.models.user import User
        if User.query.first():
            return
        from scripts.seed_demo import seed
        seed()
    except OperationalError:
        pass
