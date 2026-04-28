import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Database setup
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD_PLAIN")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

pw = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def get_pending_counts():
    print("ETL PIPELINE STATUS OVERVIEW")
    print("=" * 60)
    
    with engine.connect() as conn:
        # 1. File Registry Status
        print("\n[ File Processing Status (file_registry) ]")
        file_stats = conn.execute(text("SELECT status, COUNT(*) FROM file_registry GROUP BY status")).fetchall()
        for status, count in file_stats:
            print(f"- {status:<15}: {count:,}")
        
        # 2. Folder Registry Status
        print("\n[ Folder Scan Status (drive_folder_registry) ]")
        folder_stats = conn.execute(text("SELECT status, COUNT(*) FROM drive_folder_registry GROUP BY status")).fetchall()
        for status, count in folder_stats:
            print(f"- {status:<15}: {count:,}")

        # 3. Overall Record Counts
        print("\n[ Table Statistics ]")
        raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).fetchone()[0]
        master_count = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).fetchone()[0]
        print(f"- Raw Records (Total)    : {raw_count:,}")
        print(f"- Master Records (Total) : {master_count:,}")

        # 4. Cleanup Layer (Clean Table Status)
        # Checking if raw_clean_google_map_data table exists and its validation status
        try:
            clean_stats = conn.execute(text("SELECT validation_status, COUNT(*) FROM raw_clean_google_map_data GROUP BY validation_status")).fetchall()
            print("\n[ Cleaning Layer (raw_clean_google_map_data) ]")
            for status, count in clean_stats:
                print(f"- {status:<15}: {count:,}")
        except Exception:
            print("\n[ Cleaning Layer ]: Table raw_clean_google_map_data might not be in use or empty.")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    get_pending_counts()
