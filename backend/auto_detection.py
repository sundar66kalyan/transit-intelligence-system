# backend/auto_detection.py
from fastapi import FastAPI, File, UploadFile, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import os
import hashlib
import random
import json
import asyncio
from typing import Dict, List, Optional
import threading

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🚌 AI Vehicle Surveillance - Automatic Detection System")
    print("=" * 70)
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/video_frames", exist_ok=True)
    print("✅ AI Agents Initialized")
    print("✅ Automatic Entry/Exit Detection Active")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Auto Detection System", version="8.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ AI AGENTS ============

class FaceRecognitionAgent:
    """AI Agent for automatic face detection and recognition"""
    
    def __init__(self):
        self.registered_faces = {}  # hash -> passenger info
        self.face_cache = {}  # Recent faces for faster matching
        
    def register_face(self, passenger_id: str, name: str, passenger_type: str, image_hash: str, image_path: str):
        self.registered_faces[image_hash] = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "image_hash": image_hash,
            "image_path": image_path,
            "registered_date": datetime.now().isoformat()
        }
        return True
    
    def recognize_face(self, image_hash: str) -> Optional[Dict]:
        """Recognize face from hash"""
        return self.registered_faces.get(image_hash)
    
    def get_all_passengers(self):
        return list(self.registered_faces.values())

class TrackingAgent:
    """AI Agent for tracking passengers in video stream"""
    
    def __init__(self):
        self.active_passengers: Dict[str, Dict] = {}
        self.completed_journeys: List[Dict] = []
        self.vehicle_occupancy = 0
        self.event_logs: List[Dict] = []
        self.last_positions = {}  # Track positions for movement detection
        
    def detect_entry_exit(self, face_id: str, current_position: tuple, frame_width: int, frame_height: int) -> str:
        """Detect if person is entering or exiting based on position"""
        # Define entry zone (bottom area of frame)
        entry_zone_y = frame_height * 0.7
        exit_zone_y = frame_height * 0.3
        
        if face_id in self.last_positions:
            last_y = self.last_positions[face_id][1]
            current_y = current_position[1]
            
            # Moving from bottom to top = Entering
            if last_y > entry_zone_y and current_y < entry_zone_y:
                return "ENTRY"
            # Moving from top to bottom = Exiting  
            elif last_y < exit_zone_y and current_y > exit_zone_y:
                return "EXIT"
        
        self.last_positions[face_id] = current_position
        return "TRACKING"
    
    def process_entry(self, passenger: Dict, location: Dict, bus_id: str) -> Dict:
        """Process automatic entry detection"""
        passenger_id = passenger["passenger_id"]
        current_time = datetime.now()
        
        journey = {
            "passenger_id": passenger_id,
            "passenger_name": passenger["name"],
            "passenger_type": passenger["passenger_type"],
            "entry_time": current_time.isoformat(),
            "entry_location": location,
            "entry_gps": {"lat": location["lat"], "lon": location["lon"]},
            "bus_id": bus_id,
            "status": "IN_VEHICLE",
            "attendance_marked": True
        }
        
        self.active_passengers[passenger_id] = journey
        self.vehicle_occupancy += 1
        
        log = {
            "event_id": f"AUTO_ENTRY_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "event_type": "ENTRY",
            "passenger_name": passenger["name"],
            "passenger_id": passenger_id,
            "location": location["address"],
            "gps": {"lat": location["lat"], "lon": location["lon"]},
            "timestamp": current_time.isoformat(),
            "occupancy_after": self.vehicle_occupancy,
            "auto_detected": True
        }
        self.event_logs.append(log)
        
        return journey
    
    def process_exit(self, passenger_id: str, location: Dict, bus_id: str) -> Optional[Dict]:
        """Process automatic exit detection"""
        if passenger_id not in self.active_passengers:
            return None
        
        journey = self.active_passengers[passenger_id]
        exit_time = datetime.now()
        entry_time = datetime.fromisoformat(journey["entry_time"])
        
        duration_seconds = (exit_time - entry_time).total_seconds()
        duration_minutes = duration_seconds / 60
        
        if duration_minutes < 60:
            duration_str = f"{duration_minutes:.1f} minutes"
        else:
            hours = duration_minutes // 60
            mins = duration_minutes % 60
            duration_str = f"{int(hours)}h {int(mins)}m"
        
        completed = {
            **journey,
            "exit_time": exit_time.isoformat(),
            "exit_location": location,
            "exit_gps": {"lat": location["lat"], "lon": location["lon"]},
            "journey_duration_seconds": duration_seconds,
            "journey_duration": duration_str,
            "status": "COMPLETED"
        }
        
        self.completed_journeys.append(completed)
        del self.active_passengers[passenger_id]
        self.vehicle_occupancy = max(0, self.vehicle_occupancy - 1)
        
        log = {
            "event_id": f"AUTO_EXIT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "event_type": "EXIT",
            "passenger_name": journey["passenger_name"],
            "passenger_id": passenger_id,
            "entry_location": journey["entry_location"]["address"],
            "exit_location": location["address"],
            "journey_duration": duration_str,
            "timestamp": exit_time.isoformat(),
            "occupancy_after": self.vehicle_occupancy,
            "auto_detected": True
        }
        self.event_logs.append(log)
        
        return completed
    
    def get_current_occupancy(self) -> int:
        return self.vehicle_occupancy
    
    def get_active_passengers(self) -> List[Dict]:
        return list(self.active_passengers.values())
    
    def get_recent_events(self, limit=50) -> List[Dict]:
        return self.event_logs[-limit:]

class AlertAgent:
    """AI Agent for security alerts"""
    
    def __init__(self):
        self.alerts = []
        
    def trigger_alert(self, alert_type: str, message: str, location: Dict, passenger_info: Dict = None):
        alert = {
            "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": alert_type,
            "severity": "HIGH",
            "message": message,
            "location": location["address"],
            "gps": {"lat": location["lat"], "lon": location["lon"]},
            "passenger_info": passenger_info,
            "timestamp": datetime.now().isoformat(),
            "status": "ACTIVE"
        }
        self.alerts.append(alert)
        return alert
    
    def get_active_alerts(self):
        return [a for a in self.alerts if a["status"] == "ACTIVE"]

# Initialize Agents
face_agent = FaceRecognitionAgent()
tracking_agent = TrackingAgent()
alert_agent = AlertAgent()

# Simulated GPS locations
GPS_LOCATIONS = [
    {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
]

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

# WebSocket connections for live video
active_connections = []

@app.websocket("/ws/video_feed")
async def websocket_video_feed(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "connected", "timestamp": datetime.now().isoformat()})
    except:
        active_connections.remove(websocket)

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "message": "AI Vehicle Surveillance - Automatic Detection",
        "status": "running",
        "registered_passengers": len(face_agent.get_all_passengers()),
        "current_occupancy": tracking_agent.get_current_occupancy(),
        "auto_detection": "ACTIVE"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/register_passenger")
async def register_passenger(
    name: str = Form(...),
    passenger_id: str = Form(...),
    passenger_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Register new passenger"""
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        
        face_path = f"D:/VehicleSurveillanceSystem/data/face_images/{passenger_id}.jpg"
        with open(face_path, "wb") as f:
            f.write(contents)
        
        face_agent.register_face(passenger_id, name, passenger_type, image_hash, face_path)
        
        return {
            "status": "success",
            "message": f"✅ {name} registered successfully!",
            "passenger": {"name": name, "id": passenger_id, "type": passenger_type}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/auto_detect")
async def auto_detect_person(file: UploadFile = File(...), bus_id: str = Form("BUS-001")):
    """Automatic detection of person entering/exiting from video frame"""
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        
        # Simulate current GPS location
        current_location = random.choice(GPS_LOCATIONS)
        
        # Recognize face
        passenger = face_agent.recognize_face(image_hash)
        
        if passenger:
            # Check if passenger is already in vehicle
            is_in_vehicle = any(p["passenger_id"] == passenger["passenger_id"] 
                               for p in tracking_agent.get_active_passengers())
            
            if not is_in_vehicle:
                # ENTRY detected
                journey = tracking_agent.process_entry(passenger, current_location, bus_id)
                return {
                    "status": "success",
                    "event": "ENTRY",
                    "message": f"✅ {passenger['name']} entered automatically!",
                    "passenger": passenger,
                    "location": current_location,
                    "current_occupancy": tracking_agent.get_current_occupancy(),
                    "attendance": "PRESENT"
                }
            else:
                # EXIT detected
                completed = tracking_agent.process_exit(passenger["passenger_id"], current_location, bus_id)
                if completed:
                    return {
                        "status": "success",
                        "event": "EXIT",
                        "message": f"✅ {passenger['name']} exited automatically!",
                        "passenger": passenger,
                        "exit_location": current_location,
                        "journey_duration": completed["journey_duration"],
                        "current_occupancy": tracking_agent.get_current_occupancy()
                    }
        else:
            # Unknown person - Trigger alert
            alert = alert_agent.trigger_alert(
                "UNAUTHORIZED_PERSON",
                f"🚨 Unknown person detected at {current_location['address']}!",
                current_location
            )
            return {
                "status": "warning",
                "event": "UNAUTHORIZED",
                "message": f"🚨 ALERT: Unknown person detected!",
                "alert": alert,
                "location": current_location,
                "current_occupancy": tracking_agent.get_current_occupancy()
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/process_video_frame")
async def process_video_frame(file: UploadFile = File(...), bus_id: str = Form("BUS-001")):
    """Process video frame for automatic detection"""
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        
        current_location = random.choice(GPS_LOCATIONS)
        passenger = face_agent.recognize_face(image_hash)
        
        if passenger:
            is_in_vehicle = any(p["passenger_id"] == passenger["passenger_id"] 
                               for p in tracking_agent.get_active_passengers())
            
            event_type = "EXIT" if is_in_vehicle else "ENTRY"
            
            if event_type == "ENTRY":
                tracking_agent.process_entry(passenger, current_location, bus_id)
                return {"event": "ENTRY", "passenger": passenger, "location": current_location}
            else:
                tracking_agent.process_exit(passenger["passenger_id"], current_location, bus_id)
                return {"event": "EXIT", "passenger": passenger, "location": current_location}
        
        return {"event": "UNKNOWN", "location": current_location}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vehicle_status")
async def vehicle_status():
    return {
        "current_occupancy": tracking_agent.get_current_occupancy(),
        "active_passengers": tracking_agent.get_active_passengers(),
        "recent_events": tracking_agent.get_recent_events(20),
        "active_alerts": len(alert_agent.get_active_alerts()),
        "total_registered": len(face_agent.get_all_passengers())
    }

@app.get("/active_passengers")
async def get_active_passengers():
    return {"count": len(tracking_agent.get_active_passengers()), "passengers": tracking_agent.get_active_passengers()}

@app.get("/journey_history")
async def get_journey_history():
    return {"journeys": tracking_agent.completed_journeys[-50:], "count": len(tracking_agent.completed_journeys)}

@app.get("/recent_events")
async def get_recent_events():
    return {"events": tracking_agent.get_recent_events(50)}

@app.get("/active_alerts")
async def get_active_alerts():
    return {"alerts": alert_agent.get_active_alerts()}

@app.get("/registered_passengers")
async def get_registered_passengers():
    return {"passengers": face_agent.get_all_passengers()}

@app.delete("/clear_data")
async def clear_data():
    face_agent.registered_faces = {}
    tracking_agent.active_passengers = {}
    tracking_agent.completed_journeys = []
    tracking_agent.vehicle_occupancy = 0
    tracking_agent.event_logs = []
    alert_agent.alerts = []
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
