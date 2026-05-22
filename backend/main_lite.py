from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import random

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Vehicle Surveillance System Starting (Lite Mode)...")
    print("✅ System Ready! (Using demo detection)")
    yield
    print("👋 Shutting down...")

app = FastAPI(
    title="Vehicle Surveillance System",
    version="3.0.0-lite",
    description="AI-Powered Smart Vehicle Surveillance (Demo Mode)",
    lifespan=lifespan
)

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
        "version": "3.0.0-lite",
        "mode": "demo",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "demo",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/process_frame")
async def process_frame(file: UploadFile = File(...), camera_id: str = "cam_001"):
    """Process frame with demo detection"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"status": "error", "message": "Could not decode image"}
        
        h, w = frame.shape[:2]
        
        # Generate random passenger count between 0 and 8
        passenger_count = random.randint(0, 8)
        passengers = []
        
        # Create random bounding boxes
        for i in range(passenger_count):
            x1 = w * (0.1 + random.random() * 0.8)
            y1 = h * (0.2 + random.random() * 0.6)
            x2 = x1 + w * (0.1 + random.random() * 0.2)
            y2 = y1 + h * (0.2 + random.random() * 0.3)
            
            passengers.append({
                "track_id": i + 1,
                "identity": random.choice(["John Doe", "Jane Smith", "Unknown", "Robert Johnson", "Alice Brown"]),
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": round(0.7 + random.random() * 0.29, 2)
            })
        
        # Random alerts
        alerts = []
        if random.random() < 0.1:  # 10% chance of alert
            alerts.append({
                "type": "UNKNOWN_PERSON",
                "message": "Unidentified person detected",
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "status": "success",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "passenger_count": passenger_count,
            "passengers": passengers,
            "alerts": alerts,
            "mode": "demo",
            "fps": 30
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/register_face")
async def register_face(name: str, passenger_id: str):
    """Register a new passenger (demo mode)"""
    return {
        "status": "success",
        "message": f"Demo mode: Passenger {name} (ID: {passenger_id}) registered",
        "name": name,
        "id": passenger_id
    }

@app.get("/attendance/{bus_id}")
async def get_attendance(bus_id: str, date: str = None):
    """Get attendance report"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    mock_attendance = [
        {"passenger_id": "P001", "name": "John Doe", "boarding_time": "08:15 AM", "status": "present"},
        {"passenger_id": "P002", "name": "Jane Smith", "boarding_time": "08:20 AM", "status": "present"},
        {"passenger_id": "P003", "name": "Robert Johnson", "boarding_time": "08:25 AM", "status": "present"},
        {"passenger_id": "P004", "name": "Alice Brown", "boarding_time": "08:30 AM", "status": "late"},
        {"passenger_id": "P005", "name": "Charlie Wilson", "boarding_time": "08:35 AM", "status": "present"},
    ]
    
    return {
        "bus_id": bus_id,
        "date": date,
        "total_passengers": len(mock_attendance),
        "present_count": sum(1 for p in mock_attendance if p["status"] == "present"),
        "attendance": mock_attendance,
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚌 Vehicle Surveillance System (Lite Mode)")
    print("=" * 50)
    print("📡 Server: http://0.0.0.0:8000")
    print("📚 API Docs: http://0.0.0.0:8000/docs")
    print("❤️ Health: http://0.0.0.0:8000/health")
    print("=" * 50)
    print("💡 Running in DEMO MODE with simulated detections")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
