import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def find_remaining_fast():
    with engine.connect() as conn:
        print("--- Finding Remaining Rows Fast ---")
        
        # Check max ID in raw
        max_raw = conn.execute(text("SELECT MAX(id) FROM raw_google_map_drive_data")).scalar()
        print(f"Max ID in Raw: {max_raw}")
        
        # Check max processed ID in clean
        max_clean_processed = conn.execute(text("SELECT MAX(raw_id) FROM raw_clean_google_map_data")).scalar()
        print(f"Max Processed Raw ID in Clean: {max_clean_processed}")
        
        if max_raw > max_clean_processed:
            print(f"There are {max_raw - max_clean_processed} rows beyond the last processed ID.")
            
            # Show which files these rows belong to
            sql = text("""
                SELECT drive_file_name, COUNT(*) 
                FROM raw_google_map_drive_data 
                WHERE id > :mid
                GROUP BY drive_file_name
            """)
            res = conn.execute(sql, {"mid": max_clean_processed}).fetchall()
            for row in res:
                print(f" - {row[0]}: {row[1]} rows")
        else:
            print("The gap is not at the end of the table. Scanning for gaps...")
            # Search the whole table but with a faster join or sample
            print("Scanning whole table for specific missing rows...")
            sql = text("""
                SELECT r.drive_file_name, COUNT(*) 
                FROM raw_google_map_drive_data r 
                LEFT JOIN raw_clean_google_map_data c ON r.id = c.raw_id 
                WHERE c.raw_id IS NULL 
                GROUP BY r.drive_file_name
                LIMIT 50
            """)
            res = conn.execute(sql).fetchall()
            for row in res:
                print(f" - {row[0]}: {row[1]} rows")

if __name__ == "__main__":
    find_remaining_fast()
