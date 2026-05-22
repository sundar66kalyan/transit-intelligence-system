import cv2
import numpy as np
from typing import Optional, Dict
import os
import pickle

class FaceRecognizer:
    def __init__(self):
        self.face_analyzer = None
        self.registered_faces = {}
        self.threshold = 0.6
        self.load_face_model()
    
    def load_face_model(self):
        """Load InsightFace model"""
        try:
            import insightface
            self.face_analyzer = insightface.app.FaceAnalysis(name="buffalo_l")
            self.face_analyzer.prepare(ctx_id=-1, det_size=(640, 640))
            print("✅ Loaded InsightFace model")
        except Exception as e:
            print(f"⚠️ Could not load InsightFace: {e}")
            self.face_analyzer = None
    
    def extract_face(self, frame, bbox):
        """Extract face from bounding box"""
        if self.face_analyzer is None:
            return None
        
        try:
            x1, y1, x2, y2 = map(int, bbox)
            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size == 0:
                return None
            
            faces = self.face_analyzer.get(face_crop)
            if len(faces) > 0:
                return faces[0].normed_embedding
            return None
        except Exception as e:
            print(f"Face extraction error: {e}")
            return None
    
    def match_identity(self, embedding):
        """Match face embedding against registered faces"""
        if not self.registered_faces:
            return "Unknown"
        
        best_match = "Unknown"
        best_similarity = 0
        
        for name, reg_embedding in self.registered_faces.items():
            similarity = np.dot(embedding, reg_embedding)
            if similarity > best_similarity and similarity > self.threshold:
                best_similarity = similarity
                best_match = name
        
        return best_match
    
    def load_registered_faces(self, face_db_path):
        """Load pre-registered face embeddings"""
        if not os.path.exists(face_db_path):
            os.makedirs(face_db_path)
            return
        
        for file in os.listdir(face_db_path):
            if file.endswith(".pkl"):
                with open(os.path.join(face_db_path, file), "rb") as f:
                    embedding = pickle.load(f)
                    name = file.replace(".pkl", "")
                    self.registered_faces[name] = embedding
        print(f"✅ Loaded {len(self.registered_faces)} registered faces")
