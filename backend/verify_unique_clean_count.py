import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

pw = quote_plus(os.getenv('DB_PASSWORD_PLAIN'))
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

with engine.connect() as conn:
    print("Checking unique business count in Clean table (VALID records only)...")
    # We use name(100), city(50), address(100) to match the unique index length
    query = text("""
        SELECT COUNT(DISTINCT LEFT(name, 100), phone_number, LEFT(city, 50), LEFT(address, 100))
        FROM raw_clean_google_map_data
        WHERE validation_status = 'VALID'
    """)
    unique_count = conn.execute(query).scalar()
    
    master_count = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).scalar()
    
    print(f"Total VALID records in Clean        : {conn.execute(text('SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status=\"VALID\"')).scalar():,}")
    print(f"Unique businesses in Clean (VALID)  : {unique_count:,}")
    print(f"Total records in Master             : {master_count:,}")
    print(f"Gap between Unique Clean and Master : {unique_count - master_count:,}")
