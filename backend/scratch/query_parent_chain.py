import os
import sys
from sqlalchemy import create_engine, text

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

engine = create_engine(config.DATABASE_URI)

with engine.connect() as conn:
    print("=== Category Parent Chains ===")
    
    # Query all active level 3/4 categories
    res = conn.execute(text("SELECT id, name, level, parent_id, is_active FROM master_categories WHERE level >= 3 AND is_active = 1")).fetchall()
    
    for row in res:
        cat_id, name, level, parent_id, is_active = row
        chain = [f"L{level}:{name}(ID:{cat_id},Active:{is_active})"]
        
        curr_parent_id = parent_id
        while curr_parent_id is not None:
            parent_row = conn.execute(text("SELECT id, name, level, parent_id, is_active FROM master_categories WHERE id = :id"), {"id": curr_parent_id}).fetchone()
            if parent_row:
                p_id, p_name, p_level, p_parent, p_active = parent_row
                chain.append(f"L{p_level}:{p_name}(ID:{p_id},Active:{p_active})")
                curr_parent_id = p_parent
            else:
                chain.append(f"MISSING_PARENT(ID:{curr_parent_id})")
                break
                
        print(" -> ".join(chain))
