from sqlalchemy import create_engine, text
import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())
from config import config

engine = create_engine(config.DATABASE_URI)
with engine.connect() as conn:
    print("📋 TABLES IN DB:")
    for table in conn.execute(text("SHOW TABLES")).fetchall():
        print(f"  {table[0]}")
    
    folders = conn.execute(text("SELECT COUNT(*) FROM drive_folder_registry")).scalar()
    files_total = conn.execute(text("SELECT COUNT(*) FROM file_registry")).scalar()
    files_processed = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status = 'PROCESSED'")).scalar()
    files_error = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status = 'ERROR'")).scalar()
    files_pending = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status = 'PENDING'")).scalar()
    
    print(f"Folders registered: {folders}")
    print(f"Files in registry: {files_total}")
    print(f"  - PROCESSED: {files_processed}")
    print(f"  - ERROR: {files_error}")
    print(f"  - PENDING: {files_pending}")
    
    raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).scalar()
    clean_count = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data")).scalar()
    master_count = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).scalar()
    print(f"Total Raw Rows: {raw_count}")
    print(f"Total Clean Rows: {clean_count}")
    print(f"Total Master Rows: {master_count}")

    with_folder_id = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE drive_folder_id IS NOT NULL")).scalar()
    print(f"\nFiles with drive_folder_id: {with_folder_id}")

    print("\nETL Metadata:")
    for row in conn.execute(text("SELECT * FROM etl_metadata")).fetchall():
        print(f"  {row}")

    print("\nIndexes in raw_google_map_drive_data:")
    for idx in conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data")).fetchall():
        print(f"  {idx}")
