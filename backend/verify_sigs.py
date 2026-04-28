import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD_PLAIN") # Using plain if available
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

with engine.connect() as conn:
    null_sig = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data WHERE row_signature IS NULL")).fetchone()[0]
    total = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).fetchone()[0]
    has_sig = total - null_sig
    
    # Check if index exists
    idx_res = conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data WHERE Key_name = 'idx_row_signature'")).fetchall()
    
    # Check for duplicates among populated signatures
    dupe_sigs = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT row_signature, COUNT(*) as cnt 
            FROM raw_google_map_drive_data 
            WHERE row_signature IS NOT NULL 
            GROUP BY row_signature 
            HAVING cnt > 1
        ) as t
    """)).fetchone()[0]
    
    print(f"Total Rows: {total:,}")
    print(f"Rows with NULL Signature: {null_sig:,}")
    print(f"Rows with Populated Signature: {has_sig:,}")
    print(f"Index 'idx_row_signature' exists: {bool(idx_res)}")
    print(f"Duplicate populated signature groups: {dupe_sigs}")
