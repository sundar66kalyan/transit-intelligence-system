# clear_registered_data.ps1
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "CLEARING REGISTERED PASSENGER DATA" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if backend is running
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 2
    Write-Host "✅ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend is not running!" -ForegroundColor Red
    Write-Host "Please start the backend first:" -ForegroundColor Yellow
    Write-Host "cd D:\transit-intelligence-system" -ForegroundColor White
    Write-Host "python backend/production_backend.py" -ForegroundColor White
    exit 1
}

# Try to clear via API
Write-Host "`n🔄 Attempting to clear data..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/clear_data" -Method DELETE -TimeoutSec 5
    Write-Host "✅ Data cleared via API!" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ API clear failed. Restarting backend to clear memory..." -ForegroundColor Yellow
    
    # Kill backend
    Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    
    # Restart backend
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\transit-intelligence-system; Write-Host 'Backend Restarted - Data Cleared!' -ForegroundColor Green; python backend/production_backend.py"
    
    Write-Host "✅ Backend restarted - All data cleared!" -ForegroundColor Green
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "To verify data is cleared, run:" -ForegroundColor Cyan
Write-Host "Invoke-RestMethod -Uri http://localhost:8001/registered_passengers" -ForegroundColor White
