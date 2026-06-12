import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Mappings by Master Category Level ===")
    res = conn.execute(text("""
        SELECT mc.level, COUNT(*) 
        FROM platform_category_mapping pcm
        JOIN master_categories mc ON pcm.master_category_id = mc.id
        GROUP BY mc.level
    """)).fetchall()
    for row in res:
        print(f"Level {row[0]}: {row[1]} mappings")
        
    print("\n=== Mappings count by Status ===")
    res = conn.execute(text("SELECT mapping_status, COUNT(*) FROM platform_category_mapping GROUP BY mapping_status")).fetchall()
    for row in res:
        print(f"Status {row[0]}: {row[1]}")
        
    print("\n=== Sample Mappings to Level 3 & 4 ===")
    res = conn.execute(text("""
        SELECT pcm.platform_name, pcm.platform_category_raw, pcm.platform_subcategory_raw, mc.name, mc.level, mc.path, pcm.mapping_status
        FROM platform_category_mapping pcm
        JOIN master_categories mc ON pcm.master_category_id = mc.id
        WHERE mc.level >= 3
        LIMIT 10
    """)).fetchall()
    for row in res:
        print(f"Platform: {row[0]} | Raw Cat: {row[1]} | Subcat: {row[2]} | Mapped To: {row[3]} (L{row[4]}) | Path: {row[5]} | Status: {row[6]}")
