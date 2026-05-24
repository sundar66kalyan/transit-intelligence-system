# test_match.py
import sys
import os

sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher

# Test matching with the same faces
test_dir = "D:/transit-intelligence-system/real_faces"

print("="*50)
print("Testing Face Matching")
print("="*50)

for filename in os.listdir(test_dir):
    if filename.endswith('.jpg'):
        passenger_id = filename.replace('.jpg', '')
        
        with open(os.path.join(test_dir, filename), 'rb') as f:
            image_bytes = f.read()
        
        result = face_matcher.match_face(image_bytes)
        
        if result.get("matched"):
            print(f"✅ {filename}: Matched with {result['name']} (Confidence: {result['confidence']}%)")
        else:
            print(f"❌ {filename}: {result.get('reason')}")
