import face_recognition
import os
from PIL import Image
import numpy as np

# Paths
faces_dir = "D:/transit-intelligence-system/test_faces"
known_faces = []
known_names = []

print("="*50)
print("Face Recognition Test")
print("="*50)

# Load known faces
print("\n1. Loading known faces...")
for filename in os.listdir(faces_dir):
    if filename.endswith('.jpg'):
        pid = filename.replace('.jpg', '')
        path = os.path.join(faces_dir, filename)
        
        # Map ID to name
        name_map = {"P001": "John Doe", "P002": "Jane Smith", "P003": "Robert Johnson", "P004": "Alice Brown"}
        name = name_map.get(pid, pid)
        
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)
        
        if encodings:
            known_faces.append(encodings[0])
            known_names.append(name)
            print(f"  ✅ Loaded: {name} ({pid})")
        else:
            print(f"  ❌ No face in: {filename}")

print(f"\n📊 Total known faces: {len(known_faces)}")

# Test matching
print("\n2. Testing face matching...")
for filename in os.listdir(faces_dir):
    if filename.endswith('.jpg'):
        path = os.path.join(faces_dir, filename)
        test_image = face_recognition.load_image_file(path)
        test_encodings = face_recognition.face_encodings(test_image)
        
        if test_encodings:
            results = face_recognition.compare_faces(known_faces, test_encodings[0])
            distances = face_recognition.face_distance(known_faces, test_encodings[0])
            
            if True in results:
                match_index = results.index(True)
                confidence = 1 - distances[match_index]
                print(f"  ✅ {filename}: Matched with {known_names[match_index]} (Confidence: {confidence:.2%})")
            else:
                print(f"  ❌ {filename}: No match found")
        else:
            print(f"  ❌ {filename}: No face detected in test image")

print("\n✅ Test complete!")
