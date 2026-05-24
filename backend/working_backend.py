# backend/working_backend.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import base64
import json

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

# GPS Locations
GPS_LOCATIONS = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

# Simple face matching using image hash (for demo)
def get_image_hash(contents):
    import hashlib
    return hashlib.md5(contents).hexdigest()

@app.get("/")
async def root():
    return {
        "message": "Working Transit System",
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
    try:
        contents = await file.read()
        image_hash = get_image_hash(contents)
        
        passenger = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "gender": gender,
            "phone": phone,
            "email": email,
            "live_url": live_url,
            "image_hash": image_hash,
            "registered_date": datetime.now().isoformat()
        }
        registered_passengers.append(passenger)
        
        print(f"✅ Registered: {name} ({passenger_id}) - Hash: {image_hash[:8]}...")
        
        return {"status": "success", "message": f"✅ {name} registered!", "passenger": passenger}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/auto_entry")
async def auto_entry(file: UploadFile = File(...), camera_id: str = Form("")):
    try:
        contents = await file.read()
        uploaded_hash = get_image_hash(contents)
        location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
        
        print(f"Entry scan - Hash: {uploaded_hash[:8]}...")
        
        # Find matching passenger by hash
        matched = None
        for p in registered_passengers:
            if p["image_hash"] == uploaded_hash:
                matched = p
                break
        
        if matched:
            pid = matched["passenger_id"]
            
            if pid in active_sessions:
                return {
                    "event": "ALREADY_INSIDE",
                    "message": f"⚠️ {matched['name']} is already inside!",
                    "current_occupancy": len(active_sessions)
                }
            
            active_sessions[pid] = {
                "passenger_id": pid,
                "passenger_name": matched["name"],
                "passenger_type": matched["passenger_type"],
                "gender": matched["gender"],
                "entry_time": datetime.now().isoformat(),
                "entry_location": location["address"],
                "entry_gps": f"{location['lat']}, {location['lon']}"
            }
            
            return {
                "event": "REGISTERED_ENTRY",
                "message": f"✅ {matched['name']} ENTERED - Attendance MARKED PRESENT",
                "passenger": matched,
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "entry_time": active_sessions[pid]["entry_time"],
                "current_occupancy": len(active_sessions)
            }
        else:
            # Unknown person
            alert = {
                "type": "UNREGISTERED_PERSON",
                "message": f"🚨 UNREGISTERED person detected at {location['address']}!",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "timestamp": datetime.now().isoformat()
            }
            alerts.append(alert)
            
            return {
                "event": "UNREGISTERED_ENTRY",
                "message": f"🚨 UNREGISTERED PERSON at {location['address']}! Alert triggered",
                "location": location["address"],
                "gps": f"{location['lat']}, {location['lon']}",
                "alert": alert
            }
    except Exception as e:
        return {"event": "ERROR", "message": str(e)}

@app.post("/auto_exit")
async def auto_exit(file: UploadFile = File(...), camera_id: str = Form("")):
    try:
        contents = await file.read()
        uploaded_hash = get_image_hash(contents)
        location = GPS_LOCATIONS.get(camera_id, GPS_LOCATIONS["camera_1 - Central Station"])
        
        # Find matching passenger
        matched = None
        for p in registered_passengers:
            if p["image_hash"] == uploaded_hash:
                matched = p
                break
        
        if not matched:
            return {"event": "NOT_REGISTERED", "message": "Face not recognized. Please register first."}
        
        pid = matched["passenger_id"]
        
        if pid not in active_sessions:
            return {"event": "NOT_INSIDE", "message": f"⚠️ {matched['name']} is not inside!"}
        
        session = active_sessions[pid]
        exit_time = datetime.now()
        entry_time = datetime.fromisoformat(session["entry_time"])
        duration_seconds = (exit_time - entry_time).total_seconds()
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        journey = {
            "passenger_name": matched["name"],
            "passenger_id": pid,
            "entry_time": session["entry_time"],
            "entry_location": session["entry_location"],
            "entry_gps": session["entry_gps"],
            "exit_time": exit_time.isoformat(),
            "exit_location": location["address"],
            "exit_gps": f"{location['lat']}, {location['lon']}",
            "duration": duration_str
        }
        completed_journeys.append(journey)
        del active_sessions[pid]
        
        return {
            "event": "EXIT",
            "message": f"✅ {matched['name']} EXITED - Journey completed!",
            "duration": duration_str,
            "current_occupancy": len(active_sessions),
            "journey": journey
        }
    except Exception as e:
        return {"event": "ERROR", "message": str(e)}

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
    global registered_passengers, active_sessions, completed_journeys, alerts
    registered_passengers = []
    active_sessions = {}
    completed_journeys = []
    alerts = []
    return {"status": "success", "message": "All data cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
