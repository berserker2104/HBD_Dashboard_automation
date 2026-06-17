"""
pipelines.py — Dashboard copy (stripped).
Only CleaningPipeline and DedupPipeline are active.

MySQLPipeline and CSVExportPipeline are intentionally excluded here:
  - Database writes are handled by FlipkartFlaskDatabasePipeline in flipkart_service.py
  - CSV output is not needed in dashboard mode
"""

import re
from itemadapter import ItemAdapter


def _clean_price(val: str) -> str:
    if not val:
        return ""
    return re.sub(r"[^\d.]", "", val)


# ── Pipeline 1: Clean & normalise fields ──────────────────────────────────────

class CleaningPipeline:
    """Normalize and clean fields. Maps spider item fields correctly."""

    def process_item(self, item, spider=None):
        adapter = ItemAdapter(item)

        # Price fields — strip currency symbols, keep digits and dot only
        adapter["price"]    = _clean_price(adapter.get("price") or "")
        adapter["mrp"]      = _clean_price(adapter.get("mrp") or "")

        # Discount — strip "off" suffix, keep "67%" style
        discount = adapter.get("discount") or ""
        adapter["discount"] = discount.replace("off", "").strip()

        # Text fields — strip whitespace
        adapter["product_name"] = (adapter.get("product_name") or "").strip()
        adapter["brand"]        = (adapter.get("brand") or "").strip()
        adapter["rating"]       = (adapter.get("rating") or "").strip()
        adapter["reviews"]      = (adapter.get("reviews") or "").strip()
        adapter["spec_bullets"] = (adapter.get("spec_bullets") or "").strip()

        return item


# ── Pipeline 2: Deduplicate by product_id ────────────────────────────────────

class DedupPipeline:
    """Drop duplicate products by product_id within a single crawl run."""

    def __init__(self):
        self._seen: set = set()

    def process_item(self, item, spider=None):
        pid = ItemAdapter(item).get("product_id", "")
        if pid and pid in self._seen:
            from scrapy.exceptions import DropItem
            raise DropItem(f"Duplicate product_id: {pid}")
        if pid:
            self._seen.add(pid)
        return item
