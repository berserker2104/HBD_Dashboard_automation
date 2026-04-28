import os
import sys
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Add current dir to path for imports
sys.path.insert(0, os.getcwd())

from config import config
from tasks.gdrive_task.etl_tasks import get_service, process_csv_task

def force_retry_pending():
    load_dotenv()
    engine = create_engine(config.DATABASE_URI)
    service = get_service()
    
    with engine.connect() as conn:
        print("Finding PENDING files in registry...")
        pending_files = conn.execute(text("SELECT drive_file_id, filename, drive_folder_id FROM file_registry WHERE status='PENDING'")).fetchall()
        
        if not pending_files:
            print("No PENDING files found.")
            return

        print(f"Found {len(pending_files)} files. Fetching metadata and submitting tasks...")
        
        count = 0
        for file_id, filename, folder_id in pending_files:
            try:
                # Fetch details from Google Drive to get modifiedTime
                file_meta = service.files().get(fileId=file_id, fields="id, name, modifiedTime, parents").execute()
                
                modified_time = file_meta.get('modifiedTime')
                file_name = file_meta.get('name') or filename
                f_id = file_meta.get('parents', [folder_id])[0]
                
                # Submit to worker
                process_csv_task.delay(file_id, file_name, f_id, None, None, modified_time)
                print(f" [+] Submitted: {file_name}")
                count += 1
            except Exception as e:
                print(f" [!] Error fetching {filename} ({file_id}): {e}")
        
        print(f"\nSuccessfully submitted {count} files for re-processing.")

if __name__ == "__main__":
    force_retry_pending()
