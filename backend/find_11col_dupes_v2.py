from sqlalchemy import create_engine, text
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def find_11col_duplicates_efficiently():
    # We use MD5 of the 11 columns to group them efficiently.
    # Columns: name, address, website, phone_number, reviews_count, reviews_average, category, subcategory, city, state, area
    # CONCAT_WS ignores NULLs if we are not careful, but it's okay for hashing if we use a separator.
    
    query = text("""
        SELECT 
            MD5(CONCAT_WS('|', 
                COALESCE(name, ''), 
                COALESCE(address, ''), 
                COALESCE(website, ''), 
                COALESCE(phone_number, ''), 
                COALESCE(reviews_count, 0), 
                COALESCE(reviews_average, 0.0), 
                COALESCE(category, ''), 
                COALESCE(subcategory, ''), 
                COALESCE(city, ''), 
                COALESCE(state, ''), 
                COALESCE(area, '')
            )) as row_sig,
            COUNT(*) as cnt,
            name, phone_number, city, state,
            GROUP_CONCAT(id ORDER BY id SEPARATOR ',') as ids
        FROM raw_google_map_drive_data
        GROUP BY row_sig
        HAVING cnt > 1
        ORDER BY cnt DESC
        LIMIT 50
    """)
    
    # But wait, GROUP BY on MD5(CONCAT_WS(...)) is STILL a full table scan and compute.
    # On 4.7M rows, this might take 1-2 minutes.
    
    with engine.connect() as conn:
        print("Finding exact 11-column duplicates (hashing on the fly)...")
        conn.execute(text("SET SESSION sql_mode=''")) # Help with group by if needed
        result = conn.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print("No duplicates found.")
            return
            
        print(f"\nFound {len(rows)} duplicate groups (top 50):")
        print("-" * 130)
        print(f"{'Signature':<34} | {'Cnt':<5} | {'Name':<30} | {'Phone':<15} | {'City':<15} | {'IDs'}")
        print("-" * 130)
        
        for r in rows:
            sig = r[0]
            cnt = r[1]
            name = str(r[2])[:30]
            phone = str(r[3])[:15]
            city = str(r[4])[:15]
            ids = str(r[6])[:30] + "..."
            print(f"{sig:<34} | {cnt:<5} | {name:<30} | {phone:<15} | {city:<15} | {ids}")

if __name__ == "__main__":
    find_11col_duplicates_efficiently()
