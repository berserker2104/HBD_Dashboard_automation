import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def check_today():
    with engine.connect() as conn:
        print("--- Rows Ingested Today ---")
        sql = text("SELECT drive_file_name, COUNT(*) FROM raw_google_map_drive_data WHERE created_at > CURDATE() GROUP BY drive_file_name")
        res = conn.execute(sql).fetchall()
        for row in res:
            print(f" {row[0]}: {row[1]} rows")

if __name__ == "__main__":
    check_today()
