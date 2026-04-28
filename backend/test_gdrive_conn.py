import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def test_gdrive():
    SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), "model", "honey-bee-digital-d96daf6e6faf.json")
    ROOT_FOLDER_ID = os.getenv('GDRIVE_ROOT_FOLDER_ID', '1ltTYjekxZsk2CdF20tSk1B2FnRn4119E')
    
    print(f"Using Root Folder: {ROOT_FOLDER_ID}")
    print(f"Using Service Account: {SERVICE_ACCOUNT_FILE}")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
        
        print("Connecting to Google Drive...")
        results = service.files().list(
            q=f"'{ROOT_FOLDER_ID}' in parents and trashed=false",
            pageSize=5,
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        print(f"Successfully fetched {len(files)} files/folders.")
        for f in files:
            print(f" - {f['name']} ({f['id']})")
            
    except Exception as e:
        print(f"Error connecting to GDrive: {e}")

if __name__ == "__main__":
    test_gdrive()
