import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    tables = conn.execute(text("SHOW TABLES")).fetchall()
    print("Tables in database:")
    for t in tables:
        print(f" - {t[0]}")
