import face_recognition
from PIL import Image
import numpy as np
import os

def test_face_detection(image_path):
    print(f"\nTesting image: {image_path}")
    
    # Load image
    image = face_recognition.load_image_file(image_path)
    
    # Detect faces
    face_locations = face_recognition.face_locations(image)
    
    if face_locations:
        print(f"  ✅ Found {len(face_locations)} face(s)")
        for i, location in enumerate(face_locations):
            top, right, bottom, left = location
            print(f"     Face {i+1}: Top={top}, Right={right}, Bottom={bottom}, Left={left}")
        
        # Get encoding
        encodings = face_recognition.face_encodings(image, face_locations)
        if encodings:
            print(f"  ✅ Face encoding successful")
            return True
    else:
        print(f"  ❌ No face detected in image")
        
        # Try with enhanced image
        print(f"  🔄 Trying with enhanced image...")
        from PIL import ImageEnhance
        
        pil_image = Image.open(image_path)
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Convert back
        import io
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        import numpy as np
        enhanced_img = face_recognition.load_image_file(img_bytes)
        face_locations = face_recognition.face_locations(enhanced_img)
        
        if face_locations:
            print(f"  ✅ Found {len(face_locations)} face(s) after enhancement")
            return True
        else:
            print(f"  ❌ Still no face detected. Please use a clearer face image.")
    
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("Face Detection Test")
    print("=" * 50)
    
    # Test with a sample image if available
    test_image = input("Enter path to test image (or press Enter to skip): ").strip()
    
    if test_image and os.path.exists(test_image):
        test_face_detection(test_image)
    else:
        print("\nPlease use a clear frontal face image for registration.")
        print("Tips for better face detection:")
        print("  - Use good lighting")
        print("  - Face should be clearly visible")
        print("  - Look directly at camera")
        print("  - Remove glasses if possible")
        print("  - Use high resolution image")
