import requests

# Use your existing image
image_path = 'D:/transit-intelligence-system/data/face_images/1.jpg'

print('='*50)
print('TESTING WORKING BACKEND')
print('='*50)

# 1. Clear old data
print('\n1. Clearing old data...')
try:
    r = requests.delete('http://localhost:8001/clear_data')
    print('   Data cleared')
except:
    print('   Could not clear data')

# 2. Register
print('\n2. Registering person...')
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {
        'name': 'John Doe',
        'passenger_id': 'P001',
        'passenger_type': 'Regular',
        'gender': 'Male',
        'phone': '1234567890',
        'email': 'john@example.com',
        'live_url': ''
    }
    r = requests.post('http://localhost:8001/register_passenger', files=files, data=data)
    print(f'   Response: {r.json()}')

# 3. Test Entry
print('\n3. Testing ENTRY...')
with open(image_path, 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'camera_id': 'camera_1 - Central Station'}
    r = requests.post('http://localhost:8001/auto_entry', files=files, data=data)
    print(f'   Response: {r.json()}')

# 4. Check status
print('\n4. Vehicle status:')
r = requests.get('http://localhost:8001/vehicle_status')
status = r.json()
print(f'   Occupancy: {status.get("current_occupancy", 0)}')
print(f'   Registered: {status.get("total_registered", 0)}')

print('\n✅ Test complete!')
