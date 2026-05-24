# backend/simple_backend.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import hashlib
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registered_passengers = []
active_sessions = {}

@app.get("/")
async def root():
    return {"message": "AI Transit System API", "status": "running"}

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
    passenger = {
        "passenger_id": passenger_id,
        "name": name,
        "passenger_type": passenger_type,
        "gender": gender,
        "phone": phone,
        "email": email
    }
    registered_passengers.append(passenger)
    return {"status": "success", "message": f"✅ {name} registered!"}

@app.get("/registered_passengers")
async def get_registered():
    return {"passengers": registered_passengers, "count": len(registered_passengers)}

@app.get("/vehicle_status")
async def vehicle_status():
    return {"current_occupancy": len(active_sessions), "total_registered": len(registered_passengers)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
