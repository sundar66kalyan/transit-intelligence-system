# utils/demo_data.py
import os
import cv2
import numpy as np
from datetime import datetime

def create_demo_faces():
    """Create demo face images for testing"""
    demo_faces_dir = "D:/VehicleSurveillanceSystem/demo_faces"
    os.makedirs(demo_faces_dir, exist_ok=True)
    
    # Create sample face images (colored circles with labels)
    demo_passengers = [
        {"name": "John Doe", "id": "P001", "type": "Regular", "color": (0, 255, 0)},
        {"name": "Jane Smith", "id": "P002", "type": "VIP", "color": (255, 0, 0)},
        {"name": "Robert Johnson", "id": "P003", "type": "Staff", "color": (0, 0, 255)},
        {"name": "Alice Brown", "id": "P004", "type": "Student", "color": (255, 255, 0)},
    ]
    
    created_files = []
    for passenger in demo_passengers:
        # Create a synthetic face image
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Draw face (circle)
        cv2.circle(img, (100, 100), 60, passenger["color"], -1)
        cv2.circle(img, (100, 100), 50, (255, 255, 255), -1)
        
        # Draw eyes
        cv2.circle(img, (70, 80), 10, (0, 0, 0), -1)
        cv2.circle(img, (130, 80), 10, (0, 0, 0), -1)
        
        # Draw smile
        cv2.ellipse(img, (100, 120), (30, 20), 0, 0, 180, (0, 0, 0), 3)
        
        # Add label
        cv2.putText(img, passenger["name"][:10], (20, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Save image
        filepath = f"{demo_faces_dir}/{passenger['id']}.jpg"
        cv2.imwrite(filepath, img)
        created_files.append(filepath)
        
        print(f"Created demo face: {passenger['name']} ({passenger['id']})")
    
    return demo_passengers

if __name__ == "__main__":
    create_demo_faces()
