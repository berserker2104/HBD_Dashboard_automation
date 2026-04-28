import os
import time
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD_PLAIN")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def perform_gap_sync():
    print("Starting Batch Gap Sync: raw_clean_google_map_data -> g_map_master_table")
    print("=" * 60)
    
    start_time = time.time()
    batch_size = 5000
    commit_every = 50000
    total_synced = 0
    
    try:
        # Use connection to manage manual commits
        with engine.connect() as conn:
            # 1. Counts
            total_valid = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status = 'VALID'")).scalar()
            master_count = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).scalar()
            
            print(f"Valid Clean: {total_valid:,} | Master: {master_count:,} | Gap: {max(0, total_valid - master_count):,}")
            
            offset = 0
            while True:
                # 2. Start a transaction for this chunk
                with conn.begin():
                    query = text("""
                        SELECT name, address, website, phone_number, reviews_count, reviews_avg, 
                               category, subcategory, city, state, area, created_at
                        FROM raw_clean_google_map_data
                        WHERE validation_status = 'VALID'
                        LIMIT :limit OFFSET :offset
                    """)
                    
                    rows = conn.execute(query, {"limit": commit_every, "offset": offset}).fetchall()
                    if not rows:
                        break
                    
                    batch_data = []
                    for r in rows:
                        batch_data.append({
                            "name": r[0], "address": r[1], "website": r[2], "phone_number": r[3],
                            "reviews_count": r[4], "reviews_avg": r[5], "category": r[6],
                            "subcategory": r[7], "city": r[8], "state": r[9], "area": r[10],
                            "created_at": r[11]
                        })
                    
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
                    total_synced += result.rowcount
                    
                offset += commit_every
                print(f"Processed: {offset:,} | Total Synced: {total_synced:,} | Elapsed: {time.time()-start_time:.1f}s")
                
            print(f"\n✅ Sync Complete. Total new master rows: {total_synced:,}")

    except Exception as e:
        print(f"\n❌ Gap Sync Error: {e}")

if __name__ == "__main__":
    perform_gap_sync()
