import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

def count_pending():
    load_dotenv()
    engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")
    
    with engine.connect() as conn:
        # Check folders status
        try:
            folder_stats = conn.execute(text("SELECT status, COUNT(*) FROM drive_folder_registry GROUP BY status")).fetchall()
            print("--- Folder Registry Statuses ---")
            for status, count in folder_stats:
                print(f" {status}: {count}")
        except:
            print("--- Folder Registry: Table not found ---")

        # Check file_registry statuses
        try:
            results = conn.execute(text("SELECT status, COUNT(*) as count FROM file_registry GROUP BY status")).fetchall()
            print("\n--- File Registry Statuses ---")
            for row in results:
                print(f"{row[0]}: {row[1]}")
        except:
            print("\n--- File Registry: Table not found ---")
            
        # Check detailed table counts
        tables_to_check = [
            "raw_google_map_drive_data",
            "raw_clean_google_map_data",
            "master_table",
            "listing_master_table",
            "g_map_master_table"
        ]
        print("\n--- Detailed Table Counts ---")
        for table in tables_to_check:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
                print(f" {table}: {count:,}")
            except:
                print(f" {table}: Error/Missing")

        # Check ETL Metadata
        try:
            meta = conn.execute(text("SELECT * FROM etl_metadata")).fetchall()
            print("\n--- ETL Metadata ---")
            for row in meta:
                print(f" {row}")
        except:
            print("\n--- ETL Metadata: No metadata table found or empty ---")

if __name__ == "__main__":
    count_pending()
