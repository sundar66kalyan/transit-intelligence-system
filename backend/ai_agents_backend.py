# backend/ai_agents_backend.py
from fastapi import FastAPI, File, UploadFile, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import os
import face_recognition
import numpy as np
from PIL import Image
import io
import pickle
import json
import asyncio
from typing import Dict, List

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🤖 AI AGENTS POWERED TRANSIT SYSTEM")
    print("=" * 70)
    os.makedirs("D:/transit-intelligence-system/data", exist_ok=True)
    load_face_database()
    print("✅ AI Agents Initialized")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield
    save_face_database()

app = FastAPI(title="AI Agents System", version="4.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections = []

@app.websocket("/ws/live_feed")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "connected", "timestamp": datetime.now().isoformat()})
    except:
        active_connections.remove(websocket)

# Database
registered_passengers = []
active_sessions = {}
completed_journeys = []
alerts = []
entry_exit_logs = []
unregistered_count = 0

# Face database
known_face_encodings = []
known_face_data = []

# GPS Locations
GPS_LOCATIONS = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def load_face_database():
    global known_face_encodings, known_face_data
    db_path = "D:/transit-intelligence-system/data/face_db.pkl"
    if os.path.exists(db_path):
        try:
            with open(db_path, "rb") as f:
                data = pickle.load(f)
            known_face_encodings = data.get("encodings", [])
            known_face_data = data.get("data", [])
            print(f"Loaded {len(known_face_encodings)} faces")
        except:
            print("No existing database")

def save_face_database():
    db_path = "D:/transit-intelligence-system/data/face_db.pkl"
    data = {"encodings": known_face_encodings, "data": known_face_data}
    with open(db_path, "wb") as f:
        pickle.dump(data, f)

def encode_face(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        encodings = face_recognition.face_encodings(image_np)
        if encodings:
            return encodings[0]
        return None
    except:
        return None

def match_face_in_db(image_bytes):
    uploaded_encoding = encode_face(image_bytes)
    if uploaded_encoding is None:
        return None, 0
    if len(known_face_encodings) == 0:
        return None, 0
    face_distances = face_recognition.face_distance(known_face_encodings, uploaded_encoding)
    best_match_index = np.argmin(face_distances)
    confidence = 1 - face_distances[best_match_index]
    if confidence >= 0.5:
        return known_face_data[best_match_index], confidence
    return None, confidence

# API Endpoints
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
        encoding = encode_face(contents)
        if encoding is None:
            return {"status": "error", "message": "No face detected"}
        
        known_face_encodings.append(encoding)
        passenger_data = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "gender": gender,
            "phone": phone,
            "email": email,
            "live_url": live_url,
            "registered_date": datetime.now().isoformat()
        }
        known_face_data.append(passenger_data)
        registered_passengers.append(passenger_data)
        save_face_database()
        
        return {"status": "success", "message": f"✅ {name} registered!", "passenger": passenger_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/auto_detect_face")
async def auto_detect_face(file: UploadFile = File(...), camera_id: str = Form("")):
    global unregistered_count
    try:
        contents = await file.read()
        matched_person, confidence = match_face_in_db(contents)
        location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
        current_time = datetime.now()
        
        if matched_person:
            # Registered person - Auto mark attendance
            pid = matched_person["passenger_id"]
            if pid not in active_sessions:
                session = {
                    "passenger_id": pid,
                    "passenger_name": matched_person["name"],
                    "passenger_type": matched_person["passenger_type"],
                    "gender": matched_person["gender"],
                    "entry_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "entry_date": current_time.strftime("%Y-%m-%d"),
                    "entry_time_only": current_time.strftime("%H:%M:%S"),
                    "entry_location": location["address"],
                    "entry_gps": f"{location['lat']}, {location['lon']}",
                    "entry_camera": camera_id,
                    "attendance": "PRESENT"
                }
                active_sessions[pid] = session
                
                entry_exit_logs.append({
                    "type": "AUTO_ENTRY",
                    "passenger_name": matched_person["name"],
                    "passenger_id": pid,
                    "location": location["address"],
                    "gps": f"{location['lat']}, {location['lon']}",
                    "time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "confidence": round(confidence * 100, 2)
                })
                
                return {
                    "status": "success",
                    "event": "REGISTERED_ENTRY",
                    "message": f"✅ {matched_person['name']} ENTERED - Attendance MARKED",
                    "passenger": matched_person,
                    "location": location["address"],
                    "gps": f"{location['lat']}, {location['lon']}",
                    "entry_time": session["entry_time"],
                    "confidence": round(confidence * 100, 2),
                    "current_occupancy": len(active_sessions)
                }
            else:
                return {
                    "status": "warning",
                    "event": "ALREADY_INSIDE",
                    "message": f"⚠️ {matched_person['name']} already inside",
                    "current_occupancy": len(active_sessions)
                }
        else:
            # Unregistered person - Trigger alert
            unregistered_count += 1
            alert = {
                "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "UNREGISTERED_PERSON",
                "severity": "HIGH",
                "message": f"🚨 UNREGISTERED person detected at {location['address']}!",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "camera": camera_id,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            alerts.append(alert)
            
            entry_exit_logs.append({
                "type": "UNREGISTERED_ENTRY",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "time": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            return {
                "status": "warning",
                "event": "UNREGISTERED_ENTRY",
                "message": f"🚨 UNREGISTERED person at {location['address']}! Alert triggered",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "unregistered_count": unregistered_count
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/record_exit")
async def record_exit(passenger_id: str = Form(...), passenger_name: str = Form(...), camera_id: str = Form(...)):
    location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
    exit_time = datetime.now()
    
    if passenger_id not in active_sessions:
        return {"status": "warning", "message": f"⚠️ {passenger_name} not inside"}
    
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
    
    return {
        "status": "success",
        "event": "EXIT",
        "message": f"✅ {passenger_name} EXITED",
        "duration": duration_str,
        "current_occupancy": len(active_sessions),
        "journey": journey
    }

@app.get("/vehicle_status")
async def vehicle_status():
    registered_inside = len(active_sessions)
    return {
        "current_occupancy": registered_inside,
        "unregistered_count": unregistered_count,
        "active_passengers": list(active_sessions.values()),
        "total_registered": len(registered_passengers),
        "completed_journeys_count": len(completed_journeys),
        "active_alerts": len(alerts),
        "total_unregistered_detected": unregistered_count
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
