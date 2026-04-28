import os
import sys
import time

_backend_dir = os.path.dirname(__file__)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config import config
from sqlalchemy import create_engine, text

def check_status():
    engine = create_engine(config.DATABASE_URI)
    try:
        with engine.connect() as conn:
            # Folder Stats
            total_folders = conn.execute(text("SELECT COUNT(*) FROM drive_folder_registry")).scalar()
            done_folders = conn.execute(text("SELECT COUNT(*) FROM drive_folder_registry WHERE status='DONE'")).scalar()
            pending_folders = total_folders - done_folders
            
            # File Stats
            processed_files = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status='PROCESSED'")).scalar()
            pending_files = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status='PENDING'")).scalar()
            total_files = processed_files + pending_files
            
            # Row Stats
            raw_rows = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).scalar()
            master_rows = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).scalar()
            
            # Validation Pipeline Stats
            try:
                # Use the clean table as the processing state source now
                val_total = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data")).scalar()
                val_valid = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status='VALID'")).scalar()
                val_missing = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status='MISSING'")).scalar()
                val_dup = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status='DUPLICATE'")).scalar()
                val_invalid = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data WHERE validation_status='INVALID'")).scalar()
                
                last_id_res = conn.execute(text("SELECT meta_value FROM etl_metadata WHERE meta_key='last_processed_id'")).scalar()
                last_id = int(last_id_res) if last_id_res and str(last_id_res).isdigit() else 0
                max_id = conn.execute(text("SELECT MAX(id) FROM raw_google_map_drive_data")).scalar() or 0
            except Exception as e:
                print(f"DEBUG: Status fetch error: {e}")
                val_total = val_valid = val_missing = val_dup = val_invalid = 0
                last_id = max_id = 0
            
            print("\n" + "="*50)
            print(" 📊 GDRIVE AUTOMATION STATUS REPORT ")
            print("="*50)
            print(f"📁 FOLDERS:")
            print(f"   Registered: {total_folders:,}")
            print(f"   Processed:  {done_folders:,}")
            print(f"   Remaining:  {pending_folders:,}")
            print("-" * 50)
            print(f"📄 CSV FILES:")
            print(f"   Registered: {total_files:,}")
            print(f"   Processed:  {processed_files:,}")
            print(f"   Remaining:  {pending_files:,}")
            print("-" * 50)
            print(f"💾 DATA ROWS:")
            print(f"   Raw Ingested: {raw_rows:,}")
            print(f"   Master Valid: {master_rows:,}")
            print("-" * 50)
            pct = (int(last_id or 0) / max_id * 100) if max_id > 0 else 0
            remaining_rows = max(0, raw_rows - (val_total if val_total else 0))
            print(f"⚙️  VALIDATION PIPELINE:")
            print(f"   Processed:   {val_total:,} / {raw_rows:,} ({pct:.1f}%)")
            print(f"   Remaining:   {remaining_rows:,}")
            print(f"   Valid:       {val_valid:,}")
            print(f"   Missing:     {val_missing:,}")
            print(f"   Duplicate:   {val_dup:,}")
            print(f"   Invalid:     {val_invalid:,}")
            print(f"   Last ID:     {last_id:,} / {max_id:,}")
            print("="*50 + "\n")
            
    except Exception as e:
        print(f"Error fetching status: {e}")

if __name__ == "__main__":
    check_status()
