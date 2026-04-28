import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

with engine.connect() as conn:
    row = conn.execute(text("SELECT id, name, address, website, phone_number, city, state, drive_file_name, drive_uploaded_time FROM raw_google_map_drive_data ORDER BY id DESC LIMIT 1")).fetchone()
    if row:
        print("=== LATEST ROW in raw_google_map_drive_data ===")
        mapping = row._mapping if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
        for k, v in mapping.items():
            print(f"{k:<20}: {v}")
    else:
        print("Table is empty.")
