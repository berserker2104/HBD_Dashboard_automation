import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

def retry_errors():
    load_dotenv()
    engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")
    
    with engine.connect() as conn:
        # 1. Show errors
        print("--- Current Errors ---")
        errors = conn.execute(text("SELECT filename, error_message FROM file_registry WHERE status='ERROR' LIMIT 10")).fetchall()
        for row in errors:
            print(f" {row[0]}: {row[1]}")
            
        # 2. Reset status to PENDING
        print("\nResetting status for files currently in ERROR...")
        res = conn.execute(text("UPDATE file_registry SET status='PENDING', error_message=NULL WHERE status='ERROR'"))
        conn.commit()
        print(f"Successfully reset {res.rowcount} files to PENDING.")

if __name__ == "__main__":
    retry_errors()
