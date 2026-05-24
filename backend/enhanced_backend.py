from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import os
import face_recognition
import numpy as np
from PIL import Image, ImageEnhance
import io
import pickle
import cv2

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🤖 ENHANCED FACE RECOGNITION SYSTEM")
    print("=" * 70)
    os.makedirs("D:/transit-intelligence-system/data", exist_ok=True)
    load_face_database()
    print("✅ Backend Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield
    save_face_database()

app = FastAPI(title="Enhanced Face System", version="6.0.0", lifespan=lifespan)

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

def enhance_image_for_face_detection(image_bytes):
    """Enhance image quality for better face detection"""
    try:
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance contrast and brightness
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)
        
        # Resize if too large (for faster processing)
        if image.width > 800:
            ratio = 800 / image.width
            new_size = (800, int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=90)
        return output.getvalue()
    except Exception as e:
        print(f"Image enhancement error: {e}")
        return image_bytes

def encode_face(image_bytes):
    """Extract face encoding from image"""
    try:
        # Enhance image first
        enhanced_bytes = enhance_image_for_face_detection(image_bytes)
        
        # Convert to numpy array
        image = Image.open(io.BytesIO(enhanced_bytes))
        image_np = np.array(image)
        
        # Try multiple times with different parameters
        face_locations = face_recognition.face_locations(image_np, model='hog')
        
        if not face_locations:
            # Try with CNN model (slower but more accurate)
            face_locations = face_recognition.face_locations(image_np, model='hog')
        
        if face_locations:
            encodings = face_recognition.face_encodings(image_np, face_locations)
            if encodings:
                return encodings[0]
        
        return None
    except Exception as e:
        print(f"Face encoding error: {e}")
        return None

def load_face_database():
    global known_face_encodings, known_face_data, registered_passengers
    db_path = "D:/transit-intelligence-system/data/face_db.pkl"
    if os.path.exists(db_path):
        try:
            with open(db_path, "rb") as f:
                data = pickle.load(f)
            known_face_encodings = data.get("encodings", [])
            known_face_data = data.get("data", [])
            registered_passengers = data.get("data", [])
            print(f"✅ Loaded {len(known_face_encodings)} faces from database")
        except Exception as e:
            print(f"Error loading database: {e}")
    else:
        print("No existing database, will create new one")

def save_face_database():
    db_path = "D:/transit-intelligence-system/data/face_db.pkl"
    data = {
        "encodings": known_face_encodings,
        "data": known_face_data
    }
    with open(db_path, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ Saved {len(known_face_encodings)} faces to database")

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
@app.get("/")
async def root():
    return {"message": "Enhanced Face System", "registered": len(registered_passengers)}

@app.get("/health")
async def health():
    return {"status": "healthy", "registered_faces": len(known_face_encodings)}

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
        
        # Try to encode face
        encoding = encode_face(contents)
        
        if encoding is None:
            # Try with different image orientations
            # Sometimes images need to be rotated
            from PIL import ImageOps
            image = Image.open(io.BytesIO(contents))
            
            # Try with flipped image
            flipped = ImageOps.mirror(image)
            flipped_bytes = io.BytesIO()
            flipped.save(flipped_bytes, format='JPEG')
            encoding = encode_face(flipped_bytes.getvalue())
        
        if encoding is None:
            return {
                "status": "error", 
                "message": "No face detected in image. Please use a clear, front-facing photo with good lighting."
            }
        
        # Check if passenger already exists
        for p in registered_passengers:
            if p["passenger_id"] == passenger_id:
                return {"status": "error", "message": f"Passenger ID {passenger_id} already exists!"}
        
        # Store face encoding and data
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
        
        # Save to file immediately
        save_face_database()
        
        print(f"✅ Registered: {name} ({passenger_id}) - Total: {len(registered_passengers)}")
        
        return {
            "status": "success",
            "message": f"✅ {name} registered successfully! Face detected and stored.",
            "passenger": passenger_data,
            "total_registered": len(registered_passengers)
        }
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
            # Registered person found
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
            
            return {
                "status": "warning",
                "event": "UNREGISTERED_ENTRY",
                "message": f"🚨 UNREGISTERED person at {location['address']}! Alert triggered",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "unregistered_count": unregistered_count,
                "alert": alert
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/record_exit")
async def record_exit(
    passenger_id: str = Form(...),
    passenger_name: str = Form(...),
    camera_id: str = Form(...)
):
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
    return {
        "current_occupancy": len(active_sessions),
        "unregistered_count": unregistered_count,
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
    global registered_passengers, active_sessions, completed_journeys, alerts, unregistered_count, known_face_encodings, known_face_data
    registered_passengers = []
    active_sessions = {}
    completed_journeys = []
    alerts = []
    unregistered_count = 0
    known_face_encodings = []
    known_face_data = []
    if os.path.exists("D:/transit-intelligence-system/data/face_db.pkl"):
        os.remove("D:/transit-intelligence-system/data/face_db.pkl")
    return {"status": "success", "message": "All data cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
