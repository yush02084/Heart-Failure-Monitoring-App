from flask import Flask
from app.extensions import db, login_manager, bcrypt
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 拡張機能初期化
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Flask-Login ユーザーローダー
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprint 登録
    from app.auth import bp as auth_bp
    from app.watcher import bp as watcher_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(watcher_bp, url_prefix="/watcher")

    # ルートリダイレクト
    from flask import redirect, url_for
    from flask_login import current_user

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "watcher":
                return redirect(url_for("watcher.dashboard"))
        return redirect(url_for("auth.login"))

    # DB・デモデータ初期化
    with app.app_context():
        db.create_all()
        _seed_if_empty()

    return app


def _seed_if_empty():
    """DBが空のときだけデモデータを投入する"""
    from app.models.user import User
    if User.query.first():
        return
    from scripts.seed_demo import seed
    seed()
