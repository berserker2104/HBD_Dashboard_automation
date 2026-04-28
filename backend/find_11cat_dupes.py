from sqlalchemy import create_engine, text
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def get_duplicates_11_cols():
    query = text("""
        SELECT 
            name, address, website, phone_number, reviews_count, reviews_average, 
            category, subcategory, city, state, area,
            COUNT(*) as duplicate_count,
            GROUP_CONCAT(id ORDER BY id SEPARATOR ', ') as member_ids
        FROM raw_google_map_drive_data
        GROUP BY 
            name, address, website, phone_number, reviews_count, reviews_average, 
            category, subcategory, city, state, area
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC
        LIMIT 100
    """)
    
    # We use COALESCE or similar if any columns can be NULL to ensure GROUP BY treats NULLs together correctly
    # MySQL GROUP BY already treats NULLs as a group.
    
    with engine.connect() as conn:
        print("Searching for exact duplicates across 11 columns...")
        result = conn.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print("No exact duplicates found across all 11 columns.")
            return

        print(f"\nFound {len(rows)} duplicate groups (showing top 100):")
        print("-" * 120)
        print(f"{'Count':<8} | {'Name':<30} | {'Phone':<15} | {'City':<15} | {'IDs'}")
        print("-" * 120)
        
        total_extra = 0
        for row in rows:
            count = row.duplicate_count
            name = str(row.name)[:30] if row.name else "N/A"
            phone = str(row.phone_number)[:15] if row.phone_number else "N/A"
            city = str(row.city)[:15] if row.city else "N/A"
            ids = str(row.member_ids)[:40] + ("..." if len(str(row.member_ids)) > 40 else "")
            
            print(f"{count:<8} | {name:<30} | {phone:<15} | {city:<15} | {ids}")
            total_extra += (count - 1)
            
        print("-" * 120)
        print(f"Total rows to remove to clear these duplicates: {total_extra}")

if __name__ == "__main__":
    get_duplicates_11_cols()
