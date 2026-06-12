import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Amazon Category Columns Sample ===")
    res = conn.execute(text("""
        SELECT category_name, subcategory_name, child_category_name, category_level, category_path
        FROM product_category_master
        WHERE marketplace_name = 'Amazon' AND category_name IS NOT NULL AND category_name != ''
        LIMIT 25
    """)).fetchall()
    for row in res:
        print(f"Cat: {row[0]} | Subcat: {row[1]} | ChildCat: {row[2]} | Lvl: {row[3]} | Path: {row[4]}")
