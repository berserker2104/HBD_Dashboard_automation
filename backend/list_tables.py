import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

pw = quote_plus(os.getenv('DB_PASSWORD_PLAIN'))
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}")

with engine.connect() as conn:
    tables = conn.execute(text("SHOW TABLES")).fetchall()
    print("Tables in database:")
    for t in tables:
        print(f" - {t[0]}")
