from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

import urllib.parse
pw = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

with engine.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data WHERE row_signature IS NOT NULL")).scalar()
    print(f"Rows with row_signature: {count}")
    
    if count > 0:
        dupes = conn.execute(text("""
            SELECT row_signature, COUNT(*) as cnt 
            FROM raw_google_map_drive_data 
            WHERE row_signature IS NOT NULL 
            GROUP BY row_signature 
            HAVING cnt > 1 
            ORDER BY cnt DESC 
            LIMIT 10
        """)).fetchall()
        print(f"Found {len(dupes)} duplicate signature groups.")
        for r in dupes:
            print(f"Signature: {r[0]}, Count: {r[1]}")
