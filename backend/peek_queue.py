import redis
import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
r = redis.from_url(url)

print("Peeking at queue 'celery'...")
tasks = r.lrange('celery', 0, 2)
for i, task_raw in enumerate(tasks):
    print(f"Task {i} Raw: {task_raw[:200]}...")
    try:
        task_data = json.loads(task_raw)
        print(f"Task {i} JSON: {task_data.keys()}")
        if 'body' in task_data:
            print(f"Body snippet: {task_data['body'][:100]}")
    except Exception as e:
        print(f"Error: {e}")
