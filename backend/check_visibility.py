import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import urllib.parse
from model.robust_gdrive_etl_v2 import GDriveHighSpeedIngestor

load_dotenv()

def check_visibility():
    ingestor = GDriveHighSpeedIngestor()
    ingestor.load_registry()
    
    print(f"Loaded {len(ingestor.folder_registry)} folders from registry.")
    
    with ingestor.engine.connect() as conn:
        error_files = conn.execute(text("SELECT drive_file_id, filename, drive_folder_id FROM file_registry WHERE status='ERROR' LIMIT 5")).fetchall()
        print("\n--- Files in ERROR status (to be picked up) ---")
        for f in error_files:
            fid, name, folder_id = f
            print(f"File: {name} ({fid}) in Folder: {folder_id}")
            
            # Check if ingestor would skip this folder
            if folder_id in ingestor.folder_registry:
                print(f"  [BUG] Ingestor WILL SKIP this folder because it is in the registry!")
            else:
                print(f"  Ingestor will scan this folder.")

if __name__ == "__main__":
    check_visibility()
