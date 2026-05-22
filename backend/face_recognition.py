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

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("🚌 Face Recognition Entry System")
    print("=" * 60)
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    load_demo_passengers()
    print("✅ System Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 60)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Face Recognition System", version="6.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
registered_passengers = []
entry_logs = []
alerts = []
current_occupancy = 0
active_passengers = {}  # passenger_id -> {entry_time, entry_location}

def load_demo_passengers():
    """Load demo passengers from demo_faces folder"""
    demo_faces_dir = "D:/VehicleSurveillanceSystem/demo_faces"
    if os.path.exists(demo_faces_dir):
        for file in os.listdir(demo_faces_dir):
            if file.endswith(".jpg"):
                passenger_id = file.replace(".jpg", "")
                with open(os.path.join(demo_faces_dir, file), "rb") as f:
                    img_hash = hashlib.md5(f.read()).hexdigest()
                
                # Demo passenger data
                demo_names = {
                    "P001": {"name": "John Doe", "type": "Regular"},
                    "P002": {"name": "Jane Smith", "type": "VIP"},
                    "P003": {"name": "Robert Johnson", "type": "Staff"},
                    "P004": {"name": "Alice Brown", "type": "Student"},
                }
                
                if passenger_id in demo_names:
                    registered_passengers.append({
                        "passenger_id": passenger_id,
                        "name": demo_names[passenger_id]["name"],
                        "passenger_type": demo_names[passenger_id]["type"],
                        "is_blacklisted": False,
                        "image_hash": img_hash,
                        "registered_date": datetime.now().isoformat()
                    })
        print(f"✅ Loaded {len(registered_passengers)} demo passengers")

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

def match_face(uploaded_hash):
    """Match uploaded face with registered database"""
    for passenger in registered_passengers:
        if passenger["image_hash"] == uploaded_hash:
            return passenger
    return None

@app.get("/")
async def root():
    return {
        "message": "Face Recognition Entry System",
        "status": "running",
        "registered_passengers": len(registered_passengers),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/register_face")
async def register_face(
    name: str = Form(...),
    passenger_id: str = Form(...),
    passenger_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Register new passenger face"""
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
            "is_blacklisted": False,
            "image_hash": image_hash,
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

@app.post("/scan_entry")
async def scan_entry(
    file: UploadFile = File(...),
    bus_id: str = Form("BUS-001")
):
    """Scan face for entry - records GPS and marks attendance"""
    global current_occupancy
    
    try:
        contents = await file.read()
        uploaded_hash = get_image_hash(contents)
        
        # GPS locations for demo
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
            # REGISTERED PERSON - Mark attendance
            current_occupancy += 1
            
            # Store active passenger
            active_passengers[matched_passenger["passenger_id"]] = {
                "passenger": matched_passenger,
                "entry_time": datetime.now().isoformat(),
                "entry_location": current_location,
                "bus_id": bus_id
            }
            
            # Log entry
            entry_log = {
                "event_id": f"ENTRY_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "ENTRY",
                "passenger": matched_passenger,
                "location": current_location,
                "timestamp": datetime.now().isoformat(),
                "occupancy": current_occupancy,
                "attendance_marked": True
            }
            entry_logs.append(entry_log)
            
            # Check if blacklisted
            if matched_passenger.get("is_blacklisted"):
                alert = {
                    "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "type": "BLACKLISTED",
                    "message": f"🚨 BLACKLISTED: {matched_passenger['name']} entering!",
                    "location": current_location,
                    "timestamp": datetime.now().isoformat()
                }
                alerts.append(alert)
            
            return {
                "status": "success",
                "result": "registered",
                "message": f"✅ WELCOME {matched_passenger['name']}! Attendance marked.",
                "passenger": matched_passenger,
                "location": current_location,
                "gps": {"lat": current_location["lat"], "lon": current_location["lon"]},
                "current_occupancy": current_occupancy,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # UNREGISTERED PERSON - Trigger alert
            alert = {
                "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "UNAUTHORIZED_ENTRY",
                "severity": "HIGH",
                "message": f"🚨 ALERT: Unauthorized person at {current_location['address']}!",
                "location": current_location,
                "timestamp": datetime.now().isoformat()
            }
            alerts.append(alert)
            
            # Log unauthorized entry
            entry_logs.append({
                "event_id": f"UNAUTH_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "UNAUTHORIZED",
                "location": current_location,
                "timestamp": datetime.now().isoformat(),
                "alert_generated": True
            })
            
            return {
                "status": "success",
                "result": "unauthorized",
                "message": f"🚨 ALERT: Unknown person detected! Security notified.",
                "alert": alert,
                "location": current_location,
                "gps": {"lat": current_location["lat"], "lon": current_location["lon"]},
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scan_exit")
async def scan_exit(
    file: UploadFile = File(...),
    bus_id: str = Form("BUS-001")
):
    """Scan face for exit - records exit GPS"""
    global current_occupancy
    
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
        
        if matched_passenger and matched_passenger["passenger_id"] in active_passengers:
            current_occupancy = max(0, current_occupancy - 1)
            
            active_info = active_passengers.pop(matched_passenger["passenger_id"])
            entry_time = datetime.fromisoformat(active_info["entry_time"])
            exit_time = datetime.now()
            journey_duration = str(exit_time - entry_time)
            
            exit_log = {
                "event_id": f"EXIT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "EXIT",
                "passenger": matched_passenger,
                "entry_location": active_info["entry_location"],
                "exit_location": current_location,
                "journey_duration": journey_duration,
                "timestamp": datetime.now().isoformat(),
                "occupancy": current_occupancy
            }
            entry_logs.append(exit_log)
            
            return {
                "status": "success",
                "result": "exited",
                "message": f"✅ GOODBYE {matched_passenger['name']}! Exit recorded.",
                "passenger": matched_passenger,
                "entry_location": active_info["entry_location"],
                "exit_location": current_location,
                "journey_duration": journey_duration,
                "gps": {"lat": current_location["lat"], "lon": current_location["lon"]},
                "current_occupancy": current_occupancy
            }
        else:
            return {
                "status": "error",
                "result": "not_found",
                "message": "Passenger not found or not in vehicle",
                "current_occupancy": current_occupancy
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vehicle_status")
async def vehicle_status():
    """Get current vehicle status"""
    return {
        "current_occupancy": current_occupancy,
        "active_passengers": list(active_passengers.values()),
        "total_entries_today": len(entry_logs),
        "active_alerts": len(alerts),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/recent_entries")
async def recent_entries():
    return {"entries": entry_logs[-30:], "count": len(entry_logs)}

@app.get("/active_alerts")
async def active_alerts():
    return {"alerts": alerts[-20:], "count": len(alerts)}

@app.get("/passengers")
async def get_passengers():
    return {"passengers": registered_passengers}

@app.get("/demo_faces")
async def get_demo_faces():
    """Get list of demo faces for testing"""
    demo_faces_dir = "D:/VehicleSurveillanceSystem/demo_faces"
    demo_faces = []
    if os.path.exists(demo_faces_dir):
        for file in os.listdir(demo_faces_dir):
            if file.endswith(".jpg"):
                passenger_id = file.replace(".jpg", "")
                for p in registered_passengers:
                    if p["passenger_id"] == passenger_id:
                        demo_faces.append({
                            "passenger_id": passenger_id,
                            "name": p["name"],
                            "type": p["passenger_type"],
                            "image_path": os.path.join(demo_faces_dir, file)
                        })
                        break
    return {"demo_faces": demo_faces}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
