import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD_PLAIN','') or '')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

def check_specific():
    with engine.connect() as conn:
        print("--- Specific File Status ---")
        filenames = ['Printing_and_Publishing_Services.csv', 'Local_ATM_Locations.csv', 'Beauty_Spa.csv']
        for fn in filenames:
            res = conn.execute(text("SELECT drive_file_id, status, error_message FROM file_registry WHERE filename = :fn"), {"fn": fn}).fetchall()
            print(f"File: {fn} | Rows: {len(res)}")
            for row in res:
                print(f"  ID: {row[0]} | Status: {row[1]} | Error: {row[2]}")

if __name__ == "__main__":
    check_specific()
