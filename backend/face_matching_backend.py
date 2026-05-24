# backend/face_matching_backend.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys

sys.path.append("D:/transit-intelligence-system")
from utils.face_matcher import face_matcher

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("🚀 FACE MATCHING BACKEND")
    print("=" * 60)
    os.makedirs("D:/transit-intelligence-system/data", exist_ok=True)
    face_matcher.load_database()
    print("✅ Backend Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 60)
    yield
    print("Shutting down...")

app = FastAPI(title="Face Matching System", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registered_passengers = []
active_sessions = {}
completed_journeys = []
alerts = []
entry_exit_logs = []

GPS_LOCATIONS = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

@app.get("/health")
async def health():
    return {"status": "healthy"}

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
    try:
        contents = await file.read()
        success, msg = face_matcher.register_face(contents, name, passenger_id, gender, passenger_type)
        if not success:
            return {"status": "error", "message": msg}
        
        passenger = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "gender": gender,
            "phone": phone,
            "email": email,
            "live_url": live_url
        }
        registered_passengers.append(passenger)
        print(f"✅ Registered: {name}")
        return {"status": "success", "message": f"✅ {name} registered!", "passenger": passenger}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/match_face")
async def match_face_endpoint(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        result = face_matcher.match_face(contents)
        return result
    except Exception as e:
        return {"matched": False, "reason": str(e)}

@app.post("/record_entry")
async def record_entry(
    passenger_id: str = Form(...),
    passenger_name: str = Form(...),
    passenger_type: str = Form(...),
    gender: str = Form(""),
    camera_id: str = Form(...)
):
    location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
    current_time = datetime.now()
    
    if passenger_id in active_sessions:
        return {"status": "warning", "event": "ALREADY_INSIDE", "message": f"⚠️ {passenger_name} already inside"}
    
    session = {
        "passenger_id": passenger_id,
        "passenger_name": passenger_name,
        "passenger_type": passenger_type,
        "gender": gender,
        "entry_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "entry_date": current_time.strftime("%Y-%m-%d"),
        "entry_time_only": current_time.strftime("%H:%M:%S"),
        "entry_location": location["address"],
        "entry_gps": f"{location['lat']}, {location['lon']}"
    }
    active_sessions[passenger_id] = session
    
    entry_exit_logs.append({
        "type": "ENTRY",
        "passenger_name": passenger_name,
        "location": location["address"],
        "time": current_time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    print(f"✅ ENTRY: {passenger_name} - Active: {len(active_sessions)}")
    
    return {
        "status": "success",
        "event": "ENTRY",
        "message": f"✅ {passenger_name} ENTERED at {location['address']}",
        "entry_location": location["address"],
        "entry_gps": f"{location['lat']}, {location['lon']}",
        "entry_time": session["entry_time"],
        "current_occupancy": len(active_sessions)
    }

@app.post("/record_exit")
async def record_exit(
    passenger_id: str = Form(...),
    passenger_name: str = Form(...),
    camera_id: str = Form(...)
):
    location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
    exit_time = datetime.now()
    
    if passenger_id not in active_sessions:
        return {"status": "warning", "event": "NOT_INSIDE", "message": f"⚠️ {passenger_name} not inside"}
    
    session = active_sessions[passenger_id]
    entry_time = datetime.strptime(session["entry_time"], "%Y-%m-%d %H:%M:%S")
    duration_seconds = (exit_time - entry_time).total_seconds()
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    journey = {
        "passenger_name": passenger_name,
        "passenger_id": passenger_id,
        "gender": session.get("gender", "N/A"),
        "entry_time": session["entry_time"],
        "entry_location": session["entry_location"],
        "entry_gps": session["entry_gps"],
        "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
        "exit_location": location["address"],
        "exit_gps": f"{location['lat']}, {location['lon']}",
        "duration": duration_str
    }
    completed_journeys.append(journey)
    del active_sessions[passenger_id]
    
    print(f"✅ EXIT: {passenger_name} - Duration: {duration_str}")
    
    return {
        "status": "success",
        "event": "EXIT",
        "message": f"✅ {passenger_name} EXITED",
        "duration": duration_str,
        "current_occupancy": len(active_sessions),
        "journey": journey
    }

@app.post("/record_unknown")
async def record_unknown(camera_id: str = Form(...)):
    location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
    current_time = datetime.now()
    
    alert = {
        "type": "UNKNOWN_PERSON",
        "severity": "HIGH",
        "message": f"🚨 Unknown person detected at {location['address']}!",
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "camera": camera_id,
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    alerts.append(alert)
    
    entry_exit_logs.append({
        "type": "UNKNOWN_ENTRY",
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "time": current_time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    return {
        "status": "warning",
        "message": f"🚨 Unknown person at {location['address']}!",
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/vehicle_status")
async def vehicle_status():
    return {
        "current_occupancy": len(active_sessions),
        "active_passengers": list(active_sessions.values()),
        "total_registered": len(registered_passengers),
        "completed_journeys_count": len(completed_journeys),
        "active_alerts": len(alerts)
    }

@app.get("/registered_passengers")
async def get_registered():
    return {"passengers": registered_passengers, "count": len(registered_passengers)}

@app.get("/completed_journeys")
async def get_journeys():
    return {"journeys": completed_journeys, "count": len(completed_journeys)}

@app.get("/active_alerts")
async def get_alerts():
    return {"alerts": alerts, "count": len(alerts)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
