# backend/multi_camera_system.py (Updated Title)
# Add this at the top of the existing file

# Change the lifespan print statement:
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 80)
    print("🎯 AI-POWERED TRANSIT INTELLIGENCE SYSTEM")
    print("=" * 80)
    print("Developed by: Kalyanasundar")
    print("=" * 80)
    os.makedirs("D:/VehicleSurveillanceSystem/data/face_images", exist_ok=True)
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    print("✅ Multi-Camera Support Enabled")
    print("✅ AI Agents Initialized")
    print("📡 Server: http://localhost:8001")
    print("=" * 80)
    yield
    print("👋 Shutting down...")

# Also update the root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI-Powered Transit Intelligence System",
        "developed_by": "Kalyanasundar",
        "registered_passengers": len(db.get_all_passengers()),
        "current_occupancy": tracking_agent.get_current_occupancy(),
        "completed_journeys": len(tracking_agent.get_completed_journeys()),
        "active_alerts": len(alert_agent.get_active_alerts()),
        "cameras": list(GPS_LOCATIONS.keys())
    }
