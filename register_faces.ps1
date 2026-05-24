# register_faces.ps1
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "📸 FACE REGISTRATION UTILITY" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Add Python path
$env:PYTHONPATH = "D:\transit-intelligence-system"

python -c "
import sys
sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher
import os

# Load existing encodings
face_matcher.load_encodings()

print('\n📋 Current registered faces:')
registered = face_matcher.get_all_registered()
if registered:
    for r in registered:
        print(f'  - {r[\"name\"]} (ID: {r[\"passenger_id\"]})')
else:
    print('  No faces registered yet')

print('\n📝 To register a new face, use:')
print('  python register_single_face.py --name \"Person Name\" --id \"P001\" --image \"path/to/face.jpg\"')
"

Write-Host "`n✅ Face matcher ready!" -ForegroundColor Green
