# backend/complete_system.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import os
import hashlib
import random
import json
from typing import Dict, List, Optional

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🚌 AI-Powered Vehicle Surveillance System with Agents")
    print("=" * 70)
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    print("✅ System Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Vehicle Surveillance System", version="7.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ AI AGENTS ============

class PassengerTrackingAgent:
    """AI Agent for tracking passengers, occupancy, and journey duration"""
    
    def __init__(self):
        self.active_passengers: Dict[str, Dict] = {}  # passenger_id -> active journey
        self.completed_journeys: List[Dict] = []  # History of completed journeys
        self.vehicle_occupancy = 0
        self.entry_exit_logs: List[Dict] = []
        
    def record_entry(self, passenger: Dict, location: Dict, bus_id: str) -> Dict:
        """Record passenger entry with GPS and start journey timer"""
        passenger_id = passenger["passenger_id"]
        current_time = datetime.now()
        
        # Create journey record
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
        
        # Log entry
        log = {
            "event_id": f"ENTRY_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "event_type": "ENTRY",
            "passenger_name": passenger["name"],
            "passenger_id": passenger_id,
            "location": location["address"],
            "gps": {"lat": location["lat"], "lon": location["lon"]},
            "timestamp": current_time.isoformat(),
            "occupancy_after": self.vehicle_occupancy
        }
        self.entry_exit_logs.append(log)
        
        return journey
    
    def record_exit(self, passenger_id: str, location: Dict, bus_id: str) -> Optional[Dict]:
        """Record passenger exit, calculate journey duration"""
        if passenger_id not in self.active_passengers:
            return None
        
        journey = self.active_passengers[passenger_id]
        exit_time = datetime.now()
        entry_time = datetime.fromisoformat(journey["entry_time"])
        
        # Calculate journey duration
        duration_seconds = (exit_time - entry_time).total_seconds()
        duration_minutes = duration_seconds / 60
        
        # Format duration
        if duration_minutes < 60:
            duration_str = f"{duration_minutes:.1f} minutes"
        else:
            hours = duration_minutes // 60
            mins = duration_minutes % 60
            duration_str = f"{int(hours)}h {int(mins)}m"
        
        # Complete journey record
        completed_journey = {
            **journey,
            "exit_time": exit_time.isoformat(),
            "exit_location": location,
            "exit_gps": {"lat": location["lat"], "lon": location["lon"]},
            "journey_duration_seconds": duration_seconds,
            "journey_duration": duration_str,
            "status": "COMPLETED"
        }
        
        self.completed_journeys.append(completed_journey)
        del self.active_passengers[passenger_id]
        self.vehicle_occupancy = max(0, self.vehicle_occupancy - 1)
        
        # Log exit
        log = {
            "event_id": f"EXIT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
            "event_type": "EXIT",
            "passenger_name": journey["passenger_name"],
            "passenger_id": passenger_id,
            "entry_location": journey["entry_location"]["address"],
            "exit_location": location["address"],
            "journey_duration": duration_str,
            "timestamp": exit_time.isoformat(),
            "occupancy_after": self.vehicle_occupancy
        }
        self.entry_exit_logs.append(log)
        
        return completed_journey
    
    def get_current_occupancy(self) -> int:
        return self.vehicle_occupancy
    
    def get_active_passengers(self) -> List[Dict]:
        return list(self.active_passengers.values())
    
    def get_completed_journeys(self, limit=50) -> List[Dict]:
        return self.completed_journeys[-limit:]
    
    def get_recent_logs(self, limit=50) -> List[Dict]:
        return self.entry_exit_logs[-limit:]

class AlertAgent:
    """AI Agent for security alerts"""
    
    def __init__(self):
        self.alerts = []
        
    def generate_unauthorized_alert(self, location: Dict) -> Dict:
        alert = {
            "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "UNAUTHORIZED_ENTRY",
            "severity": "HIGH",
            "message": f"🚨 ALERT: Unregistered person detected at {location['address']}!",
            "location": location["address"],
            "gps": {"lat": location["lat"], "lon": location["lon"]},
            "timestamp": datetime.now().isoformat(),
            "status": "ACTIVE"
        }
        self.alerts.append(alert)
        return alert
    
    def get_active_alerts(self) -> List[Dict]:
        return [a for a in self.alerts if a.get("status") == "ACTIVE"]
    
    def resolve_alert(self, alert_id: str):
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "RESOLVED"
                return True
        return False

# Initialize Agents
tracking_agent = PassengerTrackingAgent()
alert_agent = AlertAgent()

# Database for registered passengers
registered_passengers = []

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

def match_face(uploaded_hash):
    """Match uploaded face with registered database"""
    for passenger in registered_passengers:
        if passenger["image_hash"] == uploaded_hash:
            return passenger
    return None

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "message": "AI Vehicle Surveillance System",
        "status": "running",
        "registered_passengers": len(registered_passengers),
        "current_occupancy": tracking_agent.get_current_occupancy(),
        "timestamp": datetime.now().isoformat()
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
    """Register a new passenger with face image"""
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        
        # Save image
        face_path = f"D:/VehicleSurveillanceSystem/data/face_images/{passenger_id}.jpg"
        with open(face_path, "wb") as f:
            f.write(contents)
        
        passenger = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "image_hash": image_hash,
            "face_image_path": face_path,
            "registered_date": datetime.now().isoformat()
        }
        registered_passengers.append(passenger)
        
        return {
            "status": "success",
            "message": f"✅ Passenger {name} (ID: {passenger_id}) registered successfully!",
            "passenger": passenger
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scan_entry")
async def scan_entry(
    file: UploadFile = File(...),
    bus_id: str = Form("BUS-001")
):
    """Scan face for entry - records GPS, marks attendance, updates occupancy"""
    try:
        contents = await file.read()
        uploaded_hash = get_image_hash(contents)
        
        # Simulated GPS locations
        locations = [
            {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
            {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
            {"lat": 28.6239, "lon": 77.2190, "address": "University"},
            {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
            {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
        ]
        current_location = random.choice(locations)
        
        # Match face with database
        matched_passenger = match_face(uploaded_hash)
        
        if matched_passenger:
            # REGISTERED - Record entry and start journey
            journey = tracking_agent.record_entry(matched_passenger, current_location, bus_id)
            
            return {
                "status": "success",
                "result": "registered",
                "message": f"✅ WELCOME {matched_passenger['name']}! Entry recorded.",
                "passenger": matched_passenger,
                "location": current_location,
                "gps": {"lat": current_location["lat"], "lon": current_location["lon"]},
                "entry_time": journey["entry_time"],
                "current_occupancy": tracking_agent.get_current_occupancy(),
                "attendance": "PRESENT"
            }
        else:
            # UNREGISTERED - Generate alert
            alert = alert_agent.generate_unauthorized_alert(current_location)
            
            return {
                "status": "success",
                "result": "unauthorized",
                "message": f"🚨 ALERT: Unknown person detected at {current_location['address']}!",
                "alert": alert,
                "location": current_location,
                "gps": {"lat": current_location["lat"], "lon": current_location["lon"]},
                "current_occupancy": tracking_agent.get_current_occupancy()
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scan_exit")
async def scan_exit(
    file: UploadFile = File(...),
    bus_id: str = Form("BUS-001")
):
    """Scan face for exit - records exit, calculates journey duration"""
    try:
        contents = await file.read()
        uploaded_hash = get_image_hash(contents)
        
        locations = [
            {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
            {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
            {"lat": 28.6239, "lon": 77.2190, "address": "University"},
            {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"}
        ]
        current_location = random.choice(locations)
        
        matched_passenger = match_face(uploaded_hash)
        
        if matched_passenger:
            # Record exit and calculate journey duration
            completed_journey = tracking_agent.record_exit(
                matched_passenger["passenger_id"], current_location, bus_id
            )
            
            if completed_journey:
                return {
                    "status": "success",
                    "result": "exited",
                    "message": f"✅ GOODBYE {matched_passenger['name']}! Exit recorded.",
                    "passenger": matched_passenger,
                    "entry_location": completed_journey["entry_location"]["address"],
                    "entry_gps": completed_journey["entry_gps"],
                    "exit_location": current_location["address"],
                    "exit_gps": {"lat": current_location["lat"], "lon": current_location["lon"]},
                    "journey_duration": completed_journey["journey_duration"],
                    "current_occupancy": tracking_agent.get_current_occupancy()
                }
            else:
                return {
                    "status": "error",
                    "result": "not_in_vehicle",
                    "message": f"⚠️ {matched_passenger['name']} is not in the vehicle",
                    "current_occupancy": tracking_agent.get_current_occupancy()
                }
        else:
            return {
                "status": "error",
                "result": "not_found",
                "message": "Passenger not found in database",
                "current_occupancy": tracking_agent.get_current_occupancy()
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vehicle_status")
async def vehicle_status():
    """Get complete vehicle status from AI Agent"""
    return {
        "current_occupancy": tracking_agent.get_current_occupancy(),
        "active_passengers": tracking_agent.get_active_passengers(),
        "completed_journeys_today": len(tracking_agent.get_completed_journeys()),
        "total_entries_logged": len(tracking_agent.get_recent_logs()),
        "active_alerts": len(alert_agent.get_active_alerts()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/active_passengers")
async def get_active_passengers():
    """Get passengers currently in vehicle"""
    return {
        "count": len(tracking_agent.get_active_passengers()),
        "passengers": tracking_agent.get_active_passengers()
    }

@app.get("/journey_history")
async def get_journey_history(limit: int = 50):
    """Get completed journey history with durations"""
    return {
        "count": len(tracking_agent.get_completed_journeys(limit)),
        "journeys": tracking_agent.get_completed_journeys(limit)
    }

@app.get("/recent_logs")
async def get_recent_logs():
    """Get recent entry/exit logs"""
    return {"logs": tracking_agent.get_recent_logs(), "count": len(tracking_agent.get_recent_logs())}

@app.get("/active_alerts")
async def get_active_alerts():
    """Get active security alerts"""
    return {"alerts": alert_agent.get_active_alerts(), "count": len(alert_agent.get_active_alerts())}

@app.get("/registered_passengers")
async def get_registered_passengers():
    """Get all registered passengers"""
    return {"passengers": registered_passengers, "count": len(registered_passengers)}

@app.delete("/clear_data")
async def clear_data():
    """Clear all data (for testing)"""
    global registered_passengers
    registered_passengers = []
    tracking_agent.active_passengers = {}
    tracking_agent.completed_journeys = []
    tracking_agent.vehicle_occupancy = 0
    tracking_agent.entry_exit_logs = []
    alert_agent.alerts = []
    return {"status": "success", "message": "All data cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
