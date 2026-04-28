import os
import sys
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Add current dir to path for imports
sys.path.insert(0, os.getcwd())

from config import config
from tasks.gdrive_task.etl_tasks import process_csv_task, get_service

def manual_process():
    load_dotenv()
    with open('pending_ids.txt', 'r') as f:
        file_ids = [line.strip() for line in f if line.strip()]
    
    if not file_ids:
        print("No pending IDs found.")
        return

    service = get_service()
    
    print(f"Manually processing {len(file_ids)} files locally (bypassing queue)...")
    
    for file_id in file_ids:
        try:
            # Fetch details from GDrive
            file_meta = service.files().get(fileId=file_id, fields="id, name, modifiedTime, parents").execute()
            
            file_name = file_meta.get('name')
            modified_time = file_meta.get('modifiedTime')
            folder_id = file_meta.get('parents', [None])[0]
            
            print(f"Processing: {file_name} ({file_id})...")
            # Call the function directly (not .delay())
            result = process_csv_task(file_id, file_name, folder_id, None, None, modified_time)
            print(f" -> {result}")
            
        except Exception as e:
            print(f" [!] Error processing {file_id}: {e}")

if __name__ == "__main__":
    manual_process()
