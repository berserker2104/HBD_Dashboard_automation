from sqlalchemy import create_engine, text
import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())
from config import config

engine = create_engine(config.DATABASE_URI)
with engine.connect() as conn:
    print("🔍 VERIFYING INDEX: idx_row_signature...")
    idx_check = conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data WHERE Key_name = 'idx_row_signature'")).fetchone()
    if idx_check:
        print("✅ UNIQUE INDEX 'idx_row_signature' is ACTIVE.")
    else:
        print("❌ WARNING: UNIQUE INDEX 'idx_row_signature' is MISSING!")

    print("\n🔍 Checking for EXACT duplicates in raw_google_map_drive_data (all 11 columns)...")
    
    # Check by row_signature (which is MD5 of all 11 columns)
    query = """
        SELECT row_signature, COUNT(*) as count
        FROM raw_google_map_drive_data
        WHERE row_signature IS NOT NULL
        GROUP BY row_signature
        HAVING count > 1
        LIMIT 20;
    """
    
    results = conn.execute(text(query)).fetchall()
    
    if not results:
        print("✅ No exact duplicates found! The row_signature unique constraint is working.")
    else:
        print(f"⚠️ Found {len(results)} groups of exact duplicates (showing top 20):")
        for row in results:
            print(f"  - Signature [{row.row_signature}] appears {row.count} times")
            
    # Also check for rows WITHOUT a signature (to see if migration is needed)
    no_sig = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data WHERE row_signature IS NULL")).scalar()
    if no_sig > 0:
        print(f"ℹ️ Note: {no_sig} rows are missing a row_signature. These might be old records.")

    # Total count in raw
    total = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).scalar()
    print(f"\nTotal records in Raw Table: {total}")
