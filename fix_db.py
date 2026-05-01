import sqlite3
conn = sqlite3.connect('instance/app.db')

# alembic_versionテーブルがなければ作成
conn.execute("""
    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(32) NOT NULL,
        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
    )
""")

# 初期スキーマのリビジョンを設定
conn.execute("DELETE FROM alembic_version")
conn.execute("INSERT INTO alembic_version VALUES ('e5ae00de9bdc')")

# notifications_viewed_atカラムを追加（なければ）
try:
    conn.execute("ALTER TABLE Users ADD COLUMN notifications_viewed_at DATETIME")
    print("カラム追加: ok")
except Exception:
    print("カラムは既に存在")

conn.commit()
conn.close()
print('DB修復完了')
