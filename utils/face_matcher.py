import face_recognition
import cv2
import numpy as np
from PIL import Image
import io
import os
import pickle

class FaceMatcher:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.known_face_genders = []
        self.known_face_types = []
        self.db_path = "D:/transit-intelligence-system/data/face_db.pkl"
        self.load_database()
    
    def load_database(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "rb") as f:
                    data = pickle.load(f)
                self.known_face_encodings = data.get("encodings", [])
                self.known_face_names = data.get("names", [])
                self.known_face_ids = data.get("ids", [])
                self.known_face_genders = data.get("genders", [])
                self.known_face_types = data.get("types", [])
                print(f"Loaded {len(self.known_face_names)} faces")
            except:
                print("No existing database")
    
    def save_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        data = {
            "encodings": self.known_face_encodings,
            "names": self.known_face_names,
            "ids": self.known_face_ids,
            "genders": self.known_face_genders,
            "types": self.known_face_types
        }
        with open(self.db_path, "wb") as f:
            pickle.dump(data, f)
        print(f"Saved {len(self.known_face_names)} faces")
    
    def register_face(self, image_bytes, name, passenger_id, gender, passenger_type):
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(image)
            face_encodings = face_recognition.face_encodings(image_np)
            if not face_encodings:
                return False, "No face detected"
            self.known_face_encodings.append(face_encodings[0])
            self.known_face_names.append(name)
            self.known_face_ids.append(passenger_id)
            self.known_face_genders.append(gender)
            self.known_face_types.append(passenger_type)
            self.save_database()
            return True, "Face registered"
        except Exception as e:
            return False, str(e)
    
    def match_face(self, image_bytes, threshold=0.5):
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(image)
            face_encodings = face_recognition.face_encodings(image_np)
            if not face_encodings:
                return {"matched": False, "reason": "No face detected"}
            if len(self.known_face_encodings) == 0:
                return {"matched": False, "reason": "No registered faces"}
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encodings[0])
            best_match_index = np.argmin(face_distances)
            confidence = 1 - face_distances[best_match_index]
            if confidence >= threshold:
                return {
                    "matched": True,
                    "name": self.known_face_names[best_match_index],
                    "passenger_id": self.known_face_ids[best_match_index],
                    "gender": self.known_face_genders[best_match_index],
                    "passenger_type": self.known_face_types[best_match_index],
                    "confidence": round(confidence * 100, 2)
                }
            else:
                return {
                    "matched": False,
                    "reason": f"Face not recognized",
                    "confidence": round(confidence * 100, 2)
                }
        except Exception as e:
            return {"matched": False, "reason": str(e)}

face_matcher = FaceMatcher()
