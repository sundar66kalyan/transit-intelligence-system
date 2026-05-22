import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import json
import asyncio
import websockets

st.set_page_config(
    page_title="Vehicle Surveillance - Entry Alert System",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8000"

st.title("🚌 AI-Powered Vehicle Surveillance System")
st.markdown("*Real-Time Entry Detection & GPS Alerts*")

# Initialize session state
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "current_location" not in st.session_state:
    st.session_state.current_location = {}

# Sidebar
with st.sidebar:
    st.header("📍 Live GPS Tracking")
    
    # Get current location
    try:
        response = requests.get(f"{API_URL}/current_location", timeout=2)
        if response.status_code == 200:
            location = response.json()
            st.session_state.current_location = location
            st.metric("Current Stop", location.get("address", "Unknown"))
            st.metric("Coordinates", f"{location.get('lat', 0):.4f}, {location.get('lon', 0):.4f}")
            st.caption(f"Last Updated: {location.get('timestamp', 'N/A')[:19]}")
    except:
        st.warning("GPS tracking unavailable")
    
    st.markdown("---")
    st.header("🚨 Alert Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Active Alerts", len(st.session_state.alerts))
    with col2:
        st.metric("Bus ID", "BUS-001")
    
    st.markdown("---")
    bus_id = st.selectbox("Select Bus", ["BUS-001", "BUS-002", "BUS-003"])

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚪 Entry Detection", "🚨 Live Alerts", "📋 Entry Logs", 
    "👤 Register Passenger", "📍 GPS History"
])

with tab1:
    st.header("Real-Time Entry Detection")
    
    st.info("""
    **How it works:**
    1. Person approaches vehicle entry point
    2. Camera captures face
    3. System checks against registered database
    4. If registered → Auto-mark attendance + Log entry
    5. If unregistered → 🚨 IMMEDIATE ALERT with GPS location
    6. If blacklisted → 🚨 CRITICAL ALERT to security team
    """)
    
    # Simulate entry detection
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📸 Simulate Person Entering", type="primary", use_container_width=True):
            with st.spinner("Processing entry..."):
                # Create dummy image for API
                import cv2
                import numpy as np
                
                dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                _, buffer = cv2.imencode('.jpg', dummy_frame)
                
                response = requests.post(
                    f"{API_URL}/process_entry",
                    files={"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                    data={"bus_id": bus_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result["result"] == "registered":
                        st.success(result["message"])
                        st.balloons()
                        
                        # Show passenger info
                        passenger = result["passenger"]
                        st.json({
                            "Passenger": passenger.get("name"),
                            "ID": passenger.get("passenger_id"),
                            "Type": passenger.get("type"),
                            "Confidence": f"{passenger.get('confidence', 0)*100:.1f}%",
                            "Location": result["location"]["address"]
                        })
                        
                    elif result["result"] == "unauthorized":
                        st.error(result["message"])
                        st.warning("⚠️ UNREGISTERED PERSON DETECTED!")
                        
                        # Add to alerts
                        if result.get("alert"):
                            st.session_state.alerts.insert(0, result["alert"])
                        
                        # Show alert details
                        alert = result["alert"]
                        st.markdown(f"""
                        **Alert Details:**
                        - Type: {alert.get('type')}
                        - Severity: {alert.get('severity')}
                        - Location: {alert.get('location', {}).get('address')}
                        - Time: {alert.get('timestamp')[:19]}
                        - Confidence: {alert.get('confidence', 0)*100:.1f}%
                        """)
                        
                        # Show location on map
                        loc = result["location"]
                        st.map(pd.DataFrame([{"lat": loc["lat"], "lon": loc["lon"]}]))
                        
                else:
                    st.error("Failed to process entry")

with tab2:
    st.header("🚨 Real-Time Security Alerts")
    
    # Auto-refresh alerts
    auto_refresh = st.checkbox("Auto-refresh alerts (every 3 seconds)", value=True)
    
    alert_placeholder = st.empty()
    
    def display_alerts():
        try:
            response = requests.get(f"{API_URL}/active_alerts", timeout=2)
            if response.status_code == 200:
                data = response.json()
                alerts = data.get("alerts", [])
                
                if alerts:
                    for alert in alerts:
                        with alert_placeholder.container():
                            if alert.get("type") == "UNAUTHORIZED_ENTRY":
                                st.error(f"""
                                **🚨 {alert.get('type')}** - Severity: {alert.get('severity')}
                                
                                **Message:** {alert.get('message')}
                                
                                **Location:** {alert.get('location', {}).get('address', 'Unknown')}
                                
                                **Time:** {alert.get('timestamp', 'N/A')[:19]}
                                
                                **Confidence:** {alert.get('confidence', 0)*100:.1f}%
                                """)
                            elif alert.get("type") == "BLACKLISTED_ENTRY":
                                st.error(f"""
                                **⚠️ CRITICAL: {alert.get('type')}** - Severity: {alert.get('severity')}
                                
                                **{alert.get('message')}**
                                
                                **Immediate action required!**
                                """)
                            else:
                                st.info(alert.get('message'))
                else:
                    st.success("✅ No active alerts. System is secure.")
                    
        except Exception as e:
            st.warning(f"Could not fetch alerts: {e}")
    
    display_alerts()
    
    if auto_refresh:
        time.sleep(3)
        st.rerun()
    
    # Manual refresh button
    if st.button("🔄 Refresh Alerts"):
        display_alerts()
    
    # Show alert history
    with st.expander("Alert History"):
        if st.session_state.alerts:
            for alert in st.session_state.alerts[-10:]:
                st.json(alert)
        else:
            st.info("No alert history")

with tab3:
    st.header("📋 Recent Entry/Exit Logs")
    
    if st.button("Refresh Logs"):
        try:
            response = requests.get(f"{API_URL}/recent_entries", params={"limit": 50})
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                
                if entries:
                    df = pd.DataFrame(entries)
                    st.dataframe(df, use_container_width=True)
                    
                    # Statistics
                    st.subheader("Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        registered = len([e for e in entries if e.get("is_registered")])
                        st.metric("Registered Entries", registered)
                    with col2:
                        unknown = len([e for e in entries if not e.get("is_registered")])
                        st.metric("Unknown Persons", unknown)
                    with col3:
                        st.metric("Total Events", len(entries))
                else:
                    st.info("No entries recorded yet")
        except Exception as e:
            st.error(f"Error: {e}")

with tab4:
    st.header("👤 Register New Passenger")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter passenger name")
        passenger_id = st.text_input("Passenger ID *", placeholder="Enter unique ID")
        passenger_type = st.selectbox("Passenger Type", ["Student", "Regular", "Staff", "VIP"])
        is_blacklisted = st.checkbox("Mark as Blacklisted", help="Blacklisted persons will trigger critical alerts")
        
    with col2:
        uploaded_face = st.file_uploader("Upload Face Image *", type=["jpg", "jpeg", "png"])
        if uploaded_face:
            from PIL import Image
            image = Image.open(uploaded_face)
            st.image(image, caption="Face Preview", width=200)
    
    if st.button("✅ Register Passenger", type="primary", use_container_width=True):
        if name and passenger_id and uploaded_face:
            files = {"file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")}
            data = {
                "name": name,
                "passenger_id": passenger_id,
                "passenger_type": passenger_type,
                "is_blacklisted": is_blacklisted
            }
            
            try:
                response = requests.post(f"{API_URL}/register_face", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        if is_blacklisted:
                            st.warning(f"⚠️ {name} registered as BLACKLISTED!")
                        else:
                            st.success(f"✅ {name} registered successfully!")
                        st.balloons()
                    else:
                        st.error("Registration failed")
                else:
                    st.error("Server error")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please fill all required fields")

with tab5:
    st.header("📍 GPS Journey Tracking")
    
    # Show current location on map
    if st.session_state.current_location:
        loc = st.session_state.current_location
        st.subheader("Current Location")
        
        map_data = pd.DataFrame([{
            "lat": loc.get("lat", 28.6139),
            "lon": loc.get("lon", 77.2090)
        }])
        st.map(map_data)
        
        st.metric("Current Stop", loc.get("address", "Unknown"))
        st.caption(f"Last Updated: {loc.get('timestamp', 'N/A')[:19]}")
    
    # Journey route
    st.subheader("Journey Route")
    route_stops = [
        {"stop": "Central Station", "lat": 28.6139, "lon": 77.2090},
        {"stop": "City Mall", "lat": 28.6189, "lon": 77.2140},
        {"stop": "University", "lat": 28.6239, "lon": 77.2190},
        {"stop": "Downtown", "lat": 28.6289, "lon": 77.2240},
        {"stop": "Hospital", "lat": 28.6339, "lon": 77.2290}
    ]
    
    route_df = pd.DataFrame(route_stops)
    st.map(route_df)
    
    # Alert locations
    st.subheader("Alert Locations")
    if st.session_state.alerts:
        alert_locations = []
        for alert in st.session_state.alerts[:5]:
            loc = alert.get("location", {})
            if loc:
                alert_locations.append({
                    "lat": loc.get("lat", 0),
                    "lon": loc.get("lon", 0),
                    "alert": alert.get("type")
                })
        
        if alert_locations:
            st.warning(f"⚠️ {len(alert_locations)} alert locations marked on map")

# Real-time alert sound simulation
st.markdown("""
<script>
// This would trigger browser notification for alerts
</script>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("🚌 Smart Vehicle Surveillance System v4.0 | Real-Time Entry Detection & GPS Alerts")
