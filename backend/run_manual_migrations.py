from app import app
from utils.db_migrations import run_pending_migrations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ManualMigration")

if __name__ == "__main__":
    print("🚀 Running manual database migrations...")
    run_pending_migrations(app)
    print("✅ Done!")
