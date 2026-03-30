import sqlite3

db = 'instance/kisan_smart.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", [r[0] for r in cur.fetchall()])

try:
    cur.execute("SELECT id, email, username, is_verified, is_locked, failed_login_attempts FROM users LIMIT 5;")
    rows = cur.fetchall()
    print("\nUsers:")
    for r in rows:
        print(r)
except Exception as e:
    print("Error reading users:", e)

try:
    cur.execute("SELECT role_id, role_name FROM roles;")
    print("\nRoles:", cur.fetchall())
except Exception as e:
    print("Error reading roles:", e)

conn.close()
print("\nDone.")
