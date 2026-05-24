import os
import cv2
import numpy as np
from PIL import Image, ImageDraw

# Create directories
os.makedirs("D:/transit-intelligence-system/test_faces", exist_ok=True)
os.makedirs("D:/transit-intelligence-system/real_faces", exist_ok=True)

def create_face_image(name, person_id, output_path):
    """Create a recognizable face image"""
    # Create blank image
    img = Image.new('RGB', (200, 200), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Face outline (circle)
    draw.ellipse([60, 40, 140, 160], fill=(255, 220, 180), outline=(100, 100, 100), width=2)
    
    # Left eye
    draw.ellipse([75, 75, 90, 90], fill=(0, 0, 0))
    draw.ellipse([78, 78, 87, 87], fill=(255, 255, 255))
    
    # Right eye
    draw.ellipse([110, 75, 125, 90], fill=(0, 0, 0))
    draw.ellipse([113, 78, 122, 87], fill=(255, 255, 255))
    
    # Nose
    draw.polygon([(95, 95), (100, 110), (105, 95)], fill=(200, 180, 160))
    
    # Mouth (smile)
    draw.arc([80, 115, 120, 135], start=0, end=180, fill=(0, 0, 0), width=2)
    
    # Eyebrows
    draw.line([70, 70, 85, 72], fill=(0, 0, 0), width=2)
    draw.line([115, 72, 130, 70], fill=(0, 0, 0), width=2)
    
    # Add name text
    draw.text((60, 175), name, fill=(0, 0, 0))
    draw.text((60, 185), f"ID: {person_id}", fill=(100, 100, 100))
    
    # Save image
    img.save(output_path)
    print(f"Created: {output_path}")

# Create test faces
test_persons = [
    ("John Doe", "P001"),
    ("Jane Smith", "P002"),
    ("Robert Johnson", "P003"),
    ("Alice Brown", "P004"),
    ("Michael Lee", "P005"),
    ("Sarah Wilson", "P006"),
]

print("=" * 50)
print("Creating Face Images")
print("=" * 50)

for name, pid in test_persons:
    path = f"D:/transit-intelligence-system/test_faces/{pid}.jpg"
    create_face_image(name, pid, path)
    # Also copy to real_faces
    import shutil
    shutil.copy(path, f"D:/transit-intelligence-system/real_faces/{pid}.jpg")

print(f"\n✅ Created {len(test_persons)} face images")
print(f"📁 Location: D:/transit-intelligence-system/test_faces/")
