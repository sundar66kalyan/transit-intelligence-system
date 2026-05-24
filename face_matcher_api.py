# face_matcher_api.py
import face_recognition
import os
import pickle
import json
from datetime import datetime

class FaceMatcherAPI:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.db_path = "D:/transit-intelligence-system/data/face_db.pkl"
        self.load_faces()
    
    def load_faces(self):
        """Load all faces from test_faces directory"""
        faces_dir = "D:/transit-intelligence-system/test_faces"
        
        if not os.path.exists(faces_dir):
            print(f"Directory not found: {faces_dir}")
            return
        
        name_map = {
            "P001": "John Doe",
            "P002": "Jane Smith",
            "P003": "Robert Johnson", 
            "P004": "Alice Brown",
            "P005": "Michael Lee",
            "P006": "Sarah Wilson"
        }
        
        for filename in os.listdir(faces_dir):
            if filename.endswith('.jpg'):
                filepath = os.path.join(faces_dir, filename)
                passenger_id = filename.replace('.jpg', '')
                name = name_map.get(passenger_id, "Unknown")
                
                image = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    self.known_ids.append(passenger_id)
                    print(f"Loaded: {name} ({passenger_id})")
        
        self.save_db()
        print(f"Total faces loaded: {len(self.known_encodings)}")
    
    def save_db(self):
        """Save face database to file"""
        data = {
            "encodings": self.known_encodings,
            "names": self.known_names,
            "ids": self.known_ids,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.db_path, 'wb') as f:
            pickle.dump(data, f)
        print(f"Database saved to {self.db_path}")
    
    def match_face(self, image_bytes):
        """Match a face from image bytes"""
        import numpy as np
        from PIL import Image
        import io
        
        # Convert bytes to image
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        # Get face encodings
        test_encodings = face_recognition.face_encodings(image_np)
        
        if not test_encodings:
            return {"matched": False, "reason": "No face detected"}
        
        if len(self.known_encodings) == 0:
            return {"matched": False, "reason": "No registered faces"}
        
        # Compare with known faces
        results = face_recognition.compare_faces(self.known_encodings, test_encodings[0])
        face_distances = face_recognition.face_distance(self.known_encodings, test_encodings[0])
        
        if True in results:
            match_index = results.index(True)
            confidence = 1 - face_distances[match_index]
            
            return {
                "matched": True,
                "name": self.known_names[match_index],
                "passenger_id": self.known_ids[match_index],
                "confidence": round(confidence * 100, 2)
            }
        else:
            return {"matched": False, "reason": "No matching face found"}

# Initialize the API
if __name__ == "__main__":
    api = FaceMatcherAPI()
    
    # Test with a sample image
    test_path = "D:/transit-intelligence-system/test_faces/P001.jpg"
    if os.path.exists(test_path):
        with open(test_path, 'rb') as f:
            result = api.match_face(f.read())
        print(f"\nTest result: {result}")
