"""
🛠️ DATABASE MAINTENANCE: Apply 4-Field Unique Constraints & Reset Pipeline
logic: (name, phone, city, address)
"""
from sqlalchemy import create_engine, text
import urllib.parse, os, time
from dotenv import load_dotenv

load_dotenv()
pw = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "darshit@1912"))
user = os.getenv("DB_USER", "local_dashboard")
host = os.getenv("DB_HOST", "127.0.0.1")
db = os.getenv("DB_NAME", "local_dashboard")
port = os.getenv("DB_PORT", "3306")

engine = create_engine(
    f"mysql+pymysql://{user}:{pw}@{host}:{port}/{db}?charset=utf8mb4",
    connect_args={"read_timeout": 600, "write_timeout": 600}
)

def apply_new_constraints():
    print(f"🚀 Updating Unique Constraints to (Name, Phone, City, Address)...")
    start_time = time.time()
    
    with engine.begin() as conn:
        conn.execute(text("SET SESSION sql_mode=''"))
        
        # 1. Update raw_clean_google_map_data
        print("📊 Updating raw_clean_google_map_data index...")
        try:
            conn.execute(text("ALTER TABLE raw_clean_google_map_data DROP INDEX idx_composite_dedup"))
        except: pass
        conn.execute(text("""
            ALTER TABLE raw_clean_google_map_data 
            ADD UNIQUE INDEX idx_composite_dedup (name(100), phone_number, city(50), address(100))
        """))

        # 2. Update g_map_master_table
        print("📊 Updating g_map_master_table index...")
        try:
            conn.execute(text("ALTER TABLE g_map_master_table DROP INDEX idx_unique_business"))
        except: pass
        conn.execute(text("""
            ALTER TABLE g_map_master_table 
            ADD UNIQUE INDEX idx_unique_business (name(100), phone_number, city(50), address(100))
        """))

        # 3. Reset Pipeline Progress to re-evaluate data
        print("🔄 Resetting ETL pipeline progress to 0 (Full Re-scan)...")
        conn.execute(text("UPDATE etl_metadata SET meta_value = '0' WHERE meta_key = 'last_processed_id'"))
        
        print("🗑️ Resetting processed states...")
        # Note: We keep raw_clean_google_map_data and g_map_master_table.
        # The pipeline will now skip them if they are duplicates of existing rows, 
        # or fail to insert them if they are already there (UPSERT/IGNORE logic).

    duration = time.time() - start_time
    print(f"✨ SUCCESS! Constraints applied and pipeline reset in {duration:.2f}s.")

if __name__ == "__main__":
    try:
        apply_new_constraints()
    except Exception as e:
        print(f"❌ Maintenance failed: {e}")
