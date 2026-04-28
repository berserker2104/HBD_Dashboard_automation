import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def check_counts():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT status, COUNT(*) FROM file_registry GROUP BY status")).fetchall()
        print("--- Global Status ---")
        for s, c in res:
            print(f" {s}: {c}")
        
        print("\n--- Pending Files (First 10) ---")
        res = conn.execute(text("SELECT filename, processed_at FROM file_registry WHERE status='PENDING' ORDER BY processed_at DESC LIMIT 10")).fetchall()
        for r in res:
            print(f" {r[0]} | Last Attempt: {r[1]}")

if __name__ == "__main__":
    check_counts()
