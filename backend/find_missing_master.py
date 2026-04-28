import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

pw = quote_plus(os.getenv('DB_PASSWORD_PLAIN'))
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

with engine.connect() as conn:
    print("Finding records that exist in Clean (VALID) but are missing from Master...")
    # This query finds records in Clean that don't have a matching record in Master
    # based on the unique key definition.
    query = text("""
        SELECT c.name, c.phone_number, c.city, c.address
        FROM raw_clean_google_map_data c
        LEFT JOIN g_map_master_table m ON 
            LEFT(c.name, 100) = LEFT(m.name, 100) AND 
            c.phone_number = m.phone_number AND 
            LEFT(c.city, 50) = LEFT(m.city, 50) AND 
            LEFT(c.address, 100) = LEFT(m.address, 100)
        WHERE c.validation_status = 'VALID'
        AND m.id IS NULL
        LIMIT 10
    """)
    missing = conn.execute(query).fetchall()
    
    if not missing:
        print("No missing records found! They might all be duplicates.")
    else:
        print(f"Found {len(missing)} missing samples:")
        for r in missing:
            print(f" - {r[0]} | {r[1]} | {r[2]} | {r[3][:30]}...")
