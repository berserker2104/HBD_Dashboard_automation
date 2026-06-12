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
    print("=== Table Columns Inspection ===")
    for table in tables:
        try:
            print(f"\nTable: {table}")
            res = conn.execute(text(f"DESCRIBE {table}")).fetchall()
            for col in res:
                col_name = col[0]
                col_type = col[1]
                # Print columns related to category, type, group, hierarchy
                col_lower = col_name.lower()
                if any(x in col_lower for x in ['cat', 'type', 'group', 'class', 'path', 'level']):
                    print(f"  - {col_name} ({col_type})")
        except Exception as e:
            print(f"  [ERROR] Could not describe {table}: {e}")
