from fastapi import FastAPI, File, UploadFile, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import os
import random
from typing import Optional
import json

import sys
sys.path.append("D:/VehicleSurveillanceSystem")
from utils.database import (
    register_passenger, log_entry_exit, get_recent_entries, 
    save_alert, get_all_passengers, is_passenger_blacklisted
)
from utils.gps_tracker import GPSTracker, AlertManager

# Initialize components
gps_tracker = GPSTracker()
alert_manager = AlertManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Vehicle Surveillance System Starting...")
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    print("✅ GPS Tracker Ready")
    print("✅ Alert System Ready")
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Vehicle Surveillance System", version="4.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections for real-time alerts
active_connections = []

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

async def broadcast_alert(alert):
    """Broadcast alert to all connected WebSocket clients"""
    for connection in active_connections:
        try:
            await connection.send_json(alert)
        except:
            pass

@app.get("/")
async def root():
    return {
        "message": "Vehicle Surveillance System API",
        "status": "running",
        "version": "4.0.0",
        "features": ["Entry Detection", "GPS Tracking", "Real-time Alerts"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/current_location")
async def get_current_location():
    """Get current GPS location"""
    location = gps_tracker.get_current_location()
    return location

@app.post("/register_face")
async def register_face_endpoint(
    name: str = Form(...),
    passenger_id: str = Form(...),
    passenger_type: str = Form(...),
    is_blacklisted: bool = Form(False),
    file: UploadFile = File(...)
):
    """Register a new passenger with face image"""
    try:
        # Save face image
        face_image_path = f"D:/VehicleSurveillanceSystem/data/face_images/{passenger_id}.jpg"
        
        contents = await file.read()
        with open(face_image_path, "wb") as f:
            f.write(contents)
        
        success = register_passenger(passenger_id, name, passenger_type, face_image_path, is_blacklisted)
        
        if success:
            return {
                "status": "success",
                "message": f"Passenger {name} (ID: {passenger_id}) registered successfully!",
                "name": name,
                "id": passenger_id,
                "is_blacklisted": is_blacklisted
            }
        else:
            return {"status": "error", "message": "Registration failed"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/process_entry")
async def process_entry(file: UploadFile = File(...), bus_id: str = "BUS-001"):
    """Process person entering the vehicle"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"status": "error", "message": "Could not decode image"}
        
        # Get current GPS location
        location = gps_tracker.get_current_location()
        
        # Get registered passengers
        passengers_list = get_all_passengers()
        
        # Simulate face recognition (in production, use actual face matching)
        # For demo, randomly decide if person is registered
        is_registered = random.choice([True, False]) if passengers_list else False
        
        alert = None
        passenger_info = {}
        
        if is_registered and passengers_list:
            # Registered passenger detected
            passenger = random.choice(passengers_list)
            passenger_info = {
                "passenger_id": passenger["passenger_id"],
                "name": passenger["name"],
                "type": passenger["passenger_type"],
                "confidence": round(0.85 + random.random() * 0.14, 2)
            }
            
            # Check if blacklisted
            if passenger.get("is_blacklisted"):
                alert = alert_manager.generate_alert(
                    "BLACKLISTED_ENTRY", passenger_info, location, passenger_info["confidence"]
                )
                await broadcast_alert(alert)
            
            # Log entry
            log_entry_exit(
                passenger["passenger_id"], passenger["name"], "ENTRY",
                location, bus_id, passenger_info["confidence"], True
            )
            
            result_status = "registered"
            message = f"✅ Registered passenger {passenger['name']} entered at {location.get('address')}"
            
        else:
            # Unknown person detected
            passenger_info = {
                "passenger_id": None,
                "name": "UNKNOWN PERSON",
                "type": "Unauthorized",
                "confidence": round(0.65 + random.random() * 0.2, 2)
            }
            
            # Generate alert for unknown person
            alert = alert_manager.generate_alert(
                "UNAUTHORIZED_ENTRY", passenger_info, location, passenger_info["confidence"]
            )
            
            # Save alert to database
            save_alert(alert)
            
            # Broadcast alert via WebSocket
            await broadcast_alert(alert)
            
            # Log entry
            log_entry_exit(
                None, "UNKNOWN_PERSON", "ENTRY",
                location, bus_id, passenger_info["confidence"], False
            )
            
            result_status = "unauthorized"
            message = f"🚨 ALERT: Unauthorized person detected at {location.get('address')}!"
        
        return {
            "status": "success",
            "result": result_status,
            "message": message,
            "passenger": passenger_info,
            "location": location,
            "alert": alert,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/recent_entries")
async def get_recent_entries_endpoint(limit: int = 50):
    """Get recent entry/exit logs"""
    entries = get_recent_entries(limit)
    return {"entries": entries, "count": len(entries)}

@app.get("/active_alerts")
async def get_active_alerts():
    """Get all active alerts"""
    alerts = alert_manager.get_active_alerts()
    return {"alerts": alerts, "count": len(alerts)}

@app.get("/passengers")
async def get_passengers():
    """Get all registered passengers"""
    return {"passengers": get_all_passengers()}

@app.get("/attendance/{bus_id}")
async def get_attendance(bus_id: str, date: str = None):
    """Get attendance report"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Get entries for the day
    entries = get_recent_entries(100)
    present_passengers = [e for e in entries if e.get("date", "").startswith(date)]
    
    return {
        "bus_id": bus_id,
        "date": date,
        "entries": entries[:20],
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚌 Vehicle Surveillance System v4.0 - With Entry Detection & GPS Alerts")
    print("=" * 60)
    print("📡 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("📍 GPS Tracking: Active")
    print("🚨 Alert System: Active")
    print("=" * 60)
    uvicorn.run(app, host="localhost", port=8000, log_level="info")
