# generate_test_faces.py
import cv2
import numpy as np
from PIL import Image, ImageDraw
import os

def create_test_face(name, passenger_id, output_path):
    """Create a simple test face image with basic facial features"""
    
    # Create blank image
    img = Image.new('RGB', (200, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw face circle
    draw.ellipse([50, 50, 150, 170], fill=(255, 220, 200), outline=(0, 0, 0), width=2)
    
    # Draw eyes
    draw.ellipse([70, 85, 85, 100], fill=(0, 0, 0))
    draw.ellipse([115, 85, 130, 100], fill=(0, 0, 0))
    
    # Draw smile
    draw.arc([75, 110, 125, 140], start=0, end=180, fill=(0, 0, 0), width=3)
    
    # Draw eyebrows
    draw.line([70, 75, 85, 78], fill=(0, 0, 0), width=3)
    draw.line([115, 78, 130, 75], fill=(0, 0, 0), width=3)
    
    # Add name text
    draw.text((50, 180), name, fill=(0, 0, 0))
    
    # Save image
    img.save(output_path)
    print(f"Created: {output_path}")
    return output_path

# Create test faces
test_faces = [
    ("John Doe", "P001"),
    ("Jane Smith", "P002"),
    ("Robert Johnson", "P003"),
    ("Alice Brown", "P004"),
]

output_dir = "D:/transit-intelligence-system/real_faces"
os.makedirs(output_dir, exist_ok=True)

for name, pid in test_faces:
    path = f"{output_dir}/{pid}.jpg"
    create_test_face(name, pid, path)

print(f"\n✅ Created {len(test_faces)} test faces in {output_dir}")
