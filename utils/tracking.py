import numpy as np
from typing import List, Dict

class ObjectTracker:
    def __init__(self):
        self.tracks = {}
        self.next_id = 0
        self.max_lost_frames = 30
        self.lost_frames = {}
        
    def update(self, detections: List[Dict], frame_shape: tuple) -> List[Dict]:
        """Simple IoU-based tracking"""
        current_boxes = [d["bbox"] for d in detections]
        tracked_objects = []
        
        for i, box in enumerate(current_boxes):
            matched = False
            for track_id, track_box in self.tracks.items():
                if self._calculate_iou(box, track_box) > 0.5:
                    tracked_objects.append({
                        "id": track_id,
                        "bbox": box,
                        "confidence": detections[i]["confidence"]
                    })
                    self.tracks[track_id] = box
                    self.lost_frames[track_id] = 0
                    matched = True
                    break
            
            if not matched:
                self.tracks[self.next_id] = box
                tracked_objects.append({
                    "id": self.next_id,
                    "bbox": box,
                    "confidence": detections[i]["confidence"]
                })
                self.lost_frames[self.next_id] = 0
                self.next_id += 1
        
        for track_id in list(self.tracks.keys()):
            if track_id not in [t["id"] for t in tracked_objects]:
                self.lost_frames[track_id] = self.lost_frames.get(track_id, 0) + 1
                if self.lost_frames[track_id] > self.max_lost_frames:
                    del self.tracks[track_id]
                    del self.lost_frames[track_id]
        
        return tracked_objects
    
    def _calculate_iou(self, box1, box2):
        """Calculate IoU between two boxes"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
