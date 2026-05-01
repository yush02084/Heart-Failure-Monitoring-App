from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_apscheduler import APScheduler
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
csrf = CSRFProtect()
scheduler = APScheduler()
mail = Mail()

login_manager.login_view = "auth.login"
login_manager.login_message = "ログインが必要です。"
