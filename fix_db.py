import sqlite3
conn = sqlite3.connect('instance/app.db')
conn.execute("UPDATE alembic_version SET version_num='e5ae00de9bdc'")
conn.commit()
conn.close()
print('ok')
