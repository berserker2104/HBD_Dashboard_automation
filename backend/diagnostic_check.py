import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def check_everything():
    with engine.connect() as conn:
        print("--- Diagnostic Check ---")
        
        # 1. Missing rows sample
        print("\n[ Sample of Missing Rows (ID, File) ]")
        sql = text("""
            SELECT r.id, r.drive_file_name 
            FROM raw_google_map_drive_data r 
            LEFT JOIN raw_clean_google_map_data c ON r.id = c.raw_id 
            WHERE c.raw_id IS NULL 
            LIMIT 10
        """)
        res = conn.execute(sql).fetchall()
        for row in res:
            print(f" ID: {row[0]} | File: {row[1]}")
            
        # 2. Validation Log
        try:
            print("\n[ Recent Validation Log ]")
            res = conn.execute(text("SELECT * FROM data_validation_log ORDER BY timestamp DESC LIMIT 5")).fetchall()
            for row in res:
                print(f" {row}")
        except:
            pass
            
        # 3. ETL DLQ
        try:
            print("\n[ Recent DLQ Entries ]")
            res = conn.execute(text("SELECT * FROM etl_dlq ORDER BY failed_at DESC LIMIT 5")).fetchall()
            for row in res:
                print(f" {row}")
        except:
            pass

if __name__ == "__main__":
    check_everything()
