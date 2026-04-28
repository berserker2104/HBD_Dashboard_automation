import requests
import json

def test_api():
    try:
        r = requests.get('http://127.0.0.1:8001/api/report/aggregate', timeout=5)
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
