import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def list_tables():
    host = os.getenv('REPORT_DB_HOST', '77.42.78.20')
    user = os.getenv('REPORT_DB_USER', 'mukesh')
    password = os.getenv('REPORT_DB_PASSWORD', 'xVUHAaORqSxG0oYPtMJm')
    db = os.getenv('REPORT_DB_NAME', 'genuinedashboardtest')
    
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db,
            connect_timeout=10
        )
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"Tables in {db}:")
            for table in tables:
                print(f"- {table[0]}")
                
            # Check for dashboard_summary specifically
            cursor.execute("SHOW TABLES LIKE 'dashboard_summary'")
            if cursor.fetchone():
                print("\n'dashboard_summary' table EXISTS.")
                cursor.execute("DESCRIBE dashboard_summary")
                columns = cursor.fetchall()
                print("Columns in 'dashboard_summary':")
                for col in columns:
                    print(f"  {col[0]} ({col[1]})")
            else:
                print("\n'dashboard_summary' table DOES NOT exist.")
    except Exception as e:
        print(f"Error connecting to database: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    list_tables()
