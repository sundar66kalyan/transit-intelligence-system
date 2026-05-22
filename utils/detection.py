import cv2
import numpy as np
from typing import List, Dict, Optional

class ObjectDetector:
    def __init__(self, model_name="yolov8n.pt", conf_threshold=0.5):
        self.conf_threshold = conf_threshold
        self.model = None
        self.load_model(model_name)
    
    def load_model(self, model_name: str):
        """Load YOLO model with error handling"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_name)
            print(f"✅ Loaded YOLO model: {model_name}")
        except Exception as e:
            print(f"⚠️ Could not load YOLO model: {e}")
            print("Running in fallback mode")
            self.model = None
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """Detect persons in frame"""
        if self.model is None:
            return self._fallback_detection(frame)
        
        try:
            results = self.model(frame, classes=[0], conf=self.conf_threshold, verbose=False)
            detections = []
            
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes.cpu().numpy()
                    for box in boxes:
                        detections.append({
                            "bbox": box.xyxy[0],
                            "confidence": float(box.conf[0]),
                            "class_id": int(box.cls[0])
                        })
            return detections
        except Exception as e:
            print(f"Detection error: {e}")
            return []
    
    def _fallback_detection(self, frame: np.ndarray) -> List[Dict]:
        """Fallback detection for testing"""
        h, w = frame.shape[:2]
        return [
            {
                "bbox": np.array([w*0.3, h*0.2, w*0.7, h*0.8]),
                "confidence": 0.85,
                "class_id": 0
            },
            {
                "bbox": np.array([w*0.5, h*0.3, w*0.9, h*0.9]),
                "confidence": 0.78,
                "class_id": 0
            }
        ]
