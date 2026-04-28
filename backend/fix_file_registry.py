import logging
from sqlalchemy import create_engine, text
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ManualMigration")

def run_migration():
    engine = create_engine(config.DATABASE_URI)
    with engine.begin() as conn:
        # Check if drive_folder_id exists in file_registry
        try:
            res = conn.execute(text("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'file_registry' AND COLUMN_NAME = 'drive_folder_id'"))
            if res.scalar() == 0:
                logger.info("⚠️ Column `drive_folder_id` missing in file_registry. Adding...")
                conn.execute(text("ALTER TABLE file_registry ADD COLUMN drive_folder_id VARCHAR(255)"))
                logger.info("✅ Column `drive_folder_id` added successfully.")
            else:
                logger.info("✅ Column `drive_folder_id` already exists in file_registry.")
        except Exception as e:
            logger.error(f"❌ Failed to migrate file_registry: {e}")

if __name__ == "__main__":
    run_migration()
