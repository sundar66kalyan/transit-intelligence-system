# complete_test.py
import requests
import os

# Path to your face image
image_path = "D:/transit-intelligence-system/data/face_images/1.jpg"

if not os.path.exists(image_path):
    print(f"Image not found: {image_path}")
    exit()

print("=" * 50)
print("AI TRANSIT SYSTEM TEST")
print("=" * 50)

# 1. Check health
print("\n1. Checking backend health...")
r = requests.get("http://localhost:8001/health")
print(f"   Health: {r.json()}")

# 2. Register the person
print("\n2. Registering person...")
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {
        'name': 'John Doe',
        'passenger_id': 'P001',
        'passenger_type': 'Regular',
        'gender': 'Male',
        'phone': '9876543210',
        'email': 'john@example.com',
        'live_url': ''
    }
    r = requests.post('http://localhost:8001/register_passenger', files=files, data=data)
    print(f"   Response: {r.json()}")

# 3. Test Entry
print("\n3. Testing AUTO ENTRY...")
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'camera_id': 'camera_1 - Central Station'}
    r = requests.post('http://localhost:8001/auto_entry', files=files, data=data)
    print(f"   Response: {r.json()}")

# 4. Check vehicle status after entry
print("\n4. Vehicle status after entry...")
r = requests.get("http://localhost:8001/vehicle_status")
print(f"   Occupancy: {r.json().get('current_occupancy', 0)}")

# 5. Test Exit
print("\n5. Testing AUTO EXIT...")
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'camera_id': 'camera_1 - Central Station'}
    r = requests.post('http://localhost:8001/auto_exit', files=files, data=data)
    print(f"   Response: {r.json()}")

# 6. Check vehicle status after exit
print("\n6. Vehicle status after exit...")
r = requests.get("http://localhost:8001/vehicle_status")
print(f"   Occupancy: {r.json().get('current_occupancy', 0)}")

# 7. Get journey history
print("\n7. Journey history...")
r = requests.get("http://localhost:8001/completed_journeys")
journeys = r.json().get('journeys', [])
print(f"   Total journeys: {len(journeys)}")
if journeys:
    print(f"   Last journey: {journeys[-1]}")

print("\n" + "=" * 50)
print("✅ Test complete!")
print("=" * 50)
