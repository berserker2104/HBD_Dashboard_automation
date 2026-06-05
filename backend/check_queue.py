import redis
import os
import json
from dotenv import load_dotenv

load_dotenv(override=True)

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
r = redis.from_url(broker_url)

print("=== CELERY QUEUE INSPECTION ===")
try:
    # Celery default queue name is 'celery'
    queue_len = r.llen("celery")
    print(f"Pending tasks in 'celery' queue: {queue_len}")
    
    # Let's peek at the first 10 tasks in the queue
    tasks = r.lrange("celery", 0, 9)
    for idx, task_raw in enumerate(tasks, 1):
        try:
            task = json.loads(task_raw)
            headers = task.get("headers", {})
            properties = task.get("properties", {})
            body = task.get("body", "")
            
            task_name = headers.get("task")
            task_id = headers.get("id")
            
            print(f"[{idx}] Task Name: {task_name} | ID: {task_id}")
        except Exception as e:
            print(f"[{idx}] Raw task data: {task_raw[:100]}... Error: {e}")
            
except Exception as e:
    print(f"Error inspecting queue: {e}")
