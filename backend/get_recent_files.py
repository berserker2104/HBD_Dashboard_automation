import sys, os
from sqlalchemy import create_engine, text
from config import config

engine = create_engine(config.DATABASE_URI)
with engine.connect() as conn:
    with open('recent_output_utf8.txt', 'w', encoding='utf-8') as f:
        # Group by status to show the overall picture
        f.write("OVERALL STATUS OF ALL FILES:\n")
        statuses = conn.execute(text("SELECT status, count(*) FROM file_registry GROUP BY status")).fetchall()
        for row in statuses:
            f.write(f"- {row[0]}: {row[1]} files\n")
        
        f.write("\nCURRENTLY PROCESSING FILES (Top 5):\n")
        res = conn.execute(text("SELECT filename, status, processed_at FROM file_registry WHERE status = 'IN_PROGRESS' ORDER BY processed_at DESC LIMIT 5")).fetchall()
        for row in res:
            f.write(f"- {row.filename} | Last Updated at: {row.processed_at}\n")
        
        f.write("\nRECENTLY FINISHED FILES (Top 5):\n")
        finished = conn.execute(text("SELECT filename, status, processed_at FROM file_registry WHERE status = 'PROCESSED' ORDER BY processed_at DESC LIMIT 5")).fetchall()
        for row in finished:
            f.write(f"- {row.filename} | Last Updated at: {row.processed_at}\n")
