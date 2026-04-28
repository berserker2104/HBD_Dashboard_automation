"""Quick test: try connecting to the report database."""
import pymysql
import sys

HOST = '77.42.78.20'
USER = 'mukesh'
PASS = 'xVUHAaORqSxG0oYPtMJm'
DB   = 'genuinedashboardtest'

for port in [3306, 3307, 8306]:
    print(f"\nTrying {HOST}:{port} ...", end=" ", flush=True)
    try:
        conn = pymysql.connect(
            host=HOST, port=port, user=USER,
            password=PASS, database=DB, connect_timeout=5
        )
        print("SUCCESS!")
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        print("Tables:")
        for t in cur.fetchall():
            print(f"  - {t[0]}")
            cur2 = conn.cursor()
            cur2.execute(f"DESCRIBE `{t[0]}`")
            for col in cur2.fetchall():
                print(f"      {col[0]:30s} {col[1]}")
            cur2.execute(f"SELECT COUNT(*) FROM `{t[0]}`")
            cnt = cur2.fetchone()[0]
            print(f"      => {cnt} rows")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"FAILED: {e}")

print("\nAll ports failed. DB is not reachable from this machine.")
