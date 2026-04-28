import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def find_remaining():
    with engine.connect() as conn:
        print("--- Analyzing 989 Remaining Rows ---")
        
        # Find rows in raw that are NOT in clean using LEFT JOIN
        sql = text("""
            SELECT r.drive_file_name, COUNT(*) as row_count 
            FROM raw_google_map_drive_data r 
            LEFT JOIN raw_clean_google_map_data c ON r.id = c.raw_id 
            WHERE c.raw_id IS NULL 
            GROUP BY r.drive_file_name
        """)
        
        print("Files containing the remaining pending rows:")
        results = conn.execute(sql).fetchall()
        
        if not results:
            print(" No pending rows found (they might have just finished processing!).")
        else:
            total = 0
            for file_name, count in results:
                print(f" - {file_name}: {count} rows")
                total += count
            print(f"\nTotal pending: {total}")

if __name__ == "__main__":
    find_remaining()
