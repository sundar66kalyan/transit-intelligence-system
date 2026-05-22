from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import cv2
import numpy as np
from datetime import datetime
import sys
import os
from typing import List, Dict

sys.path.append("D:/VehicleSurveillanceSystem")

try:
    from utils.detection import ObjectDetector
    from utils.tracking import ObjectTracker
    from utils.face_recognition import FaceRecognizer
    DETECTION_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Detection modules not available: {e}")
    DETECTION_AVAILABLE = False

# Global variables for lifespan management
detector = None
tracker = None
face_recognizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Vehicle Surveillance System Starting...")
    global detector, tracker, face_recognizer
    
    if DETECTION_AVAILABLE:
        detector = ObjectDetector()
        tracker = ObjectTracker()
        face_recognizer = FaceRecognizer()
        # Load registered faces
        face_recognizer.load_registered_faces("D:/VehicleSurveillanceSystem/data/registered_faces")
        print("✅ Detection modules loaded")
    else:
        print("⚠️ Running in demo mode")
    
    print("✅ System Ready!")
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(
    title="Vehicle Surveillance System", 
    version="2.0.0",
    description="AI-Powered Smart Vehicle Surveillance with Real-time Passenger Monitoring",
    lifespan=lifespan
)

# CORS configuration
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
        "version": "2.0.0",
        "detection_available": DETECTION_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "process_frame": "POST /process_frame",
            "attendance": "GET /attendance/{bus_id}",
            "websocket": "WS /ws/{client_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "detection": "active" if DETECTION_AVAILABLE else "demo_mode",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/process_frame")
async def process_frame(file: UploadFile = File(...), camera_id: str = "cam_001"):
    """Process single frame for passenger detection and tracking"""
    try:
        # Read and decode image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"status": "error", "message": "Could not decode image"}
        
        # Demo mode fallback
        if not DETECTION_AVAILABLE or detector is None:
            h, w = frame.shape[:2]
            mock_passengers = []
            for i in range(np.random.randint(0, 5)):  # Random 0-4 passengers for demo
                mock_passengers.append({
                    "track_id": i + 1,
                    "identity": "Unknown",
                    "bbox": [
                        w * (0.2 + i * 0.15),
                        h * 0.3,
                        w * (0.4 + i * 0.15),
                        h * 0.8
                    ],
                    "confidence": round(0.7 + np.random.random() * 0.25, 2)
                })
            
            return {
                "status": "success",
                "camera_id": camera_id,
                "timestamp": datetime.now().isoformat(),
                "passenger_count": len(mock_passengers),
                "passengers": mock_passengers,
                "alerts": [],
                "mode": "demo",
                "fps": 30
            }
        
        # Real detection mode
        detections = detector.detect(frame)
        tracks = tracker.update(detections, frame.shape)
        
        # Face recognition on tracked persons
        passengers = []
        for track in tracks:
            face_embedding = face_recognizer.extract_face(frame, track["bbox"])
            identity = "Unknown"
            if face_embedding is not None:
                identity = face_recognizer.match_identity(face_embedding)
            
            passengers.append({
                "track_id": track["id"],
                "identity": identity,
                "bbox": track["bbox"].tolist() if hasattr(track["bbox"], "tolist") else track["bbox"],
                "confidence": track.get("confidence", 0.85)
            })
        
        # Check for security alerts
        alerts = []
        for passenger in passengers:
            if passenger["identity"] == "Blacklisted":
                alerts.append({
                    "type": "SECURITY_ALERT",
                    "message": f"Blacklisted person detected! Track ID: {passenger['track_id']}",
                    "timestamp": datetime.now().isoformat()
                })
        
        return {
            "status": "success",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "passenger_count": len(passengers),
            "passengers": passengers,
            "alerts": alerts,
            "mode": "ai_detection",
            "fps": 30
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/register_face")
async def register_face(name: str, passenger_id: str, file: UploadFile = File(...)):
    """Register a new passenger face"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if not DETECTION_AVAILABLE or face_recognizer is None:
            return {
                "status": "success",
                "message": f"Demo mode: Face registered for {name} (ID: {passenger_id})",
                "name": name,
                "id": passenger_id
            }
        
        # Extract face embedding
        h, w = image.shape[:2]
        bbox = [w*0.2, h*0.2, w*0.8, h*0.8]  # Simplified - in production use face detection
        embedding = face_recognizer.extract_face(image, bbox)
        
        if embedding is not None:
            face_recognizer.register_face(name, embedding)
            return {
                "status": "success",
                "message": f"Face registered for {name} (ID: {passenger_id})",
                "name": name,
                "id": passenger_id
            }
        else:
            return {
                "status": "error",
                "message": "No face detected in the image"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/attendance/{bus_id}")
async def get_attendance(bus_id: str, date: str = None):
    """Get attendance report for a bus"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Mock attendance data
    mock_attendance = [
        {"passenger_id": "P001", "name": "John Doe", "boarding_time": "08:15 AM", "status": "present"},
        {"passenger_id": "P002", "name": "Jane Smith", "boarding_time": "08:20 AM", "status": "present"},
        {"passenger_id": "P003", "name": "Bob Johnson", "boarding_time": "08:25 AM", "status": "present"},
        {"passenger_id": "P004", "name": "Alice Brown", "boarding_time": "08:30 AM", "status": "late"},
    ]
    
    return {
        "bus_id": bus_id,
        "date": date,
        "total_passengers": len(mock_attendance),
        "attendance": mock_attendance,
        "generated_at": datetime.now().isoformat()
    }

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection for real-time updates"""
    await websocket.accept()
    print(f"🔌 Client {client_id} connected")
    try:
        while True:
            # Send heartbeat every 5 seconds
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "heartbeat",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": f"Echo: {data}"
            })
    except Exception as e:
        print(f"⚠️ Client {client_id} disconnected: {e}")

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚌 Vehicle Surveillance System Backend")
    print("=" * 50)
    print(f"📡 Server: http://0.0.0.0:8000")
    print(f"📚 API Docs: http://0.0.0.0:8000/docs")
    print(f"❤️ Health Check: http://0.0.0.0:8000/health")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
