import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

checks = [
    ('bigbasket', 'main_category'),
    ('bigbasket', 'subcategory'),
    ('blinkit', 'category'),
    ('blinkit', 'sub_category'),
    ('zepto', 'main_category'),
    ('zepto', 'subcategory'),
    ('indiamart_products', 'category_name'),
    ('indiamart_products', 'sub_category_name')
]

with engine.connect() as conn:
    print("=== Checking for ' > ' Delimiters in Raw Tables ===")
    for table, col in checks:
        try:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE `{col}` LIKE '% > %'")).fetchone()[0]
            print(f"Table: {table} | Column: {col} | Rows with ' > ': {res}")
            if res > 0:
                samples = conn.execute(text(f"SELECT DISTINCT `{col}` FROM {table} WHERE `{col}` LIKE '% > %' LIMIT 5")).fetchall()
                print("  Samples:")
                for s in samples:
                    print(f"    - {s[0]}")
        except Exception as e:
            print(f"Table: {table} | Column: {col} | [ERROR] {e}")
