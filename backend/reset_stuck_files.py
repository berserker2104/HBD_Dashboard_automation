import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import urllib.parse

load_dotenv()
try:
    user = os.getenv("DB_USER")
    password = urllib.parse.quote_plus(os.getenv("DB_PASSWORD_PLAIN") or os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    
    uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_engine(uri)
    with engine.connect() as conn:
        print("Resetting stuck IN_PROGRESS files...")
        res = conn.execute(text("UPDATE file_registry SET status='ERROR', error_message='Stuck process reset' WHERE status='IN_PROGRESS'"))
        conn.commit()
        print(f"Successfully reset {res.rowcount} files.")
        
        counts = conn.execute(text("SELECT status, COUNT(*) FROM file_registry GROUP BY status")).fetchall()
        print("\n--- Current Status ---")
        for row in counts:
            print(f"{row[0]}: {row[1]}")
            
except Exception as e:
    print(f"Error: {e}")
