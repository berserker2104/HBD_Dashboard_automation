-- ============================================================
-- DMart Product Master — Database Schema
-- ============================================================
-- This schema implements a 2-table enterprise "Product Master"
-- flow with referential integrity and duplicate prevention.
-- ============================================================

-- Table 1: Category Hierarchy (3-level tree)
-- NOTE: category_name is NOT UNIQUE because names like
-- "Accessories" or "Containers" can appear under different parents.
-- Hierarchy is tracked via parent_id self-referencing FK.
CREATE TABLE IF NOT EXISTS dmart_category_master (
    category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name   TEXT    NOT NULL,
    slug            TEXT,
    parent_id       INTEGER,
    category_level  INTEGER,
    category_path   TEXT,
    FOREIGN KEY (parent_id) REFERENCES dmart_category_master(category_id)
);

-- Composite index for fast hierarchy lookups
CREATE INDEX IF NOT EXISTS idx_category_parent 
    ON dmart_category_master(parent_id);

CREATE INDEX IF NOT EXISTS idx_category_slug 
    ON dmart_category_master(slug);


-- Table 2: Product Master
-- Product master tracks items, allowing multiple pricing rows per SKU.
-- If pricing is identical, we update and append the pincode to a JSON array.
-- If pricing is different, a separate row is created.
CREATE TABLE IF NOT EXISTS dmart_product_master (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id          TEXT    NOT NULL,
    product_name    TEXT,
    brand           TEXT,
    pack_size       TEXT,
    mrp             REAL,
    dmart_price     REAL,
    availability    INTEGER,
    category_id     INTEGER,
    category_name   TEXT,
    product_url     TEXT,
    image_url       TEXT,
    description     TEXT,
    pincodes        TEXT,      -- JSON list of pincodes (e.g. ["400001", "400002"])
    scraped_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES dmart_category_master(category_id)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_product_sku 
    ON dmart_product_master(sku_id);

CREATE INDEX IF NOT EXISTS idx_product_brand 
    ON dmart_product_master(brand);

CREATE INDEX IF NOT EXISTS idx_product_category 
    ON dmart_product_master(category_id);

CREATE INDEX IF NOT EXISTS idx_product_scraped 
    ON dmart_product_master(scraped_at);
