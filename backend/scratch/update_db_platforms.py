import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config
from app import app
from extensions import db
from services.category_sync_service import sync_all_platforms, merge_duplicate_master_categories

# Define the new queries
new_queries = {
    'Amazon': """
        SELECT DISTINCT category_path AS category, NULL AS subcategory
        FROM product_category_master
        WHERE marketplace_name = 'Amazon' AND category_path IS NOT NULL AND category_path != ''
    """,
    'BigBasket': """
        SELECT DISTINCT category_path AS category, NULL AS subcategory
        FROM product_category_master
        WHERE marketplace_name = 'BigBasket' AND category_path IS NOT NULL AND category_path != ''
    """,
    'Blinkit': """
        SELECT DISTINCT category_path AS category, NULL AS subcategory
        FROM product_category_master
        WHERE marketplace_name = 'Blinkit' AND category_path IS NOT NULL AND category_path != ''
    """,
    'IndiaMart': """
        SELECT DISTINCT category_path AS category, NULL AS subcategory
        FROM product_category_master
        WHERE marketplace_name = 'IndiaMART' AND category_path IS NOT NULL AND category_path != ''
    """
}

with app.app_context():
    print("=== Updating Database Platform Queries ===")
    for platform, sql_query in new_queries.items():
        # Clean query: strip trailing/leading spaces and newlines
        sql_query = sql_query.strip()
        
        # Check if platform exists
        res = db.session.execute(
            text("SELECT id FROM category_mapping_platforms WHERE platform_name = :name"),
            {"name": platform}
        ).fetchone()
        
        if res:
            print(f"Updating query for platform '{platform}'...")
            db.session.execute(
                text("UPDATE category_mapping_platforms SET query_sql = :query WHERE platform_name = :name"),
                {"query": sql_query, "name": platform}
            )
        else:
            print(f"Platform '{platform}' not found in database, creating record...")
            db.session.execute(
                text("INSERT INTO category_mapping_platforms (platform_name, query_sql, is_active) VALUES (:name, :query, 1)"),
                {"name": platform, "query": sql_query}
            )
            
    db.session.commit()
    print("Database platform queries updated successfully!")
    
    print("\n=== Running Full Platform Synchronization ===")
    results = sync_all_platforms()
    print("Full Synchronization Completed!")
    print("\nDiscovery results:")
    for platform, res in results['discovery'].items():
        print(f"  {platform}: {res}")
        
    print("\nAuto-mapping results:")
    print(f"  {results['auto_mapping']}")
    
    # Merge any duplicate master categories
    merge_duplicate_master_categories()
