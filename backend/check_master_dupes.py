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

def check_master_duplicates():
    print(f"Checking for duplicates in g_map_master_table...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        with engine.connect() as conn:
            # 1. Total row count
            total_rows = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).fetchone()[0]
            print(f"Total rows in master table: {total_rows:,}")
            
            if total_rows == 0:
                print("Table is empty.")
                return

            # 2. Check for duplicates based on name, phone, city, address
            # We use a subquery to find duplicate combinations
            query = text("""
                SELECT name, phone_number, city, address, COUNT(*) as cnt
                FROM g_map_master_table
                GROUP BY name, phone_number, city, address
                HAVING cnt > 1
                LIMIT 50
            """)
            
            rows = conn.execute(query).fetchall()
            
            if not rows:
                print("No duplicates found based on name, phone, city, and address.")
            else:
                print(f"Found {len(rows)} duplicate groups (showing first 50):")
                print(f"{'Name':<30} {'Phone':<15} {'City':<15} {'Count':<5}")
                print("-" * 70)
                for r in rows:
                    name = (r[0] or 'N/A')[:28]
                    phone = (r[1] or 'N/A')[:13]
                    city = (r[2] or 'N/A')[:13]
                    print(f"{name:<30} {phone:<15} {city:<15} {r[4]}")
                
                # Get a total count of duplicate groups
                total_dupe_groups = conn.execute(text("""
                    SELECT COUNT(*) FROM (
                        SELECT 1 FROM g_map_master_table
                        GROUP BY name, phone_number, city, address
                        HAVING COUNT(*) > 1
                    ) as t
                """)).fetchone()[0]
                print(f"\nTotal duplicate groups found: {total_dupe_groups:,}")

    except Exception as e:
        print(f"Error checking duplicates: {e}")

    print("-" * 60)
    print(f"Time Taken: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    check_master_duplicates()
