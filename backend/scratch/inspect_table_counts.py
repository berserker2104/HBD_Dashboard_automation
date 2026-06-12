import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

tables = [
    'bigbasket', 'blinkit', 'zepto', 'dmart_categories', 
    'indiamart_products', 'product_category_master', 
    'flipkart_products', 'jio_mart_products'
]

with engine.connect() as conn:
    print("=== Table Row Counts ===")
    for table in tables:
        try:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            print(f"Table: {table} | Row Count: {res}")
        except Exception as e:
            print(f"Table: {table} | [ERROR] {e}")
