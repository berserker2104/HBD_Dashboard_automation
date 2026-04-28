import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
try:
    import urllib.parse
    user = os.getenv("DB_USER")
    password = urllib.parse.quote_plus(os.getenv("DB_PASSWORD_PLAIN") or os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    
    uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_engine(uri)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT status, COUNT(*) FROM file_registry GROUP BY status")).fetchall()
        print("--- File Registry Status ---")
        for row in res:
            print(f"{row[0]}: {row[1]}")
            
        res2 = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).scalar()
        print(f"Total Raw Rows: {res2:,}")
except Exception as e:
    print(f"Error: {e}")
