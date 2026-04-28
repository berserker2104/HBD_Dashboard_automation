import os
import time
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Database setup
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD_PLAIN")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def perform_gap_sync():
    print("Starting Gap Sync: raw_clean_google_map_data -> g_map_master_table")
    print("=" * 60)
    
    start_time = time.time()
    batch_size = 5000
    total_synced = 0
    
    try:
        with engine.begin() as conn:
            # 1. Count potential candidates
            print("Identifying valid records in clean table...")
            total_valid_res = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status = 'VALID'")).fetchone()
            total_valid = total_valid_res[0] if total_valid_res else 0
            
            master_count_res = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).fetchone()
            master_count = master_count_res[0] if master_count_res else 0
            
            print(f"Total VALID records in clean table: {total_valid:,}")
            print(f"Total records in master table     : {master_count:,}")
            print(f"Approximate gap                   : {max(0, total_valid - master_count):,}")
            print("-" * 60)

            # 2. Sync in batches
            offset = 0
            while True:
                # Select batch of valid records
                query = text("""
                    SELECT name, address, website, phone_number, reviews_count, reviews_avg, 
                           category, subcategory, city, state, area, created_at
                    FROM raw_clean_google_map_data
                    WHERE validation_status = 'VALID'
                    LIMIT :limit OFFSET :offset
                """)
                
                rows = conn.execute(query, {"limit": batch_size, "offset": offset}).fetchall()
                if not rows:
                    break
                
                # Prepare for insert
                batch_data = []
                for r in rows:
                    batch_data.append({
                        "name": r[0],
                        "address": r[1],
                        "website": r[2],
                        "phone_number": r[3],
                        "reviews_count": r[4],
                        "reviews_avg": r[5],
                        "category": r[6],
                        "subcategory": r[7],
                        "city": r[8],
                        "state": r[9],
                        "area": r[10],
                        "created_at": r[11]
                    })
                
                # Insert into master
                insert_query = text("""
                    INSERT IGNORE INTO g_map_master_table (
                        name, address, website, phone_number, reviews_count, reviews_avg, 
                        category, subcategory, city, state, area, created_at
                    ) VALUES (
                        :name, :address, :website, :phone_number, :reviews_count, :reviews_avg, 
                        :category, :subcategory, :city, :state, :area, :created_at
                    )
                """)
                
                result = conn.execute(insert_query, batch_data)
                synced_in_batch = result.rowcount
                total_synced += synced_in_batch
                
                offset += batch_size
                elapsed = time.time() - start_time
                if offset % 50000 == 0:
                    print(f"Processed: {offset:,} | Synced New: {total_synced:,} | Time: {elapsed:.1f}s")
                
                # If a batch added 0 records for a while, we might be hitting already synced data, 
                # but since we are iterating through ALL valid records, we continue.
                
            print("\nSync completed successfully.")
            print(f"Total New Records Added to Master: {total_synced:,}")

    except Exception as e:
        print(f"\nError during Gap Sync: {e}")

    print("=" * 60)
    print(f"Total Time Taken: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    perform_gap_sync()
