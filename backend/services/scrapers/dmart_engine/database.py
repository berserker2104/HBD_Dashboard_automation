# ============================================================
# DMart Web Scraper — Database Manager Module
# ============================================================
# Handles all SQLite operations: schema creation, category
# hierarchy management, and product UPSERT (duplicate prevention).
# Implements context manager protocol for safe teardown.
# ============================================================

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import csv

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Enterprise-grade SQLite database manager for DMart product data.
    
    Features:
        - Schema creation from external .sql file
        - Category hierarchy (3-level tree with parent_id FK)
        - Product UPSERT: INSERT new / UPDATE existing by sku_id
        - Batch insert with transaction support
        - Context manager for safe connection teardown
    
    Usage:
        with DatabaseManager('dmart_master.db', 'schema.sql') as db:
            cat_id = db.upsert_category('Grocery', 'grocery', None, 1)
            db.upsert_product({...}, cat_id)
    """

    def __init__(self, db_path: str, schema_path: Optional[str] = None):
        """
        Initialize database connection and create schema if needed.
        
        Args:
            db_path: Path to SQLite database file.
            schema_path: Path to .sql schema file (optional).
        """
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path) if schema_path else None
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

        # Category cache: maps (name, parent_id) → category_id
        # Prevents repeated DB lookups for the same category
        self._category_cache: Dict[tuple, int] = {}
        self.on_product_saved = None

    def __enter__(self):
        """Context manager entry: open connection and init schema."""
        if not self.conn:
            self.connect()
            self._context_managed = True
        else:
            self._context_managed = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: always close connection safely."""
        if getattr(self, '_context_managed', False):
            self.close()
        return False  # Don't suppress exceptions

    def connect(self):
        """
        Establish SQLite connection with optimized settings.
        Creates the database file if it doesn't exist.
        """
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(
                str(self.db_path),
                timeout=30,
                check_same_thread=False
            )
            self.cursor = self.conn.cursor()

            # ── SQLite Performance Optimizations ──
            self.cursor.execute("PRAGMA journal_mode=WAL")     # Write-Ahead Logging
            self.cursor.execute("PRAGMA synchronous=NORMAL")   # Balance safety/speed
            self.cursor.execute("PRAGMA cache_size=-64000")    # 64MB cache
            self.cursor.execute("PRAGMA foreign_keys=ON")      # Enforce FK constraints
            self.cursor.execute("PRAGMA temp_store=MEMORY")    # Temp tables in RAM

            # Initialize schema if provided
            if self.schema_path and self.schema_path.exists():
                self._init_schema()

            logger.info(f"Database connected: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _init_schema(self):
        """Execute the schema SQL file to create tables and indexes."""
        try:
            schema_sql = self.schema_path.read_text(encoding='utf-8')
            self.cursor.executescript(schema_sql)
            self.conn.commit()
            logger.info(f"Schema initialized from: {self.schema_path}")
        except (sqlite3.Error, FileNotFoundError) as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def close(self):
        """Safely close the database connection."""
        try:
            if self.conn:
                self.conn.commit()  # Flush any pending changes
                self.conn.close()
                logger.info("Database connection closed.")
        except sqlite3.Error as e:
            logger.warning(f"Error closing database: {e}")
        finally:
            self.conn = None
            self.cursor = None

    # ── Category Operations ────────────────────────────────────

    def upsert_category(
        self,
        name: str,
        slug: Optional[str] = None,
        parent_id: Optional[int] = None,
        level: Optional[int] = None
    ) -> int:
        """
        Insert a category or return its ID if it already exists.
        
        Uses (name, parent_id) as the composite lookup key since
        category_name is NOT unique — "Accessories" can appear under
        multiple parent categories.
        
        Args:
            name: Category display name.
            slug: URL slug for the category.
            parent_id: Parent category ID (None for root level).
            level: Hierarchy level (1=main, 2=sub, 3=leaf).
            
        Returns:
            The category_id (existing or newly created).
        """
        cache_key = (name, parent_id)

        # Check cache first to avoid DB round-trip
        if cache_key in self._category_cache:
            return self._category_cache[cache_key]

        try:
            # Look up existing category with same name + parent
            if parent_id is not None:
                self.cursor.execute(
                    """SELECT category_id FROM dmart_category_master 
                       WHERE category_name = ? AND parent_id = ?""",
                    (name, parent_id)
                )
            else:
                self.cursor.execute(
                    """SELECT category_id FROM dmart_category_master 
                       WHERE category_name = ? AND parent_id IS NULL""",
                    (name,)
                )

            row = self.cursor.fetchone()

            if row:
                # Category exists — use existing ID
                category_id = row[0]
            else:
                # Insert new category
                self.cursor.execute(
                    """INSERT INTO dmart_category_master 
                       (category_name, slug, parent_id, category_level)
                       VALUES (?, ?, ?, ?)""",
                    (name, slug, parent_id, level)
                )
                self.conn.commit()
                category_id = self.cursor.lastrowid
                logger.info(
                    f"New category inserted: '{name}' (ID={category_id}, "
                    f"parent={parent_id}, level={level})"
                )

            # Cache the result
            self._category_cache[cache_key] = category_id
            return category_id

        except sqlite3.Error as e:
            logger.error(f"Category upsert failed for '{name}': {e}")
            raise

    def resolve_category_hierarchy(
        self,
        main_cat: str,
        sub_cat: Optional[str] = None,
        leaf_cat: Optional[str] = None,
        main_slug: Optional[str] = None,
        sub_slug: Optional[str] = None,
        leaf_slug: Optional[str] = None,
    ) -> int:
        """
        Resolve a full 3-level category path, creating entries as needed.
        
        Args:
            main_cat: Level 1 category name (e.g., "Grocery & Staples")
            sub_cat: Level 2 subcategory name (e.g., "Rice & Rice Products")
            leaf_cat: Level 3 leaf category name (e.g., "Basmati Rice")
            main_slug, sub_slug, leaf_slug: URL slugs for each level.
            
        Returns:
            The category_id of the deepest (most specific) category.
        """
        # Level 1: Main category
        main_id = self.upsert_category(main_cat, main_slug, None, 1)

        if not sub_cat:
            return main_id

        # Level 2: Sub-category (child of main)
        sub_id = self.upsert_category(sub_cat, sub_slug, main_id, 2)

        if not leaf_cat:
            return sub_id

        # Level 3: Leaf category (child of sub)
        leaf_id = self.upsert_category(leaf_cat, leaf_slug, sub_id, 3)
        return leaf_id

    # ── Product Operations ─────────────────────────────────────

    def upsert_product(self, product: dict, category_id: Optional[int] = None) -> bool:
        """
        Insert or update a product using sku_id as the duplicate key.
        
        If sku_id exists → UPDATE pricing, availability, timestamp.
        If sku_id is new → INSERT the full product record.
        
        This mirrors the Amazon ASIN duplicate check methodology.
        
        Args:
            product: Cleaned product dictionary.
            category_id: Foreign key to dmart_category_master.
            
        Returns:
            True if operation succeeded, False otherwise.
        """
        sku_id = str(product.get('sku_id', '')).strip()

        # ── Secondary Deduplication (Name + Pack) ──
        # If DMart uses regional SKUs, this ensures we don't duplicate identical products
        p_name = product.get('product_name')
        p_size = product.get('pack_size')
        if p_name:
            if p_size:
                self.cursor.execute(
                    "SELECT sku_id FROM dmart_product_master WHERE product_name = ? AND pack_size = ?", 
                    (p_name, p_size)
                )
            else:
                self.cursor.execute(
                    "SELECT sku_id FROM dmart_product_master WHERE product_name = ? AND pack_size IS NULL", 
                    (p_name,)
                )
            
            row = self.cursor.fetchone()
            if row:
                # Override incoming SKU with the existing one to force a clean UPDATE
                sku_id = row[0]

        if not sku_id:
            logger.warning(f"Skipping product with no SKU: {product.get('product_name', 'unknown')}")
            return False

        try:
            # Check if SKU already exists
            self.cursor.execute(
                "SELECT id FROM dmart_product_master WHERE sku_id = ?",
                (sku_id,)
            )
            existing = self.cursor.fetchone()

            if existing:
                # ── UPDATE: Refresh pricing, availability, and timestamp ──
                self.cursor.execute(
                    """UPDATE dmart_product_master SET
                        product_name = ?,
                        brand = ?,
                        pack_size = ?,
                        mrp = ?,
                        dmart_price = ?,
                        availability = ?,
                        category_id = COALESCE(?, category_id),
                        category_name = COALESCE(?, category_name),
                        product_url = COALESCE(?, product_url),
                        image_url = COALESCE(?, image_url),
                        description = COALESCE(?, description),
                        scraped_at = CURRENT_TIMESTAMP
                    WHERE sku_id = ?""",
                    (
                        product.get('product_name'),
                        product.get('brand'),
                        product.get('pack_size'),
                        product.get('mrp'),
                        product.get('dmart_price'),
                        product.get('availability', 1),
                        category_id,
                        product.get('category_name'),
                        product.get('product_url'),
                        product.get('image_url'),
                        product.get('description'),
                        sku_id,
                    )
                )
                logger.debug(f"Updated product: {sku_id}")
            else:
                # ── INSERT: New product record ──
                self.cursor.execute(
                    """INSERT INTO dmart_product_master 
                       (sku_id, product_name, brand, pack_size, mrp,
                        dmart_price, availability, category_id, category_name, product_url, image_url, description)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sku_id,
                        product.get('product_name'),
                        product.get('brand'),
                        product.get('pack_size'),
                        product.get('mrp'),
                        product.get('dmart_price'),
                        product.get('availability', 1),
                        category_id,
                        product.get('category_name'),
                        product.get('product_url'),
                        product.get('image_url'),
                        product.get('description'),
                    )
                )
                logger.debug(f"Inserted product: {sku_id}")

            self.conn.commit()
            if self.on_product_saved:
                try:
                    self.on_product_saved(product, category_id)
                except Exception as cb_err:
                    logger.error(f"Error in on_product_saved callback: {cb_err}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Product upsert failed for SKU '{sku_id}': {e}")
            return False

    def bulk_upsert_products(
        self,
        products: List[dict],
        category_id: Optional[int] = None
    ) -> dict:
        """
        Batch upsert multiple products in a single transaction.
        
        Args:
            products: List of cleaned product dictionaries.
            category_id: FK to category table.
            
        Returns:
            Stats dict with 'inserted', 'updated', 'failed' counts.
        """
        stats = {'inserted': 0, 'updated': 0, 'failed': 0}

        try:
            self.cursor.execute("BEGIN TRANSACTION")

            for product in products:
                sku_id = product.get('sku_id')
                if not sku_id:
                    stats['failed'] += 1
                    continue

                # Check existence
                self.cursor.execute(
                    "SELECT id FROM dmart_product_master WHERE sku_id = ?",
                    (sku_id,)
                )
                existing = self.cursor.fetchone()

                if existing:
                    self.cursor.execute(
                        """UPDATE dmart_product_master SET
                            product_name = ?, brand = ?, pack_size = ?,
                            mrp = ?, dmart_price = ?, availability = ?,
                            category_id = COALESCE(?, category_id),
                            product_url = COALESCE(?, product_url),
                            description = COALESCE(?, description),
                            scraped_at = CURRENT_TIMESTAMP
                        WHERE sku_id = ?""",
                        (
                            product.get('product_name'),
                            product.get('brand'),
                            product.get('pack_size'),
                            product.get('mrp'),
                            product.get('dmart_price'),
                            product.get('availability', 1),
                            category_id,
                            product.get('product_url'),
                            product.get('description'),
                            sku_id,
                        )
                    )
                    stats['updated'] += 1
                else:
                    self.cursor.execute(
                        """INSERT INTO dmart_product_master
                           (sku_id, product_name, brand, pack_size, mrp,
                            dmart_price, availability, category_id, product_url, description)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            sku_id,
                            product.get('product_name'),
                            product.get('brand'),
                            product.get('pack_size'),
                            product.get('mrp'),
                            product.get('dmart_price'),
                            product.get('availability', 1),
                            category_id,
                            product.get('product_url'),
                            product.get('description'),
                        )
                    )
                    stats['inserted'] += 1

            self.conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Bulk upsert transaction failed: {e}")
            self.conn.rollback()
            stats['failed'] = len(products)

        logger.info(
            f"Bulk upsert complete: {stats['inserted']} inserted, "
            f"{stats['updated']} updated, {stats['failed']} failed"
        )
        return stats

    # ── Query / Stats ──────────────────────────────────────────

    def get_product_count(self) -> int:
        """Return total product count in the database."""
        self.cursor.execute("SELECT COUNT(*) FROM dmart_product_master")
        return self.cursor.fetchone()[0]

    def get_category_count(self) -> int:
        """Return total category count in the database."""
        self.cursor.execute("SELECT COUNT(*) FROM dmart_category_master")
        return self.cursor.fetchone()[0]

    def get_products_missing_descriptions(self) -> List[str]:
        """
        Return a list of product_urls for products that have no description.
        Useful for hybrid scraping to selectively visit PDPs.
        """
        self.cursor.execute("""
            SELECT product_url 
            FROM dmart_product_master 
            WHERE description IS NULL OR description = '' 
              AND product_url IS NOT NULL
        """)
        rows = self.cursor.fetchall()
        return [row[0] for row in rows if row[0]]

    def get_existing_products_for_category(self, category_id: int) -> List[Dict[str, Any]]:
        """
        Return a list of products (sku_id, name, pack_size) already saved in SQLite for a category.
        """
        if category_id is None:
            return []
        try:
            self.cursor.execute(
                "SELECT sku_id, product_name, pack_size FROM dmart_product_master WHERE category_id = ?",
                (category_id,)
            )
            rows = self.cursor.fetchall()
            return [
                {
                    'sku_id': row[0],
                    'product_name': row[1],
                    'pack_size': row[2]
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Failed to get existing products for category {category_id}: {e}")
            return []


    def export_master_csv(self, output_path: Path) -> int:
        """
        Export the entire dmart_product_master table to a master CSV file.
        
        Args:
            output_path: Path object where the CSV should be saved.
            
        Returns:
            Number of rows exported.
        """
        try:
            # Query all columns in order
            self.cursor.execute("""
                SELECT 
                    sku_id, product_name, brand, pack_size, mrp, 
                    dmart_price, availability, product_url, image_url, description, category_name 
                FROM dmart_product_master
            """)
            rows = self.cursor.fetchall()
            
            if not rows:
                logger.warning("No data in database to export to Master CSV.")
                return 0
                
            # Column headers matching the SELECT statement
            headers = [
                'sku_id', 'product_name', 'brand', 'pack_size', 'mrp', 
                'dmart_price', 'availability', 'product_url', 'image_url', 'description', 'category_name'
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
                
            logger.info(f"Master CSV successfully exported: {output_path} ({len(rows)} rows)")
            return len(rows)
            
        except Exception as e:
            logger.error(f"Failed to export master CSV: {e}")
            return 0

    def get_stats(self) -> dict:
        """Return a summary of database statistics."""
        return {
            'total_products': self.get_product_count(),
            'total_categories': self.get_category_count(),
            'db_size_mb': round(
                self.db_path.stat().st_size / (1024 * 1024), 2
            ) if self.db_path.exists() else 0,
        }
