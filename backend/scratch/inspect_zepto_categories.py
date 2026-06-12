import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Columns of zepto_categories ===")
    try:
        res = conn.execute(text("DESCRIBE zepto_categories")).fetchall()
        for col in res:
            print(f"  - {col[0]} ({col[1]})")
            
        print("\n=== Rows count in zepto_categories ===")
        cnt = conn.execute(text("SELECT COUNT(*) FROM zepto_categories")).fetchone()[0]
        print(f"  Total Rows: {cnt}")
        
        if cnt > 0:
            print("\n=== Sample Rows from zepto_categories ===")
            samples = conn.execute(text("SELECT * FROM zepto_categories LIMIT 10")).fetchall()
            for row in samples:
                print(f"  {row}")
    except Exception as e:
        print(f"  [ERROR] {e}")
