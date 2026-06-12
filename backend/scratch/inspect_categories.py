import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Category Counts by Level ===")
    res = conn.execute(text("SELECT level, COUNT(*) FROM master_categories GROUP BY level")).fetchall()
    for row in res:
        print(f"Level {row[0]}: {row[1]}")
    
    print("\n=== Level 3 & 4 Samples ===")
    res = conn.execute(text("SELECT id, name, level, parent_id, path FROM master_categories WHERE level >= 3 LIMIT 20")).fetchall()
    for row in res:
        print(f"ID: {row[0]} | Name: {row[1]} | Level: {row[2]} | Parent ID: {row[3]} | Path: {row[4]}")
