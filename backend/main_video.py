from fastapi import FastAPI, File, UploadFile, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import os
import random
import hashlib
import asyncio
import json

# Import AI Agents
import sys
sys.path.append("D:/VehicleSurveillanceSystem")
from agents.passenger_agent import PassengerTrackingAgent, AlertAgent

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("🚌 Vehicle Surveillance System with AI Agents")
    print("=" * 60)
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/video_frames", exist_ok=True)
    print("✅ AI Agents Initialized")
    print("📡 Server running on http://localhost:8001")
    print("=" * 60)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Vehicle Surveillance System", version="5.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Agents
passenger_agent = PassengerTrackingAgent()
alert_agent = AlertAgent()

# In-memory storage
registered_passengers = []
video_stream_active = False
current_frame = None

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

@app.get("/")
async def root():
    return {
        "message": "Vehicle Surveillance System API",
        "status": "running",
        "version": "5.0.0",
        "features": ["Live Video", "Entry/Exit Tracking", "GPS Coordinates", "AI Agents"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/register_face")
async def register_face_endpoint(
    name: str = Form(...),
    passenger_id: str = Form(...),
    passenger_type: str = Form(...),
    is_blacklisted: bool = Form(False),
    file: UploadFile = File(...)
):
    """Register a new passenger"""
    try:
        contents = await file.read()
        face_image_path = f"D:/VehicleSurveillanceSystem/data/face_images/{passenger_id}.jpg"
        with open(face_image_path, "wb") as f:
            f.write(contents)
        
        image_hash = get_image_hash(contents)
        
        passenger = {
            "passenger_id": passenger_id,
            "name": name,
            "passenger_type": passenger_type,
            "is_blacklisted": is_blacklisted,
            "face_image_path": face_image_path,
            "image_hash": image_hash,
            "registered_date": datetime.now().isoformat()
        }
        registered_passengers.append(passenger)
        
        return {
            "status": "success",
            "message": f"✅ Passenger {name} registered!",
            "passenger": passenger
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/process_entry")
async def process_entry(
    file: UploadFile = File(...),
    bus_id: str = Form("BUS-001"),
    event_type: str = Form("ENTRY")
):
    """Process passenger entry or exit with GPS coordinates"""
    try:
        contents = await file.read()
        uploaded_hash = get_image_hash(contents)
        
        # GPS locations for different stops
        locations = {
            "Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
            "City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
            "University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
            "Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
            "Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
        }
        location = random.choice(list(locations.values()))
        location["timestamp"] = datetime.now().isoformat()
        
        # Find matching passenger
        matched_passenger = None
        for p in registered_passengers:
            if p.get("image_hash") == uploaded_hash:
                matched_passenger = p
                break
        
        if event_type == "ENTRY":
            if matched_passenger:
                # Registered entry
                entry_log = passenger_agent.process_entry(matched_passenger, location, bus_id)
                
                # Check blacklist
                if matched_passenger.get("is_blacklisted"):
                    alert = alert_agent.generate_alert(
                        "BLACKLISTED_ENTRY",
                        f"🚨 BLACKLISTED: {matched_passenger['name']} entering at {location['address']}!",
                        location,
                        "CRITICAL",
                        matched_passenger
                    )
                    return {"status": "success", "result": "blacklisted", "entry_log": entry_log, "alert": alert, "location": location}
                
                return {
                    "status": "success",
                    "result": "registered",
                    "message": f"✅ {matched_passenger['name']} ENTERED at {location['address']}",
                    "passenger": matched_passenger,
                    "entry_log": entry_log,
                    "location": location,
                    "current_occupancy": passenger_agent.get_current_occupancy(bus_id)
                }
            else:
                # Unauthorized entry
                alert = alert_agent.generate_alert(
                    "UNAUTHORIZED_ENTRY",
                    f"🚨 ALERT: Unregistered person entering at {location['address']}!",
                    location,
                    "HIGH"
                )
                
                # Log as unknown entry
                unknown_passenger = {"passenger_id": None, "name": "UNKNOWN", "passenger_type": "UNAUTHORIZED"}
                entry_log = passenger_agent.process_entry(unknown_passenger, location, bus_id)
                
                return {
                    "status": "success",
                    "result": "unauthorized",
                    "message": f"🚨 ALERT: Unregistered person detected at {location['address']}!",
                    "alert": alert,
                    "entry_log": entry_log,
                    "location": location,
                    "current_occupancy": passenger_agent.get_current_occupancy(bus_id)
                }
        
        elif event_type == "EXIT":
            if matched_passenger:
                exit_log = passenger_agent.process_exit(matched_passenger["passenger_id"], location, bus_id)
                if exit_log:
                    return {
                        "status": "success",
                        "result": "exited",
                        "message": f"✅ {matched_passenger['name']} EXITED at {location['address']}",
                        "passenger": matched_passenger,
                        "exit_log": exit_log,
                        "location": location,
                        "current_occupancy": passenger_agent.get_current_occupancy(bus_id)
                    }
            
            return {
                "status": "error",
                "message": "Passenger not found in vehicle",
                "current_occupancy": passenger_agent.get_current_occupancy(bus_id)
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...), bus_id: str = Form("BUS-001")):
    """Upload and process video for passenger detection"""
    try:
        video_path = f"D:/VehicleSurveillanceSystem/uploads/{file.filename}"
        with open(video_path, "wb") as f:
            f.write(await file.read())
        
        # Process video frames
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        detections = []
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % 30 == 0:  # Process every 30th frame
                # Simulate detection
                detections.append({
                    "frame": frame_count,
                    "timestamp": frame_count / fps,
                    "passengers_detected": random.randint(0, 5)
                })
        
        cap.release()
        
        return {
            "status": "success",
            "message": f"Video processed: {file.filename}",
            "total_frames": total_frames,
            "duration": total_frames / fps,
            "detections": detections[-20:]  # Last 20 detections
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vehicle_status/{bus_id}")
async def get_vehicle_status(bus_id: str):
    """Get current vehicle status including occupancy"""
    return {
        "bus_id": bus_id,
        "current_occupancy": passenger_agent.get_current_occupancy(bus_id),
        "active_passengers": passenger_agent.get_active_passengers(bus_id),
        "recent_events": passenger_agent.get_occupancy_history(bus_id, 10),
        "active_alerts": alert_agent.get_active_alerts(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/current_location")
async def get_current_location():
    locations = [
        {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
        {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
        {"lat": 28.6239, "lon": 77.2190, "address": "University"},
        {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"}
    ]
    return random.choice(locations)

@app.get("/recent_entries")
async def get_recent_entries():
    return {"entries": passenger_agent.entry_exit_logs[-50:], "count": len(passenger_agent.entry_exit_logs)}

@app.get("/active_alerts")
async def get_active_alerts():
    return {"alerts": alert_agent.get_active_alerts(), "count": len(alert_agent.get_active_alerts())}

@app.get("/passengers")
async def get_passengers():
    return {"passengers": registered_passengers}

@app.delete("/clear_data")
async def clear_data():
    global registered_passengers
    registered_passengers = []
    passenger_agent.entry_exit_logs = []
    passenger_agent.active_passengers = {}
    passenger_agent.vehicle_occupancy = {}
    alert_agent.alerts = []
    return {"status": "success", "message": "All data cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
