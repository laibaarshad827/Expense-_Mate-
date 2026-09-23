"""
Quick utility to peek at everything currently stored in the database.
Run with: python check_db.py
"""

from database.database import get_connection

conn = get_connection()
cursor = conn.cursor()

tables = ["USER", "OTP", "CATEGORY", '"TRANSACTION"']

for table in tables:
    display_name = table.strip('"')
    print(f"\n{'=' * 50}")
    print(f"TABLE: {display_name}")
    print("=" * 50)

    rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
    if not rows:
        print("  (empty)")
    else:
        for row in rows:
            print(" ", dict(row))

conn.close()