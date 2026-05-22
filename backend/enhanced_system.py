# backend/enhanced_system.py
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
    print("🚌 Enhanced AI Vehicle Surveillance System")
    print("=" * 70)
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    print("✅ System Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Enhanced Vehicle System", version="9.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ DATABASE ============
registered_passengers = []
active_sessions = {}  # passenger_id -> session info
completed_journeys = []
alerts = []
entry_exit_logs = []

# GPS Locations
GPS_LOCATIONS = [
    {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
]

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

def get_random_location():
    return random.choice(GPS_LOCATIONS)

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "message": "Enhanced Vehicle Surveillance",
        "registered": len(registered_passengers),
        "active_occupancy": len(active_sessions),
        "completed_journeys": len(completed_journeys)
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
    """Register new passenger with face image"""
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
            "message": f"✅ {name} registered successfully!",
            "passenger": passenger
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/auto_scan")
async def auto_scan(
    file: UploadFile = File(...),
    action: str = Form("auto")
):
    """Auto scan face - automatically detects entry/exit"""
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        current_location = get_random_location()
        
        # Find matching passenger
        matched = None
        for p in registered_passengers:
            if p["image_hash"] == image_hash:
                matched = p
                break
        
        if matched:
            # Check if passenger is already in vehicle
            if matched["passenger_id"] in active_sessions:
                # EXIT - Calculate journey duration
                session = active_sessions[matched["passenger_id"]]
                entry_time = datetime.fromisoformat(session["entry_time"])
                exit_time = datetime.now()
                duration_seconds = (exit_time - entry_time).total_seconds()
                duration_minutes = duration_seconds / 60
                
                if duration_minutes < 60:
                    duration_str = f"{duration_minutes:.1f} minutes"
                else:
                    hours = duration_minutes // 60
                    mins = duration_minutes % 60
                    duration_str = f"{int(hours)}h {int(mins)}m"
                
                # Create completed journey record
                journey = {
                    "journey_id": f"JRN_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "passenger_id": matched["passenger_id"],
                    "passenger_name": matched["name"],
                    "passenger_type": matched["passenger_type"],
                    "entry_time": session["entry_time"],
                    "entry_location": session["entry_location"],
                    "entry_coordinates": session["entry_coordinates"],
                    "exit_time": exit_time.isoformat(),
                    "exit_location": current_location["address"],
                    "exit_coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                    "journey_duration_seconds": duration_seconds,
                    "journey_duration": duration_str,
                    "status": "COMPLETED"
                }
                completed_journeys.append(journey)
                
                # Remove from active sessions
                del active_sessions[matched["passenger_id"]]
                
                # Log exit
                entry_exit_logs.append({
                    "type": "EXIT",
                    "passenger": matched["name"],
                    "location": current_location["address"],
                    "coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                    "timestamp": exit_time.isoformat(),
                    "duration": duration_str
                })
                
                return {
                    "status": "success",
                    "event": "EXIT",
                    "message": f"✅ {matched['name']} EXITED at {current_location['address']}",
                    "passenger": matched,
                    "exit_location": current_location["address"],
                    "exit_coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                    "entry_location": session["entry_location"],
                    "entry_coordinates": session["entry_coordinates"],
                    "journey_duration": duration_str,
                    "current_occupancy": len(active_sessions)
                }
            else:
                # ENTRY - Mark attendance present
                session = {
                    "passenger_id": matched["passenger_id"],
                    "passenger_name": matched["name"],
                    "passenger_type": matched["passenger_type"],
                    "entry_time": datetime.now().isoformat(),
                    "entry_location": current_location["address"],
                    "entry_coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                    "attendance": "PRESENT"
                }
                active_sessions[matched["passenger_id"]] = session
                
                # Log entry
                entry_exit_logs.append({
                    "type": "ENTRY",
                    "passenger": matched["name"],
                    "location": current_location["address"],
                    "coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                    "timestamp": datetime.now().isoformat(),
                    "attendance": "PRESENT"
                })
                
                return {
                    "status": "success",
                    "event": "ENTRY",
                    "message": f"✅ {matched['name']} ENTERED at {current_location['address']} - Attendance MARKED PRESENT",
                    "passenger": matched,
                    "entry_location": current_location["address"],
                    "entry_coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                    "entry_time": session["entry_time"],
                    "attendance": "PRESENT",
                    "current_occupancy": len(active_sessions)
                }
        else:
            # UNKNOWN PERSON - Trigger alert
            alert = {
                "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "UNAUTHORIZED_PERSON",
                "severity": "HIGH",
                "message": f"🚨 ALERT: Unknown person detected at {current_location['address']}!",
                "location": current_location["address"],
                "coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                "timestamp": datetime.now().isoformat(),
                "status": "ACTIVE"
            }
            alerts.append(alert)
            
            entry_exit_logs.append({
                "type": "UNAUTHORIZED",
                "passenger": "UNKNOWN",
                "location": current_location["address"],
                "coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]},
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "status": "warning",
                "event": "UNAUTHORIZED",
                "message": f"🚨 ALERT: Unknown person at {current_location['address']}!",
                "alert": alert,
                "location": current_location["address"],
                "coordinates": {"lat": current_location["lat"], "lon": current_location["lon"]}
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vehicle_status")
async def vehicle_status():
    return {
        "current_occupancy": len(active_sessions),
        "active_passengers": list(active_sessions.values()),
        "completed_journeys_count": len(completed_journeys),
        "active_alerts": len([a for a in alerts if a.get("status") == "ACTIVE"]),
        "total_registered": len(registered_passengers)
    }

@app.get("/active_passengers")
async def get_active_passengers():
    return {
        "count": len(active_sessions),
        "passengers": list(active_sessions.values())
    }

@app.get("/completed_journeys")
async def get_completed_journeys():
    return {
        "count": len(completed_journeys),
        "journeys": completed_journeys[-50:]  # Last 50 journeys
    }

@app.get("/recent_logs")
async def get_recent_logs():
    return {
        "logs": entry_exit_logs[-30:],
        "count": len(entry_exit_logs)
    }

@app.get("/active_alerts")
async def get_active_alerts():
    active = [a for a in alerts if a.get("status") == "ACTIVE"]
    return {"alerts": active, "count": len(active)}

@app.get("/registered_passengers")
async def get_registered_passengers():
    return {"passengers": registered_passengers, "count": len(registered_passengers)}

@app.delete("/clear_data")
async def clear_data():
    global registered_passengers, active_sessions, completed_journeys, alerts, entry_exit_logs
    registered_passengers = []
    active_sessions = {}
    completed_journeys = []
    alerts = []
    entry_exit_logs = []
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
