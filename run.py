from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

def ensure_columns():
    """モデルに追加されたカラムをDBに反映する（なければALTER TABLE）"""
    with app.app_context():
        try:
            db.session.execute(text(
                "ALTER TABLE Users ADD COLUMN notifications_viewed_at DATETIME"
            ))
            db.session.commit()
        except Exception:
            pass  # すでに存在する場合は無視

if __name__ == "__main__":
    ensure_columns()
    app.run(debug=True, host="0.0.0.0", port=5000)
