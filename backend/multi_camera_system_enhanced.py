# backend/multi_camera_system_enhanced.py
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
    print("🚀 ENHANCED TRANSIT INTELLIGENCE SYSTEM")
    print("=" * 70)
    os.makedirs("D:/transit-intelligence-system/data/face_images", exist_ok=True)
    os.makedirs("D:/transit-intelligence-system/uploads", exist_ok=True)
    print("✅ System Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Enhanced Transit System", version="10.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database - Global variables
registered_passengers = []
active_sessions = {}  # passenger_id -> session info
completed_journeys_list = []
alerts = []
entry_exit_logs = []
unknown_person_count = 0
total_male_count = 0
total_female_count = 0

# GPS Locations
GPS_LOCATIONS = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

@app.get("/")
async def root():
    return {
        "message": "Enhanced Transit Intelligence System",
        "registered": len(registered_passengers),
        "active_occupancy": len(active_sessions),
        "completed_journeys": len(completed_journeys_list),
        "unknown_count": unknown_person_count
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/register_passenger")
async def register_passenger(
    name: str = Form(...),
    passenger_id: str = Form(...),
    passenger_type: str = Form(...),
    gender: str = Form(...),
    phone: str = Form(""),
    email: str = Form(""),
    live_url: str = Form(""),
    file: UploadFile = File(...)
):
    global total_male_count, total_female_count
    
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        
        face_path = f"D:/transit-intelligence-system/data/face_images/{passenger_id}.jpg"
        with open(face_path, "wb") as f:
            f.write(contents)
        
        passenger = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "gender": gender,
            "phone": phone,
            "email": email,
            "live_url": live_url,
            "image_hash": image_hash,
            "face_image_path": face_path,
            "registered_date": datetime.now().isoformat()
        }
        registered_passengers.append(passenger)
        
        # Update gender count
        if gender == "Male":
            total_male_count += 1
        elif gender == "Female":
            total_female_count += 1
        
        print(f"✅ Registered: {name} ({passenger_id}) - Total registered: {len(registered_passengers)}")
        
        return {
            "status": "success",
            "message": f"✅ {name} registered successfully!",
            "passenger": passenger
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/record_entry")
async def record_entry(
    passenger_id: str = Form(...),
    passenger_name: str = Form(...),
    passenger_type: str = Form(...),
    gender: str = Form(""),
    camera_id: str = Form(...),
    is_unknown: bool = Form(False)
):
    global unknown_person_count
    
    current_location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1"])
    current_time = datetime.now()
    
    if is_unknown:
        unknown_person_count += 1
        alert = {
            "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "UNKNOWN_PERSON_ENTRY",
            "severity": "HIGH",
            "message": f"🚨 Unknown person detected at {current_location['address']}!",
            "location": current_location["address"],
            "gps": {"lat": current_location["lat"], "lon": current_location["lon"]},
            "camera": camera_id,
            "timestamp": current_time.isoformat()
        }
        alerts.append(alert)
        
        entry_exit_logs.append({
            "type": "UNKNOWN_ENTRY",
            "passenger_name": "UNKNOWN PERSON",
            "location": current_location["address"],
            "gps": f"{current_location['lat']}, {current_location['lon']}",
            "camera": camera_id,
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "date": current_time.strftime("%Y-%m-%d"),
            "time": current_time.strftime("%H:%M:%S")
        })
        
        return {
            "status": "warning",
            "event": "UNKNOWN_ENTRY",
            "message": f"🚨 Unknown person at {current_location['address']}!",
            "current_occupancy": len(active_sessions),
            "unknown_count": unknown_person_count
        }
    
    # Check if already inside
    if passenger_id in active_sessions:
        return {
            "status": "warning",
            "event": "ALREADY_INSIDE",
            "message": f"⚠️ {passenger_name} is already inside the vehicle!",
            "current_occupancy": len(active_sessions)
        }
    
    # Registered person entry
    session = {
        "passenger_id": passenger_id,
        "passenger_name": passenger_name,
        "passenger_type": passenger_type,
        "gender": gender,
        "entry_time_full": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "entry_date": current_time.strftime("%Y-%m-%d"),
        "entry_time": current_time.strftime("%H:%M:%S"),
        "entry_location": current_location["address"],
        "entry_gps": f"{current_location['lat']}, {current_location['lon']}",
        "entry_camera": camera_id,
        "status": "IN_VEHICLE"
    }
    active_sessions[passenger_id] = session
    
    entry_exit_logs.append({
        "type": "ENTRY",
        "passenger_id": passenger_id,
        "passenger_name": passenger_name,
        "gender": gender,
        "location": current_location["address"],
        "gps": f"{current_location['lat']}, {current_location['lon']}",
        "camera": camera_id,
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S")
    })
    
    print(f"✅ ENTRY: {passenger_name} at {current_location['address']} - Active: {len(active_sessions)}")
    
    return {
        "status": "success",
        "event": "ENTRY",
        "message": f"✅ {passenger_name} ENTERED at {current_location['address']}",
        "entry_time": session["entry_time_full"],
        "entry_date": session["entry_date"],
        "entry_time_only": session["entry_time"],
        "entry_location": session["entry_location"],
        "entry_gps": session["entry_gps"],
        "current_occupancy": len(active_sessions)
    }

@app.post("/record_exit")
async def record_exit(
    passenger_id: str = Form(...),
    passenger_name: str = Form(...),
    camera_id: str = Form(...)
):
    current_location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1"])
    exit_time = datetime.now()
    
    if passenger_id not in active_sessions:
        return {
            "status": "warning",
            "event": "NOT_INSIDE",
            "message": f"⚠️ {passenger_name} is not inside the vehicle!",
            "current_occupancy": len(active_sessions)
        }
    
    session = active_sessions[passenger_id]
    entry_time = datetime.strptime(session["entry_time_full"], "%Y-%m-%d %H:%M:%S")
    
    # Calculate duration
    duration_seconds = (exit_time - entry_time).total_seconds()
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    # Create completed journey
    journey = {
        "journey_id": f"JRN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{passenger_id}",
        "passenger_id": passenger_id,
        "passenger_name": passenger_name,
        "passenger_type": session["passenger_type"],
        "gender": session.get("gender", "Not specified"),
        "entry_date": session["entry_date"],
        "entry_time": session["entry_time"],
        "entry_location": session["entry_location"],
        "entry_gps": session["entry_gps"],
        "exit_date": exit_time.strftime("%Y-%m-%d"),
        "exit_time": exit_time.strftime("%H:%M:%S"),
        "exit_location": current_location["address"],
        "exit_gps": f"{current_location['lat']}, {current_location['lon']}",
        "duration": duration_str,
        "duration_seconds": duration_seconds,
        "status": "COMPLETED"
    }
    completed_journeys_list.append(journey)
    del active_sessions[passenger_id]
    
    entry_exit_logs.append({
        "type": "EXIT",
        "passenger_id": passenger_id,
        "passenger_name": passenger_name,
        "location": current_location["address"],
        "gps": f"{current_location['lat']}, {current_location['lon']}",
        "camera": camera_id,
        "timestamp": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
        "date": exit_time.strftime("%Y-%m-%d"),
        "time": exit_time.strftime("%H:%M:%S"),
        "duration": duration_str
    })
    
    print(f"✅ EXIT: {passenger_name} at {current_location['address']} - Duration: {duration_str} - Active: {len(active_sessions)}")
    
    return {
        "status": "success",
        "event": "EXIT",
        "message": f"✅ {passenger_name} EXITED at {current_location['address']}",
        "journey": journey,
        "duration": duration_str,
        "current_occupancy": len(active_sessions)
    }

@app.get("/vehicle_status")
async def vehicle_status():
    # Calculate gender counts
    active_males = sum(1 for s in active_sessions.values() if s.get("gender") == "Male")
    active_females = sum(1 for s in active_sessions.values() if s.get("gender") == "Female")
    active_unknown_gender = len(active_sessions) - active_males - active_females
    
    return {
        "current_occupancy": len(active_sessions),
        "male_count": active_males,
        "female_count": active_females,
        "unknown_person_count": active_unknown_gender,
        "total_unknown_detected": unknown_person_count,
        "total_male_registered": total_male_count,
        "total_female_registered": total_female_count,
        "active_passengers": list(active_sessions.values()),
        "completed_journeys_count": len(completed_journeys_list),
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
        "count": len(completed_journeys_list),
        "journeys": completed_journeys_list[-50:]
    }

@app.get("/entry_exit_logs")
async def get_entry_exit_logs():
    return {
        "logs": entry_exit_logs[-100:],
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
    global registered_passengers, active_sessions, completed_journeys_list, alerts, entry_exit_logs, unknown_person_count
    registered_passengers = []
    active_sessions = {}
    completed_journeys_list = []
    alerts = []
    entry_exit_logs = []
    unknown_person_count = 0
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
