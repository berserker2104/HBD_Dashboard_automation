import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Category Levels in product_category_master ===")
    res = conn.execute(text("""
        SELECT marketplace_name, category_level, COUNT(*) 
        FROM product_category_master 
        GROUP BY marketplace_name, category_level
        ORDER BY marketplace_name, category_level
    """)).fetchall()
    for row in res:
        print(f"Marketplace: {row[0]} | Level: {row[1]} | Count: {row[2]}")
        
    print("\n=== Check if there are non-null subcategories or paths ===")
    res = conn.execute(text("""
        SELECT COUNT(*), COUNT(subcategory_name), COUNT(child_category_name), COUNT(category_path)
        FROM product_category_master
        WHERE marketplace_name = 'Amazon'
    """)).fetchone()
    print(f"Total Amazon Rows: {res[0]} | Has Subcategory: {res[1]} | Has ChildCategory: {res[2]} | Has Path: {res[3]}")
    
    # Let's inspect some of those that have subcategory
    res = conn.execute(text("""
        SELECT category_name, subcategory_name, child_category_name, category_path 
        FROM product_category_master 
        WHERE marketplace_name = 'Amazon' AND subcategory_name IS NOT NULL AND subcategory_name != 'None' AND subcategory_name != ''
        LIMIT 10
    """)).fetchall()
    print("\nSample Amazon rows with subcategory:")
    for row in res:
        print(f"Cat: {row[0]} | Subcat: {row[1]} | Child: {row[2]} | Path: {row[3]}")
