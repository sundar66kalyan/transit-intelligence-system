# backend/complete_backend.py
from fastapi import FastAPI, File, UploadFile, Form
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🚀 AI-POWERED TRANSIT INTELLIGENCE SYSTEM")
    print("👨‍💻 Created by: Kalyanasundar - AI Engineer")
    print("=" * 70)
    os.makedirs("D:/transit-intelligence-system/data", exist_ok=True)
    load_face_database()
    print("✅ System Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield
    save_face_database()

app = FastAPI(title="AI Transit System", version="3.0.0", lifespan=lifespan)

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
    global known_face_encodings, known_face_data, registered_passengers
    db_path = "D:/transit-intelligence-system/data/face_db.pkl"
    if os.path.exists(db_path):
        try:
            with open(db_path, "rb") as f:
                data = pickle.load(f)
            known_face_encodings = data.get("encodings", [])
            known_face_data = data.get("data", [])
            registered_passengers = known_face_data
            print(f"✅ Loaded {len(known_face_encodings)} faces")
        except:
            print("No existing database")
    else:
        print("No database found. Starting fresh.")

def save_face_database():
    db_path = "D:/transit-intelligence-system/data/face_db.pkl"
    data = {"encodings": known_face_encodings, "data": known_face_data}
    with open(db_path, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ Saved {len(known_face_encodings)} faces")

def encode_face(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        image_np = np.array(image)
        encodings = face_recognition.face_encodings(image_np)
        if encodings:
            return encodings[0]
        return None
    except Exception as e:
        print(f"Encode error: {e}")
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

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "message": "AI Transit Intelligence System",
        "creator": "KalyanaSundar - AI Engineer",
        "registered": len(registered_passengers),
        "active": len(active_sessions),
        "endpoints": ["/register_passenger", "/auto_entry", "/auto_exit", "/vehicle_status", "/registered_passengers", "/completed_journeys", "/active_alerts", "/clear_data", "/health"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "registered": len(registered_passengers)}

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
            return {"status": "error", "message": "No face detected. Please use a clear face image."}
        
        # Check if passenger already exists
        for p in registered_passengers:
            if p["passenger_id"] == passenger_id:
                return {"status": "error", "message": f"Passenger ID {passenger_id} already exists!"}
        
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
        
        print(f"✅ Registered: {name} ({passenger_id})")
        
        return {"status": "success", "message": f"✅ {name} registered successfully!", "passenger": passenger_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/auto_entry")
async def auto_entry(file: UploadFile = File(...), camera_id: str = Form("")):
    try:
        contents = await file.read()
        location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
        current_time = datetime.now()
        
        matched_person, confidence = match_face_in_db(contents)
        
        if matched_person:
            pid = matched_person["passenger_id"]
            
            if pid in active_sessions:
                return {
                    "status": "warning",
                    "event": "ALREADY_INSIDE",
                    "message": f"⚠️ {matched_person['name']} is already inside!",
                    "current_occupancy": len(active_sessions)
                }
            
            session = {
                "passenger_id": pid,
                "passenger_name": matched_person["name"],
                "passenger_type": matched_person["passenger_type"],
                "gender": matched_person["gender"],
                "entry_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "entry_location": location["address"],
                "entry_gps": f"{location['lat']}, {location['lon']}",
                "attendance": "PRESENT"
            }
            active_sessions[pid] = session
            
            return {
                "status": "success",
                "event": "REGISTERED_ENTRY",
                "message": f"✅ {matched_person['name']} ENTERED - Attendance MARKED PRESENT",
                "passenger": matched_person,
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "entry_time": session["entry_time"],
                "confidence": round(confidence * 100, 2),
                "current_occupancy": len(active_sessions),
                "attendance": "PRESENT"
            }
        else:
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
            
            return {
                "status": "warning",
                "event": "UNREGISTERED_ENTRY",
                "message": f"🚨 UNREGISTERED PERSON at {location['address']}! Alert triggered",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "alert": alert,
                "current_occupancy": len(active_sessions)
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/auto_exit")
async def auto_exit(file: UploadFile = File(...), camera_id: str = Form("")):
    try:
        contents = await file.read()
        location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
        exit_time = datetime.now()
        
        matched_person, confidence = match_face_in_db(contents)
        
        if not matched_person:
            return {
                "status": "warning",
                "event": "NOT_REGISTERED",
                "message": "Face not recognized. Please register first."
            }
        
        pid = matched_person["passenger_id"]
        
        if pid not in active_sessions:
            return {
                "status": "warning",
                "event": "NOT_INSIDE",
                "message": f"⚠️ {matched_person['name']} is not inside the vehicle!",
                "current_occupancy": len(active_sessions)
            }
        
        session = active_sessions[pid]
        entry_time = datetime.strptime(session["entry_time"], "%Y-%m-%d %H:%M:%S")
        duration_seconds = (exit_time - entry_time).total_seconds()
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        journey = {
            "passenger_name": matched_person["name"],
            "passenger_id": pid,
            "entry_time": session["entry_time"],
            "entry_location": session["entry_location"],
            "entry_gps": session["entry_gps"],
            "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "exit_location": location["address"],
            "exit_gps": f"{location['lat']}, {location['lon']}",
            "duration": duration_str
        }
        completed_journeys.append(journey)
        del active_sessions[pid]
        
        return {
            "status": "success",
            "event": "EXIT",
            "message": f"✅ {matched_person['name']} EXITED - Journey completed!",
            "passenger": matched_person,
            "exit_location": location["address"],
            "exit_gps": f"{location['lat']}, {location['lon']}",
            "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "journey_duration": duration_str,
            "current_occupancy": len(active_sessions),
            "journey": journey
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

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

@app.delete("/clear_data")
async def clear_data():
    global registered_passengers, active_sessions, completed_journeys, alerts, known_face_encodings, known_face_data
    registered_passengers = []
    active_sessions = {}
    completed_journeys = []
    alerts = []
    known_face_encodings = []
    known_face_data = []
    if os.path.exists("D:/transit-intelligence-system/data/face_db.pkl"):
        os.remove("D:/transit-intelligence-system/data/face_db.pkl")
    return {"status": "success", "message": "All data cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
