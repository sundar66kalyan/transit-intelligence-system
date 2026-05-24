# test_face_match.py
import sys
import argparse
from pathlib import Path

sys.path.append('D:/transit-intelligence-system')
from utils.face_matcher import face_matcher

def test_face_match(image_path):
    """Test face matching on an image"""
    print(f"\n🔍 Testing face match for: {image_path}")
    
    # Load encodings
    face_matcher.load_encodings()
    
    if len(face_matcher.known_face_encodings) == 0:
        print("❌ No registered faces in database")
        print("Please register faces first using: python register_single_face.py")
        return
    
    # Load and encode image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Match face
    result = face_matcher.match_face(image_bytes)
    
    print("\n" + "="*50)
    if result["matched"]:
        print("✅ FACE MATCHED!")
        print(f"   Name: {result['name']}")
        print(f"   ID: {result['passenger_id']}")
        print(f"   Confidence: {result['confidence']}%")
    else:
        print("❌ NO MATCH FOUND!")
        print(f"   Reason: {result['reason']}")
        if result.get('confidence'):
            print(f"   Confidence: {result['confidence']:.2%}")
        if result.get('closest_match'):
            print(f"   Closest match: {result['closest_match']}")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test face matching')
    parser.add_argument('--image', required=True, help='Path to test image')
    
    args = parser.parse_args()
    test_face_match(args.image)
