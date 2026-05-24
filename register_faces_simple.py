# register_faces_simple.py
import sys
import os

sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher

# Clear existing faces
face_matcher.clear_all()

# Demo faces directory
faces_dir = "D:/transit-intelligence-system/real_faces"

if os.path.exists(faces_dir):
    for filename in os.listdir(faces_dir):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            passenger_id = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
            image_path = os.path.join(faces_dir, filename)
            
            # Map IDs to names
            name_map = {
                "P001": "John Doe",
                "P002": "Jane Smith", 
                "P003": "Robert Johnson",
                "P004": "Alice Brown"
            }
            name = name_map.get(passenger_id, passenger_id)
            
            print(f"Registering {name} ({passenger_id})...")
            success = face_matcher.register_face(name, passenger_id, image_path)
            
            if success:
                print(f"  ✅ Registered successfully")
            else:
                print(f"  ❌ Failed - no face detected")
else:
    print(f"Faces directory not found: {faces_dir}")
    print("Run: python generate_test_faces.py first")

print(f"\n📊 Total registered: {len(face_matcher.known_face_names)}")
print("\nRegistered faces:")
for face in face_matcher.get_all_registered():
    print(f"  - {face['name']} (ID: {face['passenger_id']})")
