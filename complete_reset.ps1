# complete_reset.ps1
Write-Host "=========================================" -ForegroundColor Red
Write-Host "⚠️  DATA RESET UTILITY" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Red
Write-Host ""

$confirm = Read-Host "Type 'DELETE' to confirm reset"
if ($confirm -ne "DELETE") {
    Write-Host "❌ Reset cancelled" -ForegroundColor Yellow
    exit
}

Write-Host "`n🔄 Resetting data..." -ForegroundColor Yellow

# Method 1: Try API
try {
    $response = Invoke-RestMethod -Method DELETE -Uri "http://localhost:8001/clear_data" -ErrorAction Stop
    Write-Host "✅ API reset successful" -ForegroundColor Green
} catch {
    Write-Host "⚠️ API not accessible, deleting files directly..." -ForegroundColor Yellow
    
    # Delete files directly
    $dataPath = "D:\transit-intelligence-system\data"
    
    if (Test-Path "$dataPath\face_db.pkl") {
        Remove-Item "$dataPath\face_db.pkl" -Force
        Write-Host "✅ Deleted face_db.pkl" -ForegroundColor Green
    }
    
    if (Test-Path "$dataPath\face_images") {
        Remove-Item "$dataPath\face_images\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Deleted face_images" -ForegroundColor Green
    }
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "✅ Data reset complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Restart the backend: python backend/production_backend.py" -ForegroundColor Cyan
