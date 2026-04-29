import os
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

# ローカル開発時: 起動のたびにカラムを自動追加（なければ）
with app.app_context():
    try:
        db.session.execute(text(
            "ALTER TABLE Users ADD COLUMN notifications_viewed_at DATETIME"
        ))
        db.session.commit()
    except Exception:
        pass  # すでに存在する場合は無視

if __name__ == "__main__":
    debug = os.getenv("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=5000)
