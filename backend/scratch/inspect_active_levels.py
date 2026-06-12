import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Active vs Inactive Counts by Level ===")
    res = conn.execute(text("""
        SELECT level, is_active, COUNT(*) 
        FROM master_categories 
        GROUP BY level, is_active
        ORDER BY level, is_active
    """)).fetchall()
    for row in res:
        status = "Active" if row[1] else "Inactive"
        print(f"Level {row[0]} ({status}): {row[2]}")
