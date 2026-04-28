import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def check_files():
    with engine.connect() as conn:
        print("--- Status of Errored/Pending Files ---")
        res = conn.execute(text("SELECT drive_file_id, filename, status, error_message FROM file_registry WHERE status = 'PENDING' LIMIT 20")).fetchall()
        for row in res:
            print(f"ID: {row[0]} | File: {row[1]} | Status: {row[2]} | Error: {row[3]}")

if __name__ == "__main__":
    check_files()
