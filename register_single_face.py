# register_single_face.py
import sys
import argparse
from pathlib import Path

sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher

def register_face(name, passenger_id, image_path):
    """Register a single face"""
    print(f"\n📸 Registering face for {name} (ID: {passenger_id})")
    print(f"📁 Image: {image_path}")
    
    # Check if image exists
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return False
    
    # Load existing encodings
    face_matcher.load_encodings()
    
    # Register the face
    success = face_matcher.register_face(name, passenger_id, image_path, is_bytes=False)
    
    if success:
        print(f"✅ Successfully registered {name}")
        print(f"📊 Total registered faces: {len(face_matcher.known_face_names)}")
    else:
        print(f"❌ Failed to register {name}. No face detected in image.")
    
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Register a face for recognition')
    parser.add_argument('--name', required=True, help='Person name')
    parser.add_argument('--id', required=True, help='Passenger ID')
    parser.add_argument('--image', required=True, help='Path to face image')
    
    args = parser.parse_args()
    register_face(args.name, args.id, args.image)
