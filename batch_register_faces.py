# batch_register_faces.py
import sys
import os
from pathlib import Path

sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher

def batch_register(folder_path):
    """Register all faces in a folder"""
    print(f"\n📁 Scanning folder: {folder_path}")
    
    # Load existing encodings
    face_matcher.load_encodings()
    
    # Supported image formats
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # Find all images
    images = []
    for ext in image_extensions:
        images.extend(Path(folder_path).glob(f"*{ext}"))
        images.extend(Path(folder_path).glob(f"*{ext.upper()}"))
    
    print(f"📸 Found {len(images)} images")
    
    registered_count = 0
    failed_count = 0
    
    for img_path in images:
        # Extract name from filename (remove extension)
        name = img_path.stem.replace('_', ' ').title()
        passenger_id = f"P{registered_count + 1:03d}"
        
        print(f"\n📝 Registering: {name} (ID: {passenger_id})")
        
        success = face_matcher.register_face(name, passenger_id, str(img_path), is_bytes=False)
        
        if success:
            registered_count += 1
            print(f"   ✅ Registered successfully")
        else:
            failed_count += 1
            print(f"   ❌ Failed - No face detected")
    
    print(f"\n" + "="*50)
    print(f"✅ Successfully registered: {registered_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total in database: {len(face_matcher.known_face_names)}")
    print("="*50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Batch register faces from folder')
    parser.add_argument('--folder', required=True, help='Folder containing face images')
    
    args = parser.parse_args()
    batch_register(args.folder)
