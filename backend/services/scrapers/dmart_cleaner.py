# ============================================================
# DMart Cleaner — Re-export Shim
# ============================================================
# The canonical DataCleaner implementation now lives in:
#   services/scrapers/dmart_engine/cleaner.py
#
# This shim re-exports DataCleaner from there so any existing
# code that does:
#   from services.scrapers.dmart_cleaner import DataCleaner
# continues to work without modification.
# ============================================================

from services.scrapers.dmart_engine.cleaner import DataCleaner  # noqa: F401

__all__ = ["DataCleaner"]
