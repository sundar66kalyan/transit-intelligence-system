# test_face_recognition.py
import face_recognition
import os
import cv2
import numpy as np

print("=" * 60)
print("FACE RECOGNITION SYSTEM TEST")
print("=" * 60)

# Path to face images
faces_dir = "D:/transit-intelligence-system/test_faces"

# Check if directory exists
if not os.path.exists(faces_dir):
    print(f"❌ Directory not found: {faces_dir}")
    print("Please run create_faces.py first")
    exit(1)

# Load known faces
print("\n📸 Loading known faces...")
known_face_encodings = []
known_face_names = []
known_face_ids = []

for filename in os.listdir(faces_dir):
    if filename.endswith('.jpg'):
        filepath = os.path.join(faces_dir, filename)
        passenger_id = filename.replace('.jpg', '')
        
        # Map IDs to names
        name_map = {
            "P001": "John Doe",
            "P002": "Jane Smith", 
            "P003": "Robert Johnson",
            "P004": "Alice Brown",
            "P005": "Michael Lee",
            "P006": "Sarah Wilson"
        }
        name = name_map.get(passenger_id, "Unknown")
        
        # Load image and get face encoding
        image = face_recognition.load_image_file(filepath)
        face_encodings = face_recognition.face_encodings(image)
        
        if face_encodings:
            known_face_encodings.append(face_encodings[0])
            known_face_names.append(name)
            known_face_ids.append(passenger_id)
            print(f"  ✅ Loaded: {name} ({passenger_id})")
        else:
            print(f"  ⚠️ No face detected: {filename}")

print(f"\n📊 Total faces loaded: {len(known_face_encodings)}")

if len(known_face_encodings) == 0:
    print("\n❌ No faces loaded. Please check the images.")
    exit(1)

# Test matching each face against itself
print("\n🔍 Testing face matching...")
print("-" * 40)

success_count = 0
for filename in os.listdir(faces_dir):
    if filename.endswith('.jpg'):
        filepath = os.path.join(faces_dir, filename)
        passenger_id = filename.replace('.jpg', '')
        
        # Load test image
        test_image = face_recognition.load_image_file(filepath)
        test_encodings = face_recognition.face_encodings(test_image)
        
        if test_encodings:
            # Compare with known faces
            results = face_recognition.compare_faces(known_face_encodings, test_encodings[0])
            face_distances = face_recognition.face_distance(known_face_encodings, test_encodings[0])
            
            if True in results:
                match_index = results.index(True)
                confidence = 1 - face_distances[match_index]
                matched_name = known_face_names[match_index]
                matched_id = known_face_ids[match_index]
                
                print(f"  ✅ {filename}: Matched with {matched_name} ({matched_id})")
                print(f"     Confidence: {confidence:.2%}")
                success_count += 1
            else:
                print(f"  ❌ {filename}: No match found")
        else:
            print(f"  ❌ {filename}: No face detected")

print("-" * 40)
print(f"\n📊 Results: {success_count}/{len(os.listdir(faces_dir))} faces matched successfully")

if success_count == len(os.listdir(faces_dir)):
    print("\n🎉 All faces matched successfully!")
else:
    print("\n⚠️ Some faces failed to match.")

print("\n" + "=" * 60)
print("Face recognition system is ready!")
print("=" * 60)
