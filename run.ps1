Write-Host "Starting Vehicle Surveillance System..." -ForegroundColor Cyan
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\VehicleSurveillanceSystem; python -m backend.main"

Start-Sleep -Seconds 3

# Start frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\VehicleSurveillanceSystem; streamlit run frontend/app.py"

Write-Host "✅ System started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Dashboard: http://localhost:8501" -ForegroundColor Yellow
