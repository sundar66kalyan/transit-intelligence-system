# face_utils.ps1 - Face Recognition Utility Commands

function Register-Face {
    param(
        [string]$Name,
        [string]$ID,
        [string]$ImagePath
    )
    Write-Host "📸 Registering face for $Name..." -ForegroundColor Cyan
    python D:\transit-intelligence-system\register_single_face.py --name "$Name" --id "$ID" --image "$ImagePath"
}

function Test-FaceMatch {
    param([string]$ImagePath)
    Write-Host "🔍 Testing face match..." -ForegroundColor Cyan
    python D:\transit-intelligence-system\test_face_match.py --image "$ImagePath"
}

function Batch-RegisterFaces {
    param([string]$FolderPath)
    Write-Host "📁 Batch registering faces from $FolderPath..." -ForegroundColor Cyan
    python D:\transit-intelligence-system\batch_register_faces.py --folder "$FolderPath"
}

function Get-RegisteredFaces {
    Write-Host "📋 Registered faces:" -ForegroundColor Cyan
    python -c "
import sys
sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher
face_matcher.load_encodings()
faces = face_matcher.get_all_registered()
if faces:
    for f in faces:
        print(f'  - {f[\"name\"]} (ID: {f[\"passenger_id\"]})')
else:
    print('  No faces registered')
"
}

function Clear-Faces {
    Write-Host "🗑️ Clearing all face data..." -ForegroundColor Red
    python -c "
import sys
sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher
face_matcher.clear_all()
print('✅ All face data cleared')
"
}

# Export functions
Export-ModuleMember -Function Register-Face, Test-FaceMatch, Batch-RegisterFaces, Get-RegisteredFaces, Clear-Faces

Write-Host "✅ Face utility commands loaded!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  Register-Face -Name 'John Doe' -ID 'P001' -ImagePath 'C:\face.jpg'"
Write-Host "  Test-FaceMatch -ImagePath 'C:\test.jpg'"
Write-Host "  Batch-RegisterFaces -FolderPath 'D:\faces\'"
Write-Host "  Get-RegisteredFaces"
Write-Host "  Clear-Faces"
