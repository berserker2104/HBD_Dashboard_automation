import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def monitor_flow():
    with open('pending_ids.txt', 'r') as f:
        file_ids = [line.strip() for line in f if line.strip()]
    
    if not file_ids:
        print("No pending IDs to monitor.")
        return

    with engine.connect() as conn:
        print(f"Monitoring Flow for {len(file_ids)} Files...\n")
        
        # 1. Registry Status
        res = conn.execute(text("SELECT status, COUNT(*) FROM file_registry WHERE drive_file_id IN :ids GROUP BY status"), {"ids": file_ids}).fetchall()
        print("--- File Registry Status ---")
        for s, c in res:
            print(f" {s}: {c}")

        # 2. Raw Table Count
        raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data WHERE drive_file_id IN :ids"), {"ids": file_ids}).scalar()
        print(f"\n--- Raw Records Ingested ---")
        print(f" Total Rows: {raw_count:,}")

        # 3. Clean Table Status (Join with Raw)
        try:
            clean_count = conn.execute(text("""
                SELECT COUNT(*) 
                FROM raw_clean_google_map_data c
                JOIN raw_google_map_drive_data r ON c.raw_id = r.id
                WHERE r.drive_file_id IN :ids
            """), {"ids": file_ids}).scalar()
            print(f"\n--- Clean Records Processed ---")
            print(f" Total Rows: {clean_count:,}")
        except Exception as e:
            msg = str(e)
            if "[SQL:" in msg: msg = msg.split("[SQL:")[0]
            print(f"\n--- Clean Table Error: {msg} ---")
            
        # 4. Master Table Status (Approximate via Clean)
        try:
            # We can check how many rows from these IDs reached 'VALID' status in clean
            valid_count = conn.execute(text("""
                SELECT COUNT(*) 
                FROM raw_clean_google_map_data c
                JOIN raw_google_map_drive_data r ON c.raw_id = r.id
                WHERE r.drive_file_id IN :ids AND c.validation_status = 'VALID'
            """), {"ids": file_ids}).scalar()
            print(f"\n--- Records in Master (Approx via Clean Valid) ---")
            print(f" Total Rows: {valid_count:,}")
        except:
            pass

if __name__ == "__main__":
    monitor_flow()
