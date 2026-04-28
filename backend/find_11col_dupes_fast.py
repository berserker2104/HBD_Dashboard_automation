import os
import hashlib
import time
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Database setup
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def find_exact_duplicates_batch_wise():
    # Columns to check for exact same
    cols = [
        "name", "address", "website", "phone_number", 
        "reviews_count", "reviews_average", "category", 
        "subcategory", "city", "state", "area"
    ]
    
    query_cols = ", ".join(cols)
    
    # We'll use a dictionary to track signatures
    # Key: MD5 hash of 11 columns, Value: Count
    signatures = {}
    
    batch_size = 50000
    total_processed = 0
    duplicate_groups = 0
    total_duplicate_rows = 0
    
    start_time = time.time()
    
    print(f"Starting exact 11-column duplicate check for table: raw_google_map_drive_data")
    print(f"Columns: {query_cols}")
    print("-" * 80)

    try:
        with engine.connect() as conn:
            # Get max ID for chunking
            res = conn.execute(text("SELECT MIN(id), MAX(id) FROM raw_google_map_drive_data")).fetchone()
            min_id, max_id = res[0], res[1]
            
            if min_id is None:
                print("Table is empty.")
                return

            current_id = min_id
            while current_id <= max_id:
                # Fetch batch
                query = text(f"""
                    SELECT id, {query_cols}
                    FROM raw_google_map_drive_data
                    WHERE id >= :start AND id < :end
                """)
                rows = conn.execute(query, {"start": current_id, "end": current_id + batch_size}).fetchall()
                
                if not rows:
                    current_id += batch_size
                    continue

                for row in rows:
                    # Construct a unique string for the 11 columns
                    # We use a separator to avoid collisions
                    vals = [str(val).strip() if val is not None else "" for val in row[1:]]
                    sig_str = "|".join(vals)
                    sig_hash = hashlib.md5(sig_str.encode('utf-8', errors='ignore')).hexdigest()
                    
                    if sig_hash in signatures:
                        if signatures[sig_hash] == 1:
                            duplicate_groups += 1
                        signatures[sig_hash] += 1
                        total_duplicate_rows += 1
                    else:
                        signatures[sig_hash] = 1
                
                total_processed += len(rows)
                current_id += batch_size
                
                # Feedback every batch
                elapsed = time.time() - start_time
                print(f"Processed: {total_processed:,} | Dupe Groups: {duplicate_groups:,} | Extra Dupe Rows: {total_duplicate_rows:,} | Time: {elapsed:.1f}s")

    except Exception as e:
        print(f"Error during processing: {e}")
        return

    end_time = time.time()
    duration = end_time - start_time
    
    print("-" * 80)
    print(f"FINAL RESULT:")
    result_text = (
        f"Total Rows Processed:   {total_processed:,}\n"
        f"Unique Records:         {len(signatures):,}\n"
        f"Duplicate Groups:       {duplicate_groups:,}\n"
        f"Total Extra Dupe Rows:  {total_duplicate_rows:,}\n"
        f"Total Time Taken:       {duration:.1f} seconds\n"
        f"Efficiency:            {total_processed / duration:.0f} rows/sec\n"
    )
    print(result_text)
    print("-" * 80)
    
    with open("find_11col_dupes_result.txt", "w", encoding="utf-8") as f:
        f.write("-" * 80 + "\n")
        f.write("FINAL RESULT:\n")
        f.write(result_text)
        f.write("-" * 80 + "\n")

if __name__ == "__main__":
    find_exact_duplicates_batch_wise()
