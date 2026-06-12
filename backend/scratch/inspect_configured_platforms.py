import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Configured Platforms in Database ===")
    res = conn.execute(text("SELECT id, platform_name, query_sql, is_active FROM category_mapping_platforms")).fetchall()
    for row in res:
        print(f"ID: {row[0]} | Name: {row[1]} | Active: {row[3]}")
        print(f"Query: {row[2][:120]}...")
        print("-" * 50)
