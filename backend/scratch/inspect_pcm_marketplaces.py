import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Marketplaces in product_category_master ===")
    res = conn.execute(text("""
        SELECT marketplace_name, COUNT(*) 
        FROM product_category_master 
        GROUP BY marketplace_name
    """)).fetchall()
    for row in res:
        print(f"Marketplace: {row[0]} | Row Count: {row[1]}")
