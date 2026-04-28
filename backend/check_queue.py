import redis
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
r = redis.from_url(url)
print(f"Queue 'celery' length: {r.llen('celery')}")
print(f"Queue 'priority' length: {r.llen('priority')}")
