import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD_PLAIN")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

with engine.connect() as conn:
    raw = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).scalar()
    clean_valid = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status='VALID'")).scalar()
    master = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).scalar()
    
    print(f"RAW Table           : {raw:,}")
    print(f"CLEAN (Valid only)  : {clean_valid:,}")
    print(f"MASTER Table        : {master:,}")
    print(f"Difference (Gap)    : {clean_valid - master:,}")
