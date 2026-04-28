import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

pw = quote_plus(os.getenv('DB_PASSWORD_PLAIN'))
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

with engine.connect() as conn:
    print("Searching for the real missing records...")
    # Find records in Clean (VALID) whose unique key (Name, Phone, City, Address) 
    # does NOT exist in the Master table.
    query = text("""
        SELECT c.id, c.name, c.phone_number, c.city, c.address
        FROM raw_clean_google_map_data c
        WHERE c.validation_status = 'VALID'
        AND NOT EXISTS (
            SELECT 1 FROM g_map_master_table m 
            WHERE 
                LEFT(c.name, 100) = LEFT(m.name, 100) AND 
                c.phone_number = m.phone_number AND 
                LEFT(c.city, 50) = LEFT(m.city, 50) AND 
                LEFT(c.address, 100) = LEFT(m.address, 100)
        )
        LIMIT 20
    """)
    missing = conn.execute(query).fetchall()
    
    if not missing:
        print("✅ No missing records found! Every unique business in Clean is already in Master.")
    else:
        print(f"❌ Found {len(missing)} sample records truly missing from Master:")
        for r in missing:
            print(f"ID: {r[0]} | Name: {r[1]} | Phone: {r[2]} | City: {r[3]} | Addr: {r[4][:30]}...")
            
    # Also check the count of how many are logically missing
    print("\nCalculating total missing count...")
    count_query = text("""
        SELECT COUNT(*)
        FROM raw_clean_google_map_data c
        WHERE c.validation_status = 'VALID'
        AND NOT EXISTS (
            SELECT 1 FROM g_map_master_table m 
            WHERE 
                LEFT(c.name, 100) = LEFT(m.name, 100) AND 
                c.phone_number = m.phone_number AND 
                LEFT(c.city, 50) = LEFT(m.city, 50) AND 
                LEFT(c.address, 100) = LEFT(m.address, 100)
        )
    """)
    total_missing = conn.execute(count_query).scalar()
    print(f"Total records that NEED syncing: {total_missing:,}")
