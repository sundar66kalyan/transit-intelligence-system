# reset_data.py
import requests

try:
    response = requests.delete("http://localhost:8001/clear_data")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    print("Make sure backend is running on port 8001")
