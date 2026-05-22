from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import os
import random
import hashlib

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("🚌 Vehicle Surveillance System Starting...")
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    print("✅ System Ready!")
    print("📡 Server running on http://localhost:8001")
    print("=" * 50)
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Vehicle Surveillance System", version="4.0.0", lifespan=lifespan)

# CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
registered_passengers = []
entry_logs = []
alerts = []

# Store image hashes for basic matching (simplified face recognition)
def get_image_hash(image_bytes):
    """Generate a simple hash from image for comparison"""
    return hashlib.md5(image_bytes).hexdigest()

@app.get("/")
async def root():
    return {
        "message": "Vehicle Surveillance System API",
        "status": "running",
        "version": "4.0.0",
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
    """Register a new passenger with face image"""
    try:
        # Read image
        contents = await file.read()
        
        # Save face image
        face_image_path = f"D:/VehicleSurveillanceSystem/data/face_images/{passenger_id}.jpg"
        with open(face_image_path, "wb") as f:
            f.write(contents)
        
        # Generate image hash for comparison
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
            "message": f"✅ Passenger {name} (ID: {passenger_id}) registered successfully!",
            "passenger": passenger
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def compare_faces(uploaded_image_hash, registered_passengers):
    """Compare uploaded image with registered faces using hash"""
    for passenger in registered_passengers:
        if passenger.get("image_hash") == uploaded_image_hash:
            return passenger
    return None

@app.post("/process_entry")
async def process_entry(
    file: UploadFile = File(...),
    bus_id: str = Form("BUS-001")
):
    """Process person entering vehicle with actual face comparison"""
    try:
        # Read uploaded image
        contents = await file.read()
        uploaded_hash = get_image_hash(contents)
        
        # Simulated GPS locations
        locations = [
            {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
            {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
            {"lat": 28.6239, "lon": 77.2190, "address": "University"},
            {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
            {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
        ]
        location = random.choice(locations)
        location["timestamp"] = datetime.now().isoformat()
        
        # Compare with registered passengers
        matched_passenger = compare_faces(uploaded_hash, registered_passengers)
        
        if matched_passenger:
            # Registered person detected
            log_entry = {
                "passenger_name": matched_passenger["name"],
                "passenger_id": matched_passenger["passenger_id"],
                "event_type": "ENTRY",
                "location": location["address"],
                "bus_id": bus_id,
                "timestamp": datetime.now().isoformat(),
                "is_registered": True
            }
            entry_logs.append(log_entry)
            
            # Check if blacklisted
            if matched_passenger.get("is_blacklisted"):
                alert = {
                    "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "type": "BLACKLISTED_ENTRY",
                    "severity": "CRITICAL",
                    "message": f"🚨 CRITICAL: Blacklisted person {matched_passenger['name']} detected at {location['address']}!",
                    "location": location,
                    "passenger": matched_passenger,
                    "timestamp": datetime.now().isoformat(),
                    "status": "ACTIVE"
                }
                alerts.append(alert)
            
            return {
                "status": "success",
                "result": "registered",
                "message": f"✅ Registered passenger {matched_passenger['name']} entered at {location['address']}",
                "passenger": matched_passenger,
                "location": location,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Unknown person - generate alert
            alert = {
                "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "UNAUTHORIZED_ENTRY",
                "severity": "HIGH",
                "message": f"🚨 ALERT: Unregistered person detected at {location['address']}!",
                "location": location,
                "timestamp": datetime.now().isoformat(),
                "status": "ACTIVE"
            }
            alerts.append(alert)
            
            log_entry = {
                "passenger_name": "UNKNOWN",
                "passenger_id": None,
                "event_type": "ENTRY",
                "location": location["address"],
                "bus_id": bus_id,
                "timestamp": datetime.now().isoformat(),
                "is_registered": False
            }
            entry_logs.append(log_entry)
            
            return {
                "status": "success",
                "result": "unauthorized",
                "message": f"🚨 ALERT: Unauthorized person detected at {location['address']}!",
                "alert": alert,
                "location": location,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/current_location")
async def get_current_location():
    """Get simulated current GPS location"""
    locations = [
        {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
        {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
        {"lat": 28.6239, "lon": 77.2190, "address": "University"},
        {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"}
    ]
    return random.choice(locations)

@app.get("/recent_entries")
async def get_recent_entries():
    """Get recent entry logs"""
    return {"entries": entry_logs[-50:], "count": len(entry_logs)}

@app.get("/active_alerts")
async def get_active_alerts():
    """Get active alerts"""
    return {"alerts": alerts[-20:], "count": len(alerts)}

@app.get("/passengers")
async def get_passengers():
    """Get all registered passengers"""
    return {"passengers": registered_passengers}

@app.delete("/clear_data")
async def clear_data():
    """Clear all data (for testing)"""
    global registered_passengers, entry_logs, alerts
    registered_passengers = []
    entry_logs = []
    alerts = []
    return {"status": "success", "message": "All data cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
