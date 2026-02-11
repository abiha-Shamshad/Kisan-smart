import sqlite3
import os

db_path = r"c:\Users\Each One Teach One\Desktop\Kisan smart\instance\test_kisan.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in {db_path}: {tables}")
    conn.close()
else:
    print(f"File not found: {db_path}")
