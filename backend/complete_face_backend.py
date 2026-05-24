from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys
import face_recognition
import numpy as np
from PIL import Image
import io
import pickle

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("🚀 COMPLETE FACE MATCHING SYSTEM")
    print("=" * 60)
    os.makedirs("D:/transit-intelligence-system/data", exist_ok=True)
    load_face_database()
    print("✅ Backend Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 60)
    yield
    save_face_database()

app = FastAPI(title="Complete Face System", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage
registered_passengers = []
active_sessions = {}
completed_journeys = []
alerts = []
entry_exit_logs = []

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
    print(f"Saved {len(known_face_encodings)} faces")

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
        
        # Encode face
        encoding = encode_face(contents)
        if encoding is None:
            return {"status": "error", "message": "No face detected in image"}
        
        # Store face data
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
        
        # Store in registered passengers list
        registered_passengers.append(passenger_data)
        save_face_database()
        
        print(f"✅ Registered: {name} ({passenger_id})")
        
        return {
            "status": "success",
            "message": f"✅ {name} registered successfully!",
            "passenger": passenger_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/match_face")
async def match_face(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        matched_person, confidence = match_face_in_db(contents)
        
        if matched_person:
            return {
                "matched": True,
                "name": matched_person["name"],
                "passenger_id": matched_person["passenger_id"],
                "passenger_type": matched_person["passenger_type"],
                "gender": matched_person["gender"],
                "confidence": round(confidence * 100, 2)
            }
        else:
            return {
                "matched": False,
                "reason": "Face not recognized - Unknown person",
                "confidence": round(confidence * 100, 2) if confidence else 0
            }
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
        "entry_gps": f"{location['lat']}, {location['lon']}",
        "entry_camera": camera_id
    }
    active_sessions[passenger_id] = session
    
    entry_exit_logs.append({
        "type": "ENTRY",
        "passenger_name": passenger_name,
        "passenger_id": passenger_id,
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "time": current_time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    return {
        "status": "success",
        "event": "ENTRY",
        "message": f"✅ {passenger_name} ENTERED at {location['address']}",
        "entry_location": location["address"],
        "entry_gps": f"{location['lat']}, {location['lon']}",
        "entry_time": session["entry_time"],
        "current_occupancy": len(active_sessions)
    }

@app.post("/record_unknown_entry")
async def record_unknown_entry(
    camera_id: str = Form(...),
    image_data: str = Form("")
):
    location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
    current_time = datetime.now()
    
    alert = {
        "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": "UNKNOWN_PERSON_ENTRY",
        "severity": "HIGH",
        "message": f"🚨 UNKNOWN PERSON detected at {location['address']}!",
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "camera": camera_id,
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S")
    }
    alerts.append(alert)
    
    entry_exit_logs.append({
        "type": "UNKNOWN_ENTRY",
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "camera": camera_id,
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    return {
        "status": "warning",
        "event": "UNKNOWN_ENTRY",
        "message": f"🚨 UNKNOWN PERSON at {location['address']}!",
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "alert": alert
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
    
    entry_exit_logs.append({
        "type": "EXIT",
        "passenger_name": passenger_name,
        "passenger_id": passenger_id,
        "location": location["address"],
        "gps": f"{location['lat']}, {location['lon']}",
        "time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration_str
    })
    
    return {
        "status": "success",
        "event": "EXIT",
        "message": f"✅ {passenger_name} EXITED at {location['address']}",
        "duration": duration_str,
        "current_occupancy": len(active_sessions),
        "journey": journey
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

@app.get("/entry_logs")
async def get_logs():
    return {"logs": entry_exit_logs, "count": len(entry_exit_logs)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
