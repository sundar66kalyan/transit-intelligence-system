# Simple Face Utility Commands

function Register-Face {
    param($Name, $ID, $ImagePath)
    python -c "
import sys
sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher
success = face_matcher.register_face('$Name', '$ID', r'$ImagePath')
print(f'✅ Registered {success and `$Name or `"Failed`"}')
"
}

function Test-Face {
    param($ImagePath)
    python -c "
import sys
sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher
with open(r'$ImagePath', 'rb') as f:
    result = face_matcher.match_face(f.read())
if result.get('matched'):
    print(f'✅ MATCH: {result[\"name\"]} ({result[\"confidence\"]}%)')
else:
    print(f'❌ No match: {result.get(\"reason\")}')
"
}

function List-Faces {
    python -c "
import sys
sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher
faces = face_matcher.get_all_registered()
print(f'Total faces: {len(faces)}')
for f in faces:
    print(f'  - {f[\"name\"]} (ID: {f[\"passenger_id\"]})')
"
}

function Clear-Faces {
    python -c "
import sys
sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher
face_matcher.clear_all()
print('✅ All faces cleared')
"
}

Write-Host "✅ Face utilities loaded!" -ForegroundColor Green
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  Register-Face -Name 'John' -ID 'P001' -ImagePath 'D:\face.jpg'"
Write-Host "  Test-Face -ImagePath 'D:\test.jpg'"
Write-Host "  List-Faces"
Write-Host "  Clear-Faces"
