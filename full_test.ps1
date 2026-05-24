Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "AI TRANSIT SYSTEM - COMPLETE TEST" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Write-Host "`n1. Checking backend health..." -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "http://localhost:8001/health" -ErrorAction SilentlyContinue
if ($health) {
    Write-Host "   ✅ Backend is running" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend is NOT running!" -ForegroundColor Red
    Write-Host "   Please start backend first: python backend/minimal_backend.py" -ForegroundColor White
    exit
}

Write-Host "`n2. Registering person..." -ForegroundColor Yellow
python -c "
import requests
with open('D:/transit-intelligence-system/data/face_images/1.jpg', 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'name': 'Test User', 'passenger_id': 'T001', 'passenger_type': 'Regular', 'gender': 'Male', 'phone': '123', 'email': 'test@test.com', 'live_url': ''}
    r = requests.post('http://localhost:8001/register_passenger', files=files, data=data)
    print(f'   {r.json()}')
"

Write-Host "`n3. Testing ENTRY..." -ForegroundColor Yellow
python -c "
import requests
with open('D:/transit-intelligence-system/data/face_images/1.jpg', 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'camera_id': 'camera_1 - Central Station'}
    r = requests.post('http://localhost:8001/auto_entry', files=files, data=data)
    print(f'   {r.json()}')
"

Write-Host "`n4. Vehicle status after entry..." -ForegroundColor Yellow
$status = Invoke-RestMethod -Uri "http://localhost:8001/vehicle_status"
Write-Host "   Occupancy: $($status.current_occupancy)" -ForegroundColor Green

Write-Host "`n5. Testing EXIT..." -ForegroundColor Yellow
python -c "
import requests
with open('D:/transit-intelligence-system/data/face_images/1.jpg', 'rb') as f:
    files = {'file': ('face.jpg', f, 'image/jpeg')}
    data = {'camera_id': 'camera_1 - Central Station'}
    r = requests.post('http://localhost:8001/auto_exit', files=files, data=data)
    print(f'   {r.json()}')
"

Write-Host "`n6. Vehicle status after exit..." -ForegroundColor Yellow
$status = Invoke-RestMethod -Uri "http://localhost:8001/vehicle_status"
Write-Host "   Occupancy: $($status.current_occupancy)" -ForegroundColor Green

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "✅ TEST COMPLETE!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
