import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Mappings Count by Platform ===")
    res = conn.execute(text("SELECT platform_name, COUNT(*) FROM platform_category_mapping GROUP BY platform_name")).fetchall()
    for row in res:
        print(f"Platform: {row[0]} | Total Mappings: {row[1]}")
        
    print("\n=== Mappings with level detail per Platform ===")
    res = conn.execute(text("""
        SELECT pcm.platform_name, mc.level, COUNT(*)
        FROM platform_category_mapping pcm
        LEFT JOIN master_categories mc ON pcm.master_category_id = mc.id
        GROUP BY pcm.platform_name, mc.level
        ORDER BY pcm.platform_name, mc.level
    """)).fetchall()
    for row in res:
        level_str = f"L{row[1]}" if row[1] is not None else "UNMAPPED"
        print(f"Platform: {row[0]} | Master Level: {level_str} | Count: {row[2]}")
