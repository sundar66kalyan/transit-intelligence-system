Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Face Recognition System - Quick Test" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Step 1: Create faces
Write-Host "`n📸 Creating face images..." -ForegroundColor Yellow
python D:\transit-intelligence-system\create_faces.py

# Step 2: Test recognition
Write-Host "`n🔍 Testing face recognition..." -ForegroundColor Yellow
python D:\transit-intelligence-system\test_face_recognition.py

# Step 3: Check files
Write-Host "`n📁 Face images created:" -ForegroundColor Yellow
Get-ChildItem D:\transit-intelligence-system\test_faces\*.jpg | ForEach-Object { Write-Host "  - $($_.Name)" }

Write-Host "`n✅ System ready!" -ForegroundColor Green
Write-Host "📍 Face images location: D:\transit-intelligence-system\test_faces\" -ForegroundColor Cyan
