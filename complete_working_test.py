# complete_working_test.py
import requests
import time

image_path = 'D:/transit-intelligence-system/data/face_images/1.jpg'

print('='*60)
print('COMPLETE WORKING BACKEND TEST')
print('='*60)

# 1. Health check
print('\n1. Health check...')
try:
    r = requests.get('http://localhost:8001/health')
    print(f'   ✅ Backend is healthy: {r.json()}')
except:
    print('   ❌ Backend is not running!')
    exit()

# 2. Clear existing data
print('\n2. Clearing old data...')
r = requests.delete('http://localhost:8001/clear_data')
print(f'   {r.json()}')

# 3. Register person
print('\n3. Registering person with face image...')
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {
        'name': 'Test User',
        'passenger_id': 'T001',
        'passenger_type': 'Regular',
        'gender': 'Male',
        'phone': '9876543210',
        'email': 'test@user.com',
        'live_url': ''
    }
    r = requests.post('http://localhost:8001/register_passenger', files=files, data=data)
    result = r.json()
    print(f'   {result}')
    
    if result.get('status') != 'success':
        print('   ❌ Registration failed!')
        exit()

# 4. Test ENTRY with same image
print('\n4. Testing ENTRY with registered face...')
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'camera_id': 'camera_1 - Central Station'}
    r = requests.post('http://localhost:8001/auto_entry', files=files, data=data)
    result = r.json()
    print(f'   Event: {result.get("event")}')
    print(f'   Message: {result.get("message")}')
    if result.get("location"):
        print(f'   Location: {result.get("location")}')
    if result.get("gps"):
        print(f'   GPS: {result.get("gps")}')
    if result.get("current_occupancy") is not None:
        print(f'   Occupancy: {result.get("current_occupancy")}')

# 5. Check vehicle status after entry
print('\n5. Vehicle status after entry...')
r = requests.get('http://localhost:8001/vehicle_status')
status = r.json()
print(f'   Current Occupancy: {status.get("current_occupancy", 0)}')
print(f'   Total Registered: {status.get("total_registered", 0)}')

# 6. Test EXIT
print('\n6. Testing EXIT...')
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'camera_id': 'camera_1 - Central Station'}
    r = requests.post('http://localhost:8001/auto_exit', files=files, data=data)
    result = r.json()
    print(f'   Event: {result.get("event")}')
    print(f'   Message: {result.get("message")}')
    if result.get("duration"):
        print(f'   Duration: {result.get("duration")}')
    if result.get("current_occupancy") is not None:
        print(f'   Remaining Occupancy: {result.get("current_occupancy")}')

# 7. Final vehicle status
print('\n7. Final vehicle status...')
r = requests.get('http://localhost:8001/vehicle_status')
status = r.json()
print(f'   Current Occupancy: {status.get("current_occupancy", 0)}')
print(f'   Completed Journeys: {status.get("completed_journeys_count", 0)}')

# 8. Check journey history
print('\n8. Journey history...')
r = requests.get('http://localhost:8001/completed_journeys')
journeys = r.json()
print(f'   Total journeys: {journeys.get("count", 0)}')
if journeys.get("journeys"):
    last = journeys["journeys"][-1]
    print(f'   Last journey: {last.get("passenger_name")} - {last.get("duration")}')

print('\n' + '='*60)
print('✅ TEST COMPLETE!')
print('='*60)
