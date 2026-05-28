# ============================================================
# DMart Scraper Service — Celery Integration Adapter
# ============================================================
# Thin adapter between Celery tasks and the dmart_engine package.
#
# Flow:
#   Frontend  →  POST /api/scrape_dmart  →  dmart_routes.py
#   dmart_routes.py  →  run_dmart_scraper.delay()  (Celery)
#   Celery worker  →  scrape_dmart_search()  (this file)
#   scrape_dmart_search()  →  DMartScraper (dmart_engine)
#                         →  SQLite (dmart_master.db)  [engine writes directly]
#                         →  MySQL  (dmart_products)   [this adapter syncs]
#
# The scraper engine (dmart_engine/scraper.py) streams every
# product to SQLite in real-time. After scraping completes,
# this adapter reads new rows from SQLite and upserts them to MySQL.
# ============================================================

import asyncio
import logging
from typing import Optional

from services.scrapers.dmart_engine.scraper import DMartScraper
from services.scrapers.dmart_engine.database import DatabaseManager
from services.scrapers.dmart_engine.config import DB_PATH, SCHEMA_PATH, EXPORT_DIR
from services.scrapers.dmart_engine.sitemap_runner import SitemapRunner

logger = logging.getLogger(__name__)


def scrape_dmart_search(
    search_term: str,
    mode: str = "category",
    pincodes: str = "400001",
    max_categories: Optional[int] = None,
    task_id: Optional[int] = None
):
    """
    Celery-compatible entry point for the DMart scraper.

    Modes:
        category — Infinite scroll PLP scraping (default)
        sitemap  — PDP scraping via XML sitemap
        hybrid   — Category scrape + sitemap fill for missing descriptions

    After each pincode's scrape completes, all products in SQLite
    (dmart_product_master) are synced to MySQL (dmart_products table).
    """
    from app import app
    from extensions import db
    from model.product_model.additional_products import DMart
    from model.scraper_task import ScraperTask

    with app.app_context():
        # ── Retrieve Task for progress updates ──
        task = None
        if task_id:
            try:
                task = ScraperTask.query.get(task_id)
                if task:
                    task.status = "RUNNING"
                    task.progress = 0
                    db.session.commit()
                    logger.info(f"ScraperTask {task_id} initialized to RUNNING")
            except Exception as e:
                logger.warning(f"Failed to fetch/initialize ScraperTask in start: {e}")

        # ── Parse pincode list ──
        if str(pincodes).strip().lower() == "all":
            from services.scrapers.dmart_engine.config import PINCODE_LIST
            pincode_list = PINCODE_LIST
        else:
            pincode_list = [p.strip() for p in str(pincodes).split(",") if p.strip()]

        limit = int(max_categories) if max_categories else None

        logger.info(
            f"=== DMart Scraper START | mode={mode} | "
            f"pincodes={pincode_list[:3]}... | max_cat={limit} ==="
        )

        for idx, pin in enumerate(pincode_list, 1):
            logger.info(f"[{idx}/{len(pincode_list)}] Running scrape for pincode: {pin}")

            if task:
                try:
                    db.session.refresh(task)
                    task.status = f"Pincode {pin} ({idx}/{len(pincode_list)}): Initializing browser..."
                    db.session.commit()
                except Exception:
                    pass

            # ── Open SQLite (shared across modes for this pincode) ──
            sqlite_db = DatabaseManager(str(DB_PATH), str(SCHEMA_PATH))

            # ── Register real-time simultaneous MySQL & Task updates callback ──
            def on_product_saved_callback(product: dict, category_id: Optional[int] = None):
                try:
                    sku_id = str(product.get('sku_id', '')).strip()
                    if not sku_id:
                        return

                    product_name = product.get('product_name') or "Unknown Product"
                    brand = product.get('brand')
                    pack_size = product.get('pack_size')
                    mrp = product.get('mrp')
                    dmart_price = product.get('dmart_price')
                    availability = product.get('availability')
                    category_name = product.get('category_name') or "Uncategorized"
                    product_url = product.get('product_url')
                    image_url = product.get('image_url')
                    description = product.get('description')

                    price_str = str(dmart_price) if dmart_price is not None else "0.0"
                    mrp_str = str(mrp) if mrp is not None else "0.0"

                    # Sync product to MySQL dmart_products
                    existing = DMart.query.filter_by(asin=sku_id).first()
                    if existing:
                        existing.title       = product_name
                        existing.imgUrl      = image_url
                        existing.productUrl  = product_url
                        existing.price       = price_str
                        existing.categoryName = category_name
                        existing.brand       = brand
                        existing.description = description
                    else:
                        new_product = DMart(
                            asin         = sku_id,
                            title        = product_name,
                            imgUrl       = image_url,
                            productUrl   = product_url,
                            stars        = "0.0",
                            reviews      = "0",
                            price        = price_str,
                            categoryName = category_name,
                            brand        = brand,
                            description  = description,
                        )
                        db.session.add(new_product)
                    
                    db.session.commit()

                    # Update ScraperTask status and progress
                    if task:
                        try:
                            db.session.refresh(task)
                            task.total_found = task.total_found + 1
                            
                            # Estimate progress based on found products
                            estimated_prog = min(99, int((task.total_found / (limit * len(pincode_list) if limit else 300)) * 100))
                            task.progress = max(task.progress, estimated_prog)
                            
                            cat_lbl = category_name or "products"
                            task.status = f"Pincode {pin} ({idx}/{len(pincode_list)}): Scraped {task.total_found} products (last: {cat_lbl})"
                            db.session.commit()
                        except Exception as t_err:
                            db.session.rollback()
                            logger.error(f"Failed to update task progress: {t_err}")

                except Exception as sync_err:
                    db.session.rollback()
                    logger.error(f"Real-time MySQL sync failed for SKU {product.get('sku_id')}: {sync_err}")

            sqlite_db.on_product_saved = on_product_saved_callback
            sqlite_db.connect()

            try:
                # Count products already in SQLite before this run
                products_before = sqlite_db.get_product_count()

                # ── Mode: Category Infinite Scroll ──
                if mode in ("category", "hybrid"):
                    logger.info(f"Stage 1: Category PLP scrape for pincode {pin}...")

                    async def _run_category():
                        async with DMartScraper(sqlite_db, pincode=pin) as scraper:
                            await scraper.run(max_categories=limit)

                    asyncio.run(_run_category())
                    products_after_cat = sqlite_db.get_product_count()
                    logger.info(
                        f"Category scrape done. SQLite: {products_before} → {products_after_cat} "
                        f"(+{products_after_cat - products_before} new products)"
                    )

                # ── Mode: Sitemap PDP Scraping ──
                if mode == "sitemap":
                    sitemap_limit = int(search_term) if str(search_term).isdigit() else 50
                    logger.info(f"Sitemap mode: scraping {sitemap_limit} PDPs for pincode {pin}...")
                    runner = SitemapRunner(sqlite_db, pincode=pin)
                    asyncio.run(runner.run(limit=sitemap_limit))

                # ── Mode: Hybrid Stage 2 — fill missing descriptions ──
                if mode == "hybrid":
                    try:
                        missing_urls = sqlite_db.get_products_missing_descriptions()
                        if missing_urls:
                            logger.info(
                                f"Hybrid Stage 2: filling descriptions for "
                                f"{len(missing_urls)} products..."
                            )
                            runner = SitemapRunner(sqlite_db, pincode=pin)
                            asyncio.run(runner.run(
                                limit=len(missing_urls),
                                custom_urls=missing_urls
                            ))
                        else:
                            logger.info("Hybrid Stage 2: no missing descriptions. Skipping.")
                    except Exception as e:
                        logger.error(f"Hybrid Stage 2 failed: {e}")

                # ── Read new products from SQLite → Sync to MySQL (Double-safety fallback) ──
                logger.info("Reading products from SQLite for MySQL sync...")
                try:
                    sqlite_db.cursor.execute("""
                        SELECT
                            sku_id, product_name, brand, pack_size,
                            mrp, dmart_price, availability,
                            category_name, product_url, image_url, description
                        FROM dmart_product_master
                        ORDER BY scraped_at DESC
                    """)
                    rows = sqlite_db.cursor.fetchall()
                except Exception as e:
                    logger.error(f"SQLite read failed: {e}")
                    rows = []

                logger.info(f"Syncing {len(rows)} products from SQLite → MySQL...")
                synced = 0
                failed = 0

                for row in rows:
                    try:
                        (
                            sku_id, product_name, brand, pack_size,
                            mrp, dmart_price, availability,
                            category_name, product_url, image_url, description
                        ) = row

                        if not sku_id:
                            continue

                        price_str    = str(dmart_price) if dmart_price is not None else "0.0"
                        mrp_str      = str(mrp) if mrp is not None else "0.0"
                        cat_str      = category_name or "Uncategorized"
                        name_str     = product_name or "Unknown Product"

                        existing = DMart.query.filter_by(asin=sku_id).first()
                        if existing:
                            existing.title       = name_str
                            existing.imgUrl      = image_url
                            existing.productUrl  = product_url
                            existing.price       = price_str
                            existing.categoryName = cat_str
                            existing.brand       = brand
                            existing.description = description
                        else:
                            new_product = DMart(
                                asin         = sku_id,
                                title        = name_str,
                                imgUrl       = image_url,
                                productUrl   = product_url,
                                stars        = "0.0",
                                reviews      = "0",
                                price        = price_str,
                                categoryName = cat_str,
                                brand        = brand,
                                description  = description,
                            )
                            db.session.add(new_product)

                        synced += 1
                        if synced % 200 == 0:
                            db.session.commit()

                    except Exception as row_err:
                        failed += 1
                        db.session.rollback()
                        logger.error(f"MySQL upsert failed for SKU {sku_id}: {row_err}")

                db.session.commit()
                logger.info(
                    f"MySQL sync complete: {synced} synced, {failed} failed "
                    f"from {len(rows)} total SQLite rows."
                )

                # ── Export master CSV from SQLite ──
                try:
                    master_csv = EXPORT_DIR / "dmart_master_report.csv"
                    rows_exported = sqlite_db.export_master_csv(master_csv)
                    logger.info(f"Master CSV exported: {master_csv} ({rows_exported} rows)")
                except Exception as csv_err:
                    logger.error(f"CSV export failed: {csv_err}")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Scrape failed for pincode {pin}: {e}", exc_info=True)
                if task:
                    try:
                        db.session.refresh(task)
                        task.status = "ERROR"
                        task.error_message = str(e)
                        db.session.commit()
                    except Exception:
                        pass
                raise
            finally:
                sqlite_db.close()

        # Mark ScraperTask as COMPLETED
        if task:
            try:
                db.session.refresh(task)
                task.status = "COMPLETED"
                task.progress = 100
                db.session.commit()
                logger.info(f"ScraperTask {task_id} marked as COMPLETED")
            except Exception as t_err:
                logger.error(f"Failed to set task as COMPLETED: {t_err}")

        logger.info("=== DMart Celery Task COMPLETE ===")

if __name__ == '__main__':
    import argparse
    import os
    import sys
    
    # Ensure backend folder is in sys.path when running as CLI subprocess
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
        
    parser = argparse.ArgumentParser(description="DMart Scraper Standalone Process Runner")
    parser.add_argument("--search_term", type=str, required=True)
    parser.add_argument("--mode", type=str, default="category")
    parser.add_argument("--pincodes", type=str, default="400001")
    parser.add_argument("--max_categories", type=int, default=None)
    parser.add_argument("--task_id", type=int, default=None)
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s")
    
    scrape_dmart_search(
        search_term=args.search_term,
        mode=args.mode,
        pincodes=args.pincodes,
        max_categories=args.max_categories,
        task_id=args.task_id
    )
