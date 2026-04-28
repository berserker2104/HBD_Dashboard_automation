import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def get_pending_ids():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT drive_file_id FROM file_registry WHERE status='PENDING'")).fetchall()
        with open('pending_ids.txt', 'w') as f:
            for r in res:
                f.write(f"{r[0]}\n")
        print(f"Saved {len(res)} IDs to pending_ids.txt")

if __name__ == "__main__":
    get_pending_ids()
