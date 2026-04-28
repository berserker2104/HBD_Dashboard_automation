import requests
import json

def test_atm_endpoint():
    # Hit root first to trigger route printing in backend logs
    root_resp = requests.get("http://localhost:8001/")
    print("--- SERVER ROUTES ---")
    print(json.dumps(root_resp.json(), indent=2))
    print("---------------------\n")
    
    url = "http://localhost:8001/api/atm/fetch-data"
    params = {
        "page": 1,
        "limit": 5
    }
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except:
            print("Response text (not JSON):")
            print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_atm_endpoint()
