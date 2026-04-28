from sqlalchemy import create_engine, text
import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())
from config import config

engine = create_engine(config.DATABASE_URI)
with engine.begin() as conn:
    print("🚀 Attempting to create UNIQUE INDEX idx_row_signature on raw_google_map_drive_data...")
    try:
        # First check for existing duplicates
        dupes = conn.execute(text("""
            SELECT row_signature, COUNT(*) as count 
            FROM raw_google_map_drive_data 
            WHERE row_signature IS NOT NULL 
            GROUP BY row_signature 
            HAVING count > 1 
            LIMIT 5
        """)).fetchall()
        
        if dupes:
            print("❌ CANNOT CREATE UNIQUE INDEX: The following signatures already have duplicates:")
            for d in dupes:
                print(f"  - {d.row_signature} ({d.count} times)")
            print("\nSuggesting: Clean the table before applying the unique constraint.")
        else:
            conn.execute(text("CREATE UNIQUE INDEX idx_row_signature ON raw_google_map_drive_data(row_signature)"))
            print("✅ UNIQUE INDEX created successfully!")
            
    except Exception as e:
        print(f"❌ Error during index creation: {e}")
