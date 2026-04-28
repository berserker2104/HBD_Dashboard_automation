import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

pw = quote_plus(os.getenv('DB_PASSWORD_PLAIN'))
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

with engine.connect() as conn:
    g_map_master = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).scalar()
    master = conn.execute(text("SELECT COUNT(*) FROM master_table")).scalar()
    clean_valid = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status='VALID'")).scalar()
    
    print(f"CLEAN (Valid only)   : {clean_valid:,}")
    print(f"g_map_master_table   : {g_map_master:,}")
    print(f"master_table         : {master:,}")
    print(f"Gap (Clean vs GMap)  : {clean_valid - g_map_master:,}")
