# プロジェクトファイル構成（推奨）

> Flask + SQLAlchemy + Alembic の3人体制プロトタイプ向け
> Blueprint パターン × Application Factory パターン採用
> 担当別オーナーシップが明確になるように設計

---

## 1. 全体構造

```
heart-failure-watcher/
├── README.md                        # プロジェクト説明（v2.1のもの流用）
├── requirements.txt                 # Python依存関係
├── .env.example                     # 環境変数テンプレート
├── .gitignore                       # 除外設定
├── alembic.ini                      # Alembic設定
├── config.py                        # アプリ設定（dev/prod切替）
├── run.py                           # Flask起動エントリポイント
│
├── alembic/                         # 【A担当】DB マイグレーション
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
│
├── app/                             # アプリケーションパッケージ
│   ├── __init__.py                  # 【A専任】Flask app factory
│   ├── extensions.py                # 【A専任】db, login_manager等のシングルトン
│   │
│   ├── models/                      # 【A担当】SQLAlchemy モデル
│   │   ├── __init__.py
│   │   ├── mixins.py                # TimestampMixin, SoftDeleteMixin
│   │   ├── user.py                  # Users
│   │   ├── watch_relationship.py    # Watch_Relationships
│   │   ├── invitation.py            # Invitations
│   │   ├── daily_record.py          # Daily_Records
│   │   ├── record_read_status.py    # Record_Read_Status
│   │   ├── notification_log.py      # Notification_Log
│   │   └── notification_preferences.py
│   │
│   ├── auth/                        # 【A担当】認証 Blueprint
│   │   ├── __init__.py              # bp = Blueprint("auth", ...)
│   │   ├── routes.py                # /auth/* ルート
│   │   ├── forms.py                 # WTForms（登録、ログイン）
│   │   └── helpers.py               # PIN check, hash, session helper
│   │
│   ├── parent/                      # 【A担当（routes）+ B担当（templates）】
│   │   ├── __init__.py              # bp = Blueprint("parent", ...)
│   │   ├── routes.py                # 【A】/parent/* ルート
│   │   ├── forms.py                 # 【A】親側のフォーム定義
│   │   └── services.py              # 【A】親側のビジネスロジック
│   │
│   ├── watcher/                     # 【A担当（routes）+ C担当（templates）】
│   │   ├── __init__.py              # bp = Blueprint("watcher", ...)
│   │   ├── routes.py                # 【A】/watcher/* ルート
│   │   └── services.py              # 【A】子側のビジネスロジック
│   │
│   ├── invitations/                 # 【A担当】招待トークン Blueprint
│   │   ├── __init__.py
│   │   ├── routes.py                # /auth/register/watcher/<token>
│   │   └── helpers.py               # トークン発行・検証
│   │
│   ├── core/                        # 【A担当】アプリ横断ロジック
│   │   ├── __init__.py
│   │   ├── alert_logic.py           # 判定ロジック（仕様書 §7）
│   │   ├── tz.py                    # JST 統一ユーティリティ
│   │   └── decorators.py            # @login_required_parent 等
│   │
│   ├── templates/                   # Jinja2 テンプレート
│   │   ├── base.html                # 【A初期版、B/C共有】共通レイアウト
│   │   ├── auth/                    # 【B/Cが該当画面を担当】
│   │   │   ├── login.html           # 共通ログイン画面（B/C どちらかがやる）
│   │   │   └── register_parent.html # 親登録（B 担当）
│   │   ├── parent/                  # 【B担当】
│   │   │   ├── home.html            # ホーム画面
│   │   │   ├── input.html           # 日次入力
│   │   │   └── invitations.html     # 招待リンク発行
│   │   ├── watcher/                 # 【C担当】
│   │   │   ├── register_via_token.html  # トークン経由登録
│   │   │   ├── dashboard.html       # ダッシュボード
│   │   │   └── parent_detail.html   # 親詳細
│   │   └── errors/                  # 【B/Cが分担】
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   └── static/                      # 静的ファイル
│       ├── css/
│       │   ├── base.css             # 【A初期版、B/C共有】共通スタイル
│       │   ├── parent.css           # 【B担当】親画面専用
│       │   └── watcher.css          # 【C担当】子画面専用
│       ├── js/
│       │   ├── parent_input.js      # 【B担当】入力画面の検証等
│       │   └── watcher_dashboard.js # 【C担当】ダッシュボードの動的処理
│       └── img/
│           └── (画像があれば)
│
├── tests/                           # 【A担当中心】テスト
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixtures
│   ├── test_alert_logic.py          # 判定ロジックの単体テスト
│   ├── test_models.py
│   └── test_routes.py
│
├── scripts/                         # 【A担当】運用スクリプト
│   ├── seed_demo_data.py            # デモデータ投入
│   └── reset_db.py                  # DB リセット
│
└── instance/                        # 【git管理外】環境固有
    ├── dev.db                       # SQLite ファイル（gitignore）
    └── (各自の .env など)
```

---

## 2. オーナーシップ早見表

### A（サーバー/DB）担当
| パス | 内容 |
|---|---|
| `app/__init__.py` | app factory、Blueprint 登録 |
| `app/extensions.py` | db, login_manager 等 |
| `app/models/**` | 全モデル |
| `app/auth/**` | 認証ロジック全般 |
| `app/parent/routes.py` `app/parent/forms.py` `app/parent/services.py` | 親側のサーバーロジック |
| `app/watcher/routes.py` `app/watcher/services.py` | 子側のサーバーロジック |
| `app/invitations/**` | 招待トークン |
| `app/core/**` | 判定ロジック、TZ、デコレータ |
| `alembic/**` | マイグレーション |
| `tests/**` | テスト |
| `scripts/**` | 運用スクリプト |
| `config.py` `run.py` `requirements.txt` | プロジェクト設定 |

### B（親画面）担当
| パス | 内容 |
|---|---|
| `app/templates/auth/register_parent.html` | 親登録画面 |
| `app/templates/auth/login.html` *or `templates/parent/login.html` (要相談)* | ログイン画面 |
| `app/templates/parent/**` | 親画面テンプレート全般 |
| `app/templates/errors/404.html` *or `500.html`* | エラー画面（B/C で分担） |
| `app/static/css/parent.css` | 親画面専用スタイル |
| `app/static/js/parent_input.js` | 親側の動的処理 |

### C（子画面）担当
| パス | 内容 |
|---|---|
| `app/templates/watcher/**` | 子画面テンプレート全般 |
| `app/templates/auth/login.html` *(B と要相談、どちらかが担当)* | ログイン画面 |
| `app/templates/errors/404.html` *or `500.html`* | エラー画面（B/C で分担） |
| `app/static/css/watcher.css` | 子画面専用スタイル |
| `app/static/js/watcher_dashboard.js` | 子側の動的処理 |

### 共有ファイル（編集時は予告）
| パス | 主担当 | ルール |
|---|---|---|
| `app/templates/base.html` | A 初期版 | B/C が拡張時は Slack 予告 + PR 必須 |
| `app/static/css/base.css` | A 初期版 | B/C が共通スタイル追加時は要相談 |
| `requirements.txt` | A 主導 | 各メンバーが追加したら全員に共有 |

---

## 3. 主要ファイルのテンプレート

### `run.py`
```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

### `config.py`
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'dev.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_COST = int(os.getenv("BCRYPT_COST", 4))  # 開発:4, 本番:12
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # SESSION_COOKIE_SECURE = True  # HTTPS化したら有効化
    TIMEZONE = "Asia/Tokyo"
```

### `app/__init__.py`
```python
from flask import Flask
from app.extensions import db, login_manager
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Blueprint 登録
    from app.auth import bp as auth_bp
    from app.parent import bp as parent_bp
    from app.watcher import bp as watcher_bp
    from app.invitations import bp as invitations_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(parent_bp, url_prefix="/parent")
    app.register_blueprint(watcher_bp, url_prefix="/watcher")
    app.register_blueprint(invitations_bp)

    return app
```

### `app/extensions.py`
```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
```

### `app/models/mixins.py`
```python
from datetime import datetime
from zoneinfo import ZoneInfo
from app.extensions import db

JST = ZoneInfo("Asia/Tokyo")

def now_jst():
    return datetime.now(JST)

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=now_jst, nullable=False)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst, nullable=False)

class SoftDeleteMixin:
    deleted_at = db.Column(db.DateTime, nullable=True)
```

### `app/templates/base.html`（A 初期版の最小例）
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}心不全見守りアプリ{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, msg in messages %}
                <div class="flash flash-{{ category }}">{{ msg }}</div>
            {% endfor %}
        {% endwith %}
        {% block content %}{% endblock %}
    </main>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

## 4. requirements.txt（最小構成）

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Migrate==4.0.5
alembic==1.13.0
bcrypt==4.1.0
python-dotenv==1.0.0
zoneinfo;python_version<'3.9'
pytest==7.4.0
```

> P1 で Chart.js を入れる場合はフロント側で CDN 経由（Pythonに依存追加なし）
> メール通知を実装する場合は `Flask-Mail==0.9.1` 追加

---

## 5. .gitignore（推奨）

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.pytest_cache/

# Flask
instance/
*.db
*.sqlite

# 環境変数
.env

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## 6. 初期セットアップ手順（A が Day 1 朝に実施）

```bash
# 1. リポジトリ作成 + クローン
git clone https://github.com/<org>/heart-failure-watcher.git
cd heart-failure-watcher

# 2. 仮想環境
python -m venv .venv
source .venv/bin/activate  # Windowsは .venv\Scripts\activate

# 3. 依存関係
pip install -r requirements.txt

# 4. ディレクトリ構造を作成（空ファイルでOK）
mkdir -p app/{models,auth,parent,watcher,invitations,core,templates/{auth,parent,watcher,errors},static/{css,js,img}} alembic/versions tests scripts instance

# 5. Alembic 初期化
alembic init alembic  # alembic.ini が出力される

# 6. .env ファイル作成（各メンバー）
cp .env.example .env

# 7. 起動確認
python run.py
```

---

## 7. ブランチ運用と PR ルール

### ブランチ命名
```
main                              # protected
feature/server-init               # A
feature/parent-input              # B
feature/watcher-dashboard         # C
fix/<short-description>           # バグ修正
```

### PR ルール
- main への direct push 禁止
- PR は最低 1人の approve で merge
- merge は Squash merge を推奨（コミット履歴を綺麗に）
- conflict 時は本人がローカルで rebase

### 共有ファイル編集時の予告
Slack/LINE/Discord で以下を投稿：
```
@here base.html を 30分くらい触ります（〇〇のため）
```

---

## 8. 起動前チェックリスト（Day 1 朝）

- [ ] 全員が Python 3.11+ をインストール済み
- [ ] 全員が GitHub アカウントを持ち、リポジトリにアクセスできる
- [ ] 全員が VSCode（または同等のエディタ）+ Python拡張をインストール済み
- [ ] 全員が SQLite ブラウザ（DB Browser for SQLite等）をインストール済み
- [ ] チャット・通話手段（Slack/Discord/Zoom）が確立している
- [ ] ワイヤーフレームが共有 URL で全員見られる

---

*Last updated: 2026-04-26*
