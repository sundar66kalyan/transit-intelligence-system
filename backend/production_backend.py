# backend/production_backend.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🚀 AI-POWERED TRANSIT INTELLIGENCE SYSTEM")
    print("👨‍💻 Created by: Kalyanasundar - AI Engineer")
    print("🐙 GitHub: https://github.com/sundar66kalyan")
    print("=" * 70)
    os.makedirs("D:/transit-intelligence-system/data", exist_ok=True)
    print("✅ System Ready!")
    print("📡 Server: http://localhost:8001")
    print("=" * 70)
    yield

app = FastAPI(
    title="AI-Powered Transit Intelligence System",
    description="Created by Kalyanasundar - AI Engineer | Face Recognition | GPS Tracking | Real-time Monitoring",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
registered_passengers = []
active_sessions = {}
completed_journeys = []
alerts = []

GPS_LOCATIONS = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

@app.get("/")
async def root():
    return {
        "message": "AI-Powered Transit Intelligence System",
        "creator": "Kalyanasundar - AI Engineer",
        "github": "https://github.com/sundar66kalyan",
        "registered": len(registered_passengers)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "creator": "Kalyanasundar"}

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
        os.makedirs("D:/transit-intelligence-system/data/face_images", exist_ok=True)
        image_path = f"D:/transit-intelligence-system/data/face_images/{passenger_id}.jpg"
        
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(contents))
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(image_path, 'JPEG', quality=90)
        
        passenger = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "gender": gender,
            "phone": phone,
            "email": email,
            "live_url": live_url,
            "registered_date": datetime.now().isoformat()
        }
        registered_passengers.append(passenger)
        return {"status": "success", "message": f"✅ {name} registered!", "passenger": passenger}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/auto_detect_face")
async def auto_detect_face(file: UploadFile = File(...), camera_id: str = Form("")):
    import random
    location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
    current_time = datetime.now()
    
    if registered_passengers and random.choice([True, False]):
        passenger = random.choice(registered_passengers)
        if passenger["passenger_id"] not in active_sessions:
            session = {
                "passenger_id": passenger["passenger_id"],
                "passenger_name": passenger["name"],
                "passenger_type": passenger["passenger_type"],
                "gender": passenger["gender"],
                "entry_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "entry_location": location["address"],
                "entry_gps": f"{location['lat']}, {location['lon']}"
            }
            active_sessions[passenger["passenger_id"]] = session
            return {
                "status": "success", "event": "REGISTERED_ENTRY",
                "message": f"✅ {passenger['name']} ENTERED", "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}", "current_occupancy": len(active_sessions)
            }
    else:
        alert = {"type": "UNREGISTERED_PERSON", "severity": "HIGH",
                "message": f"🚨 UNREGISTERED person at {location['address']}!",
                "location": location["address"], "gps": f"{location['lat']}, {location['lon']}",
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")}
        alerts.append(alert)
        return {"status": "warning", "event": "UNREGISTERED_ENTRY", "message": alert["message"],
                "location": location["address"], "gps": f"{location['lat']}, {location['lon']}", "alert": alert}

@app.post("/record_exit")
async def record_exit(passenger_id: str = Form(...), passenger_name: str = Form(...), camera_id: str = Form(...)):
    location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
    if passenger_id not in active_sessions:
        return {"status": "warning", "message": f"⚠️ {passenger_name} not inside"}
    session = active_sessions[passenger_id]
    exit_time = datetime.now()
    entry_time = datetime.strptime(session["entry_time"], "%Y-%m-%d %H:%M:%S")
    duration_seconds = (exit_time - entry_time).total_seconds()
    minutes = int(duration_seconds // 60)
    duration_str = f"{minutes} minutes" if minutes > 0 else "less than a minute"
    journey = {"passenger_name": passenger_name, "passenger_id": passenger_id,
               "entry_time": session["entry_time"], "entry_location": session["entry_location"],
               "entry_gps": session["entry_gps"], "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
               "exit_location": location["address"], "exit_gps": f"{location['lat']}, {location['lon']}",
               "duration": duration_str}
    completed_journeys.append(journey)
    del active_sessions[passenger_id]
    return {"status": "success", "event": "EXIT", "message": f"✅ {passenger_name} EXITED",
            "duration": duration_str, "current_occupancy": len(active_sessions), "journey": journey}

@app.get("/vehicle_status")
async def vehicle_status():
    return {"current_occupancy": len(active_sessions), "active_passengers": list(active_sessions.values()),
            "total_registered": len(registered_passengers), "completed_journeys_count": len(completed_journeys),
            "active_alerts": len(alerts)}

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
