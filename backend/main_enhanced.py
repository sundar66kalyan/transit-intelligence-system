from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import os
import shutil
from typing import Optional

# Import database module
import sys
sys.path.append("D:/VehicleSurveillanceSystem")
from utils.database import register_passenger, mark_attendance, get_attendance_report, get_all_passengers

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Vehicle Surveillance System Starting...")
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    print("✅ System Ready!")
    yield
    print("👋 Shutting down...")

app = FastAPI(title="Vehicle Surveillance System", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Vehicle Surveillance System API",
        "status": "running",
        "version": "3.0.0",
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
    file: UploadFile = File(...)
):
    """Register a new passenger with face image"""
    try:
        # Save face image
        face_image_path = f"D:/VehicleSurveillanceSystem/data/face_images/{passenger_id}.jpg"
        
        # Read and save image
        contents = await file.read()
        with open(face_image_path, "wb") as f:
            f.write(contents)
        
        # Register in database
        success = register_passenger(passenger_id, name, passenger_type, face_image_path)
        
        if success:
            return {
                "status": "success",
                "message": f"Passenger {name} (ID: {passenger_id}) registered successfully!",
                "name": name,
                "id": passenger_id,
                "image_saved": face_image_path
            }
        else:
            return {"status": "error", "message": "Registration failed"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/mark_attendance")
async def mark_attendance_endpoint(
    passenger_id: str = Form(...),
    bus_id: str = Form(...),
    status: str = Form("present")
):
    """Mark attendance for a passenger"""
    success = mark_attendance(passenger_id, bus_id, status)
    
    if success:
        return {
            "status": "success",
            "message": f"Attendance marked as {status} for {passenger_id}",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {"status": "error", "message": "Failed to mark attendance"}

@app.get("/attendance/{bus_id}")
async def get_attendance(bus_id: str, date: str = None):
    """Get attendance report"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    attendance_data = get_attendance_report(bus_id, date)
    
    # Calculate statistics
    total = len(attendance_data)
    present = sum(1 for a in attendance_data if a["attendance"] == "Present")
    absent = total - present
    
    return {
        "bus_id": bus_id,
        "date": date,
        "total_passengers": total,
        "present_count": present,
        "absent_count": absent,
        "attendance_rate": (present / total * 100) if total > 0 else 0,
        "attendance": attendance_data,
        "generated_at": datetime.now().isoformat()
    }

@app.get("/passengers")
async def get_passengers():
    """Get all registered passengers"""
    return {"passengers": get_all_passengers()}

@app.post("/process_frame")
async def process_frame(file: UploadFile = File(...), camera_id: str = "cam_001"):
    """Process video frame with simulated detection"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"status": "error", "message": "Could not decode image"}
        
        h, w = frame.shape[:2]
        
        # Get registered passengers for demo
        passengers_list = get_all_passengers()
        passenger_names = [p["name"] for p in passengers_list] if passengers_list else ["John Doe", "Jane Smith"]
        
        # Generate random passenger count
        import random
        passenger_count = random.randint(1, min(6, len(passenger_names) + 2))
        passengers = []
        
        for i in range(passenger_count):
            x1 = w * (0.1 + random.random() * 0.8)
            y1 = h * (0.2 + random.random() * 0.6)
            x2 = x1 + w * (0.1 + random.random() * 0.2)
            y2 = y1 + h * (0.2 + random.random() * 0.3)
            
            # Randomly select from registered passengers or unknown
            if passengers_list and random.random() > 0.3:
                passenger = random.choice(passengers_list)
                identity = passenger["name"]
                passenger_id = passenger["passenger_id"]
            else:
                identity = "Unknown"
                passenger_id = None
            
            passengers.append({
                "track_id": i + 1,
                "identity": identity,
                "passenger_id": passenger_id,
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": round(0.7 + random.random() * 0.29, 2)
            })
            
            # Auto-mark attendance for recognized passengers (in demo)
            if passenger_id:
                mark_attendance(passenger_id, camera_id, "present")
        
        return {
            "status": "success",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "passenger_count": passenger_count,
            "passengers": passengers,
            "mode": "demo"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚌 Vehicle Surveillance System Backend")
    print("=" * 50)
    print("📡 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="localhost", port=8000, log_level="info")
