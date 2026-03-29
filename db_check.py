import sqlite3
import os

db_path = 'instance/site.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Tables ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print(t[0])

if ('users',) in tables or ('User',) in tables:
    table_name = 'users' if ('users',) in tables else 'User'
    print(f"\n--- Users in {table_name} ---")
    cursor.execute(f"SELECT email, username FROM {table_name} LIMIT 5;")
    users = cursor.fetchall()
    for u in users:
        print(u)
else:
    print("\nNo user table found.")

conn.close()
