# backend/multi_camera_system.py (Updated)
from fastapi import FastAPI, File, UploadFile, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
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
from collections import defaultdict

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 80)
    print("🚌 MULTI-CAMERA VEHICLE SURVEILLANCE SYSTEM")
    print("=" * 80)
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    print("✅ Multi-Camera Support Enabled")
    print("✅ AI Agents Initialized")
    print("📡 Server: http://localhost:8001")
    print("=" * 80)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Multi-Camera Vehicle System", version="10.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ DATABASE ============
class PassengerDatabase:
    def __init__(self):
        self.registered_passengers = {}
        self.face_hashes = {}
        
    def register_passenger(self, passenger_id: str, name: str, passenger_type: str, image_hash: str, image_path: str):
        self.registered_passengers[passenger_id] = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "image_hash": image_hash,
            "face_image_path": image_path,
            "registered_date": datetime.now().isoformat(),
            "total_journeys": 0
        }
        self.face_hashes[image_hash] = passenger_id
        return True
    
    def find_passenger_by_hash(self, image_hash: str):
        passenger_id = self.face_hashes.get(image_hash)
        if passenger_id:
            return self.registered_passengers.get(passenger_id)
        return None
    
    def get_all_passengers(self):
        return list(self.registered_passengers.values())

# ============ AI TRACKING AGENT ============
class TrackingAgent:
    def __init__(self):
        self.active_sessions = {}
        self.completed_journeys = []
        self.vehicle_occupancy = 0
        self.entry_logs = []
        self.exit_logs = []
        self.scan_history = []  # Store recent scans for display
        
    def process_entry(self, passenger: Dict, location: Dict, camera_id: str, bus_id: str):
        passenger_id = passenger["passenger_id"]
        current_time = datetime.now()
        
        session = {
            "session_id": f"SES_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "passenger_id": passenger_id,
            "passenger_name": passenger["name"],
            "passenger_type": passenger["passenger_type"],
            "entry_time": current_time.isoformat(),
            "entry_location": location,
            "entry_gps": {"lat": location["lat"], "lon": location["lon"]},
            "entry_camera": camera_id,
            "bus_id": bus_id,
            "status": "IN_VEHICLE",
            "attendance": "PRESENT"
        }
        
        self.active_sessions[passenger_id] = session
        self.vehicle_occupancy += 1
        
        entry_record = {
            "event_id": f"ENTRY_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "event_type": "ENTRY",
            "passenger_name": passenger["name"],
            "passenger_id": passenger_id,
            "camera_id": camera_id,
            "location": location["address"],
            "gps": {"lat": location["lat"], "lon": location["lon"]},
            "timestamp": current_time.isoformat(),
            "occupancy_after": self.vehicle_occupancy
        }
        self.entry_logs.append(entry_record)
        self.scan_history.append(entry_record)
        
        return session
    
    def process_exit(self, passenger_id: str, location: Dict, camera_id: str, bus_id: str):
        if passenger_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[passenger_id]
        exit_time = datetime.now()
        entry_time = datetime.fromisoformat(session["entry_time"])
        
        duration_seconds = (exit_time - entry_time).total_seconds()
        duration_minutes = duration_seconds / 60
        
        if duration_minutes < 60:
            duration_str = f"{duration_minutes:.1f} minutes"
        else:
            hours = duration_minutes // 60
            mins = duration_minutes % 60
            duration_str = f"{int(hours)}h {int(mins)}m"
        
        journey = {
            "journey_id": f"JRN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "passenger_id": passenger_id,
            "passenger_name": session["passenger_name"],
            "passenger_type": session["passenger_type"],
            "entry_time": session["entry_time"],
            "entry_location": session["entry_location"]["address"],
            "entry_gps": session["entry_gps"],
            "entry_camera": session["entry_camera"],
            "exit_time": exit_time.isoformat(),
            "exit_location": location["address"],
            "exit_gps": {"lat": location["lat"], "lon": location["lon"]},
            "exit_camera": camera_id,
            "journey_duration_seconds": duration_seconds,
            "journey_duration": duration_str,
            "bus_id": bus_id,
            "status": "COMPLETED"
        }
        
        self.completed_journeys.append(journey)
        del self.active_sessions[passenger_id]
        self.vehicle_occupancy = max(0, self.vehicle_occupancy - 1)
        
        exit_record = {
            "event_id": f"EXIT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "event_type": "EXIT",
            "passenger_name": session["passenger_name"],
            "passenger_id": passenger_id,
            "camera_id": camera_id,
            "entry_location": session["entry_location"]["address"],
            "exit_location": location["address"],
            "journey_duration": duration_str,
            "timestamp": exit_time.isoformat(),
            "occupancy_after": self.vehicle_occupancy
        }
        self.exit_logs.append(exit_record)
        self.scan_history.append(exit_record)
        
        return journey
    
    def get_current_occupancy(self):
        return self.vehicle_occupancy
    
    def get_active_passengers(self):
        return list(self.active_sessions.values())
    
    def get_completed_journeys(self, limit=100):
        return self.completed_journeys[-limit:]
    
    def get_scan_history(self, limit=20):
        return self.scan_history[-limit:]

# ============ ALERT AGENT ============
class AlertAgent:
    def __init__(self):
        self.alerts = []
        
    def trigger_alert(self, alert_type: str, message: str, location: Dict, camera_id: str):
        alert = {
            "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": alert_type,
            "severity": "HIGH",
            "message": message,
            "location": location["address"],
            "gps": {"lat": location["lat"], "lon": location["lon"]},
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "status": "ACTIVE"
        }
        self.alerts.append(alert)
        return alert
    
    def get_active_alerts(self):
        return [a for a in self.alerts if a["status"] == "ACTIVE"]
    
    def resolve_alert(self, alert_id: str):
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "RESOLVED"
                return True
        return False

# ============ GPS LOCATIONS ============
GPS_LOCATIONS = {
    "camera_1": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station - Front Door"},
    "camera_2": {"lat": 28.6150, "lon": 77.2100, "address": "Central Station - Middle Door"},
    "camera_3": {"lat": 28.6160, "lon": 77.2110, "address": "Central Station - Back Door"},
    "camera_4": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall Entry"},
    "camera_5": {"lat": 28.6239, "lon": 77.2190, "address": "University Gate"},
}

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

def get_location_for_camera(camera_id: str):
    return GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1"])

# Initialize components
db = PassengerDatabase()
tracking_agent = TrackingAgent()
alert_agent = AlertAgent()

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "message": "Multi-Camera Vehicle Surveillance System",
        "registered_passengers": len(db.get_all_passengers()),
        "current_occupancy": tracking_agent.get_current_occupancy(),
        "completed_journeys": len(tracking_agent.get_completed_journeys()),
        "active_alerts": len(alert_agent.get_active_alerts()),
        "cameras": list(GPS_LOCATIONS.keys())
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/register_passenger")
async def register_passenger(
    name: str = Form(...),
    passenger_id: str = Form(...),
    passenger_type: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        
        face_path = f"D:/VehicleSurveillanceSystem/data/face_images/{passenger_id}.jpg"
        with open(face_path, "wb") as f:
            f.write(contents)
        
        db.register_passenger(passenger_id, name, passenger_type, image_hash, face_path)
        
        return {
            "status": "success",
            "message": f"✅ {name} (ID: {passenger_id}) registered successfully!",
            "passenger": {"name": name, "id": passenger_id, "type": passenger_type}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scan_entry")
async def scan_entry(
    file: UploadFile = File(...),
    camera_id: str = Form("camera_1"),
    bus_id: str = Form("BUS-001")
):
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        location = get_location_for_camera(camera_id)
        passenger = db.find_passenger_by_hash(image_hash)
        
        if passenger:
            if passenger["passenger_id"] in tracking_agent.active_sessions:
                return {
                    "status": "warning",
                    "event": "ALREADY_IN_VEHICLE",
                    "message": f"⚠️ {passenger['name']} is already in the vehicle!",
                    "passenger": passenger,
                    "current_occupancy": tracking_agent.get_current_occupancy()
                }
            
            session = tracking_agent.process_entry(passenger, location, camera_id, bus_id)
            
            return {
                "status": "success",
                "event": "ENTRY",
                "message": f"✅ {passenger['name']} ENTERED via {camera_id} at {location['address']}",
                "passenger": passenger,
                "entry_location": location["address"],
                "entry_gps": {"lat": location["lat"], "lon": location["lon"]},
                "entry_time": session["entry_time"],
                "camera_id": camera_id,
                "attendance": "PRESENT",
                "current_occupancy": tracking_agent.get_current_occupancy(),
                "total_entries": len(tracking_agent.entry_logs),
                "total_exits": len(tracking_agent.exit_logs)
            }
        else:
            alert = alert_agent.trigger_alert(
                "UNAUTHORIZED_ENTRY",
                f"🚨 ALERT: Unknown person detected at {location['address']}!",
                location,
                camera_id
            )
            
            return {
                "status": "warning",
                "event": "UNAUTHORIZED",
                "message": f"🚨 ALERT: Unknown person at {location['address']}!",
                "alert": alert,
                "location": location["address"],
                "gps": {"lat": location["lat"], "lon": location["lon"]},
                "camera_id": camera_id,
                "current_occupancy": tracking_agent.get_current_occupancy(),
                "total_entries": len(tracking_agent.entry_logs),
                "total_exits": len(tracking_agent.exit_logs)
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scan_exit")
async def scan_exit(
    file: UploadFile = File(...),
    camera_id: str = Form("camera_1"),
    bus_id: str = Form("BUS-001")
):
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        location = get_location_for_camera(camera_id)
        passenger = db.find_passenger_by_hash(image_hash)
        
        if passenger:
            if passenger["passenger_id"] not in tracking_agent.active_sessions:
                return {
                    "status": "warning",
                    "event": "NOT_IN_VEHICLE",
                    "message": f"⚠️ {passenger['name']} is not in the vehicle!",
                    "passenger": passenger,
                    "current_occupancy": tracking_agent.get_current_occupancy()
                }
            
            journey = tracking_agent.process_exit(passenger["passenger_id"], location, camera_id, bus_id)
            
            if journey:
                return {
                    "status": "success",
                    "event": "EXIT",
                    "message": f"✅ {passenger['name']} EXITED via {camera_id} at {location['address']}",
                    "passenger": passenger,
                    "entry_location": journey["entry_location"],
                    "entry_gps": journey["entry_gps"],
                    "exit_location": location["address"],
                    "exit_gps": {"lat": location["lat"], "lon": location["lon"]},
                    "journey_duration": journey["journey_duration"],
                    "camera_id": camera_id,
                    "current_occupancy": tracking_agent.get_current_occupancy(),
                    "total_entries": len(tracking_agent.entry_logs),
                    "total_exits": len(tracking_agent.exit_logs)
                }
        else:
            return {
                "status": "error",
                "event": "NOT_REGISTERED",
                "message": "Passenger not found in database",
                "current_occupancy": tracking_agent.get_current_occupancy()
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vehicle_status")
async def vehicle_status():
    return {
        "current_occupancy": tracking_agent.get_current_occupancy(),
        "active_passengers": tracking_agent.get_active_passengers(),
        "completed_journeys": len(tracking_agent.get_completed_journeys()),
        "active_alerts": len(alert_agent.get_active_alerts()),
        "total_registered": len(db.get_all_passengers()),
        "total_entries": len(tracking_agent.entry_logs),
        "total_exits": len(tracking_agent.exit_logs)
    }

@app.get("/active_passengers")
async def get_active_passengers():
    return {
        "count": len(tracking_agent.get_active_passengers()),
        "passengers": tracking_agent.get_active_passengers()
    }

@app.get("/completed_journeys")
async def get_completed_journeys():
    return {
        "count": len(tracking_agent.get_completed_journeys()),
        "journeys": tracking_agent.get_completed_journeys()
    }

@app.get("/scan_history")
async def get_scan_history():
    return {
        "history": tracking_agent.get_scan_history(),
        "count": len(tracking_agent.get_scan_history())
    }

@app.get("/active_alerts")
async def get_active_alerts():
    return {"alerts": alert_agent.get_active_alerts(), "count": len(alert_agent.get_active_alerts())}

@app.get("/registered_passengers")
async def get_registered_passengers():
    return {"passengers": db.get_all_passengers(), "count": len(db.get_all_passengers())}

@app.get("/cameras")
async def get_cameras():
    return {"cameras": list(GPS_LOCATIONS.keys()), "locations": GPS_LOCATIONS}

@app.delete("/clear_data")
async def clear_data():
    global tracking_agent, alert_agent
    tracking_agent.active_sessions = {}
    tracking_agent.completed_journeys = []
    tracking_agent.vehicle_occupancy = 0
    tracking_agent.entry_logs = []
    tracking_agent.exit_logs = []
    tracking_agent.scan_history = []
    alert_agent.alerts = []
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
