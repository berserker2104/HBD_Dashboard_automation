import os
import time
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Database setup
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD_PLAIN") # Using plain if available
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def check_master_11col_duplicates():
    print(f"Checking for EXACT 11-column duplicates in g_map_master_table...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        with engine.connect() as conn:
            # Check for duplicates based on all 11 business columns
            query = text("""
                SELECT name, address, website, phone_number, reviews_count, reviews_avg, category, subcategory, city, state, area, COUNT(*) as cnt
                FROM g_map_master_table
                GROUP BY name, address, website, phone_number, reviews_count, reviews_avg, category, subcategory, city, state, area
                HAVING cnt > 1
                LIMIT 50
            """)
            
            rows = conn.execute(query).fetchall()
            
            if not rows:
                print("No exact 11-column duplicates found.")
            else:
                print(f"Found {len(rows)} exact 11-column duplicate groups (showing first 50):")
                # Summarize counts
                total_dupe_groups = conn.execute(text("""
                    SELECT COUNT(*) FROM (
                        SELECT 1 FROM g_map_master_table
                        GROUP BY name, address, website, phone_number, reviews_count, reviews_avg, category, subcategory, city, state, area
                        HAVING COUNT(*) > 1
                    ) as t
                """)).fetchone()[0]
                print(f"Total duplicate groups: {total_dupe_groups:,}")

    except Exception as e:
        print(f"Error checking duplicates: {e}")

    print("-" * 60)
    print(f"Time Taken: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    check_master_11col_duplicates()
