from database.session import SessionLocal
from sqlalchemy import text

def check_counts():
    session = SessionLocal()
    tables = [
        'asklaila', 'atm', 'bank', 'college_dunia', 'justdial', 
        'magicpin', 'nearbuy', 'pinda', 'post_office', 'schoolgis', 
        'shiksha', 'yellow_pages', 'amazon_products', 'bigbasket',
        'blinkit', 'dmart_products', 'jio_mart_products', 'upload_data_query',
        'zepto', 'zomato', 'vivo', 'item_data', 'master_table'
    ]
    
    results = {}
    for t in tables:
        try:
            # Check if table exists
            exists = session.execute(text(f"SHOW TABLES LIKE '{t}'")).fetchone()
            if exists:
                count = session.execute(text(f"SELECT COUNT(*) FROM `{t}`")).fetchone()[0]
                results[t] = count
            else:
                results[t] = "Table not found"
        except Exception as e:
            results[t] = f"Error: {str(e)}"
    
    session.close()
    
    for table, stat in results.items():
        print(f"{table}: {stat}")

if __name__ == "__main__":
    check_counts()
