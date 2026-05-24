# backend/minimal_backend.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import face_recognition
import numpy as np
from PIL import Image
import io
import pickle

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
registered_passengers = []
active_sessions = {}
completed_journeys = []
alerts = []
known_face_encodings = []
known_face_data = []

GPS_LOCATIONS = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def encode_face(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_np = np.array(image)
        encodings = face_recognition.face_encodings(image_np)
        if encodings:
            return encodings[0]
        return None
    except:
        return None

@app.get("/")
async def root():
    return {
        "message": "AI Transit System",
        "endpoints": ["/health", "/register_passenger", "/auto_entry", "/auto_exit", "/vehicle_status", "/registered_passengers"]
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
    contents = await file.read()
    encoding = encode_face(contents)
    if encoding is None:
        return {"status": "error", "message": "No face detected"}
    
    known_face_encodings.append(encoding)
    passenger = {
        "passenger_id": passenger_id,
        "name": name,
        "passenger_type": passenger_type,
        "gender": gender,
        "phone": phone,
        "email": email,
        "registered_date": datetime.now().isoformat()
    }
    known_face_data.append(passenger)
    registered_passengers.append(passenger)
    
    return {"status": "success", "message": f"✅ {name} registered!"}

@app.post("/auto_entry")
async def auto_entry(file: UploadFile = File(...), camera_id: str = Form("")):
    try:
        contents = await file.read()
        location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
        
        # Try to match face
        uploaded_encoding = encode_face(contents)
        if uploaded_encoding is None:
            return {"event": "NO_FACE", "message": "No face detected in image"}
        
        if len(known_face_encodings) == 0:
            return {"event": "NO_REGISTERED", "message": "No registered faces. Please register first."}
        
        # Compare faces
        face_distances = face_recognition.face_distance(known_face_encodings, uploaded_encoding)
        best_match_index = np.argmin(face_distances)
        confidence = 1 - face_distances[best_match_index]
        
        if confidence >= 0.5:
            passenger = known_face_data[best_match_index]
            pid = passenger["passenger_id"]
            
            if pid in active_sessions:
                return {"event": "ALREADY_INSIDE", "message": f"⚠️ {passenger['name']} already inside"}
            
            active_sessions[pid] = {
                "passenger_id": pid,
                "passenger_name": passenger["name"],
                "entry_time": datetime.now().isoformat(),
                "entry_location": location["address"],
                "entry_gps": f"{location['lat']}, {location['lon']}"
            }
            
            return {
                "event": "REGISTERED_ENTRY",
                "message": f"✅ {passenger['name']} ENTERED",
                "passenger": passenger,
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "confidence": round(confidence * 100, 2),
                "current_occupancy": len(active_sessions)
            }
        else:
            return {
                "event": "UNREGISTERED_ENTRY",
                "message": "🚨 UNREGISTERED PERSON - Alert triggered",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}"
            }
    except Exception as e:
        return {"event": "ERROR", "message": str(e)}

@app.post("/auto_exit")
async def auto_exit(file: UploadFile = File(...), camera_id: str = Form("")):
    try:
        contents = await file.read()
        location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
        
        uploaded_encoding = encode_face(contents)
        if uploaded_encoding is None:
            return {"event": "NO_FACE", "message": "No face detected"}
        
        if len(known_face_encodings) == 0:
            return {"event": "NO_REGISTERED", "message": "No registered faces"}
        
        face_distances = face_recognition.face_distance(known_face_encodings, uploaded_encoding)
        best_match_index = np.argmin(face_distances)
        confidence = 1 - face_distances[best_match_index]
        
        if confidence >= 0.5:
            passenger = known_face_data[best_match_index]
            pid = passenger["passenger_id"]
            
            if pid not in active_sessions:
                return {"event": "NOT_INSIDE", "message": f"⚠️ {passenger['name']} not inside"}
            
            session = active_sessions[pid]
            entry_time = datetime.fromisoformat(session["entry_time"])
            exit_time = datetime.now()
            duration_seconds = (exit_time - entry_time).total_seconds()
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            
            journey = {
                "passenger_name": passenger["name"],
                "entry_time": session["entry_time"],
                "entry_location": session["entry_location"],
                "exit_time": exit_time.isoformat(),
                "exit_location": location["address"],
                "duration": duration_str
            }
            completed_journeys.append(journey)
            del active_sessions[pid]
            
            return {
                "event": "EXIT",
                "message": f"✅ {passenger['name']} EXITED",
                "duration": duration_str,
                "current_occupancy": len(active_sessions),
                "journey": journey
            }
        else:
            return {"event": "NOT_RECOGNIZED", "message": "Face not recognized"}
    except Exception as e:
        return {"event": "ERROR", "message": str(e)}

@app.get("/vehicle_status")
async def vehicle_status():
    return {
        "current_occupancy": len(active_sessions),
        "active_passengers": list(active_sessions.values()),
        "total_registered": len(registered_passengers),
        "completed_journeys_count": len(completed_journeys)
    }

@app.get("/registered_passengers")
async def get_registered():
    return {"passengers": registered_passengers, "count": len(registered_passengers)}

@app.get("/completed_journeys")
async def get_journeys():
    return {"journeys": completed_journeys, "count": len(completed_journeys)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
