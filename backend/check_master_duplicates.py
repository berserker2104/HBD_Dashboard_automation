from sqlalchemy import create_engine, text
import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())
from config import config

engine = create_engine(config.DATABASE_URI)
with engine.connect() as conn:
    print("🔍 Checking for duplicates in g_map_master_table...")
    
    # Check by the unique business criteria: name, address, phone_number, city
    query = """
        SELECT name, address, phone_number, city, COUNT(*) as count
        FROM g_map_master_table
        GROUP BY name, address, phone_number, city
        HAVING count > 1
        LIMIT 20;
    """
    
    results = conn.execute(text(query)).fetchall()
    
    if not results:
        print("✅ No duplicates found! The unique constraints are working perfectly.")
    else:
        print(f"⚠️ Found {len(results)} groups of possible duplicates (showing top 20):")
        for row in results:
            print(f"  - [{row.count} times] {row.name} | {row.phone_number} | {row.city}")
            
    # Total count in master
    total = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).scalar()
    print(f"\nTotal records in Master Table: {total}")
