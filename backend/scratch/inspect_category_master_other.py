import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

marketplaces = ['BigBasket', 'Blinkit', 'IndiaMART']

with engine.connect() as conn:
    print("=== Samples from product_category_master ===")
    for m in marketplaces:
        print(f"\nMarketplace: {m}")
        res = conn.execute(text(f"""
            SELECT category_name, subcategory_name, child_category_name, category_level, category_path
            FROM product_category_master
            WHERE marketplace_name = :m AND category_path IS NOT NULL AND category_path != ''
            LIMIT 10
        """), {"m": m}).fetchall()
        for row in res:
            print(f"  Cat: {row[0]} | Subcat: {row[1]} | Child: {row[2]} | Lvl: {row[3]} | Path: {row[4]}")
