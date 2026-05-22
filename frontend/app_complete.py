import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import cv2
import numpy as np
import tempfile
import time

st.set_page_config(
    page_title="Vehicle Surveillance System",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8001"

st.title("🚌 AI-Powered Vehicle Surveillance System")
st.markdown("*Live Video | Entry/Exit Tracking | AI Agents*")

# Initialize session state
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "video_processed" not in st.session_state:
    st.session_state.video_processed = False

# Sidebar
with st.sidebar:
    st.header("📍 Vehicle Status")
    
    # Check backend
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ System Online")
    except:
        st.error("❌ Backend Offline")
        st.stop()
    
    st.markdown("---")
    
    bus_id = st.selectbox("Select Bus", ["BUS-001", "BUS-002", "BUS-003"])
    
    # Get vehicle status
    try:
        status = requests.get(f"{API_URL}/vehicle_status/{bus_id}").json()
        current_occupancy = status.get("current_occupancy", 0)
        
        st.metric("👥 Current Passengers", current_occupancy, delta=f"{current_occupancy} on board")
        
        # Show active passengers
        active = status.get("active_passengers", [])
        if active:
            with st.expander(f"🟢 Active Passengers ({len(active)})"):
                for p in active[-5:]:
                    st.caption(f"• {p.get('name', 'Unknown')} (Entered: {p.get('entry_time', 'N/A')[:16]})")
    except:
        st.metric("👥 Current Passengers", "N/A")
    
    st.markdown("---")
    
    # Alert count
    try:
        alerts = requests.get(f"{API_URL}/active_alerts").json()
        st.metric("🚨 Active Alerts", alerts.get("count", 0))
    except:
        pass

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📹 Live Video", "🚪 Entry/Exit", "🚨 Alerts", 
    "📊 Vehicle Status", "👤 Register", "📍 GPS"
])

with tab1:
    st.header("Live Video Surveillance")
    
    st.info("""
    **Upload a video for passenger detection**
    - System analyzes video for passenger entries/exits
    - Tracks occupancy in real-time
    - Records GPS coordinates for each event
    """)
    
    uploaded_video = st.file_uploader("Upload Video", type=["mp4", "avi", "mov", "mkv"])
    
    if uploaded_video:
        # Save and display video
        video_path = f"D:/VehicleSurveillanceSystem/uploads/{uploaded_video.name}"
        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())
        
        st.video(video_path)
        
        if st.button("🔍 Analyze Video", type="primary"):
            with st.spinner("Analyzing video for passenger movements..."):
                files = {"file": uploaded_video}
                data = {"bus_id": bus_id}
                
                response = requests.post(f"{API_URL}/upload_video", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Analysis complete! Duration: {result.get('duration', 0):.1f} seconds")
                    
                    # Show detections
                    detections = result.get("detections", [])
                    if detections:
                        st.subheader("Detections")
                        df = pd.DataFrame(detections)
                        st.line_chart(df.set_index("frame")["passengers_detected"])
                else:
                    st.error("Analysis failed")

with tab2:
    st.header("🚪 Passenger Entry/Exit Tracking")
    
    st.info("""
    **Track passenger movements with GPS coordinates:**
    - Upload face image for ENTRY → Records entry time & location
    - Upload same face for EXIT → Records exit time & location
    - System calculates journey duration
    - AI Agent maintains current occupancy count
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚪 ENTRY")
        entry_image = st.file_uploader("Capture person for ENTRY", type=["jpg", "jpeg", "png"], key="entry")
        
        if entry_image:
            st.image(entry_image, width=200)
            if st.button("📥 Record ENTRY", type="primary"):
                files = {"file": ("image.jpg", entry_image.getvalue(), "image/jpeg")}
                data = {"bus_id": bus_id, "event_type": "ENTRY"}
                
                response = requests.post(f"{API_URL}/process_entry", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("result") == "registered":
                        st.success(result.get("message"))
                        st.info(f"📍 GPS: {result.get('location', {}).get('address')}")
                        st.metric("Current Occupancy", result.get("current_occupancy", 0))
                    elif result.get("result") == "unauthorized":
                        st.error(result.get("message"))
                        st.warning(f"📍 Alert at: {result.get('location', {}).get('address')}")
                        st.session_state.alerts.insert(0, result.get("alert"))
                else:
                    st.error("Failed to process entry")
    
    with col2:
        st.subheader("🚪 EXIT")
        exit_image = st.file_uploader("Capture person for EXIT", type=["jpg", "jpeg", "png"], key="exit")
        
        if exit_image:
            st.image(exit_image, width=200)
            if st.button("📤 Record EXIT", type="primary"):
                files = {"file": ("image.jpg", exit_image.getvalue(), "image/jpeg")}
                data = {"bus_id": bus_id, "event_type": "EXIT"}
                
                response = requests.post(f"{API_URL}/process_entry", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("result") == "exited":
                        st.success(result.get("message"))
                        st.info(f"📍 GPS: {result.get('location', {}).get('address')}")
                        st.metric("Current Occupancy", result.get("current_occupancy", 0))
                    else:
                        st.warning(result.get("message", "Passenger not found"))
                else:
                    st.error("Failed to process exit")

with tab3:
    st.header("🚨 Security Alerts")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_alerts")
        if response.status_code == 200:
            alerts_data = response.json()
            alerts_list = alerts_data.get("alerts", [])
            
            if alerts_list:
                for alert in alerts_list:
                    with st.container():
                        severity = alert.get("severity", "HIGH")
                        if severity == "CRITICAL":
                            st.error(f"""
                            **🚨 CRITICAL ALERT** - {alert.get('type')}
                            - **Message:** {alert.get('message')}
                            - **GPS Location:** {alert.get('gps_coordinates', {}).get('address', 'Unknown')}
                            - **Coordinates:** {alert.get('gps_coordinates', {}).get('lat')}, {alert.get('gps_coordinates', {}).get('lon')}
                            - **Time:** {alert.get('timestamp', 'N/A')[:19]}
                            """)
                        else:
                            st.warning(f"""
                            **⚠️ Alert:** {alert.get('message')}
                            **Location:** {alert.get('gps_coordinates', {}).get('address')}
                            **Time:** {alert.get('timestamp', 'N/A')[:19]}
                            """)
                        st.markdown("---")
            else:
                st.success("✅ No active alerts")
    except Exception as e:
        st.error(f"Error: {e}")

with tab4:
    st.header("📊 Vehicle Status & Occupancy")
    
    if st.button("🔄 Refresh Status"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/vehicle_status/{bus_id}")
        if response.status_code == 200:
            data = response.json()
            
            # Current occupancy
            st.subheader("Current Status")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Occupancy", data.get("current_occupancy", 0), delta="in vehicle")
            with col2:
                st.metric("Active Passengers", len(data.get("active_passengers", [])))
            with col3:
                st.metric("Active Alerts", len(data.get("active_alerts", [])))
            
            # Active passengers list
            active_passengers = data.get("active_passengers", [])
            if active_passengers:
                st.subheader(f"🟢 Passengers Onboard ({len(active_passengers)})")
                for p in active_passengers:
                    with st.expander(f"{p.get('name')} - {p.get('passenger_type')}"):
                        st.write(f"**Entry Time:** {p.get('entry_time', 'N/A')[:19]}")
                        st.write(f"**Entry Location:** {p.get('entry_location', {}).get('address', 'Unknown')}")
                        st.write(f"**GPS:** {p.get('entry_location', {}).get('lat')}, {p.get('entry_location', {}).get('lon')}")
            else:
                st.info("No passengers currently onboard")
            
            # Recent events
            recent_events = data.get("recent_events", [])
            if recent_events:
                st.subheader("Recent Events")
                df = pd.DataFrame(recent_events)
                st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

with tab5:
    st.header("👤 Register New Passenger")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name")
        passenger_id = st.text_input("Passenger ID")
        passenger_type = st.selectbox("Type", ["Student", "Regular", "Staff", "VIP"])
        is_blacklisted = st.checkbox("Blacklist")
    
    with col2:
        uploaded_face = st.file_uploader("Face Image", type=["jpg", "jpeg", "png"])
        if uploaded_face:
            image = Image.open(uploaded_face)
            st.image(image, width=200)
    
    if st.button("✅ Register"):
        if name and passenger_id and uploaded_face:
            files = {"file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")}
            data = {
                "name": name,
                "passenger_id": passenger_id,
                "passenger_type": passenger_type,
                "is_blacklisted": str(is_blacklisted).lower()
            }
            
            response = requests.post(f"{API_URL}/register_face", files=files, data=data)
            if response.status_code == 200:
                st.success(f"✅ {name} registered!")
                st.balloons()
    
    # List registered
    st.markdown("---")
    st.subheader("Registered Passengers")
    try:
        response = requests.get(f"{API_URL}/passengers")
        if response.status_code == 200:
            passengers = response.json().get("passengers", [])
            if passengers:
                df = pd.DataFrame(passengers)
                if "image_hash" in df.columns:
                    df = df.drop(columns=["image_hash"])
                if "face_image_path" in df.columns:
                    df = df.drop(columns=["face_image_path"])
                st.dataframe(df, use_container_width=True)
    except:
        pass

with tab6:
    st.header("📍 GPS Location Tracking")
    
    if st.button("Get Current Location"):
        response = requests.get(f"{API_URL}/current_location")
        if response.status_code == 200:
            loc = response.json()
            map_data = pd.DataFrame([{"lat": loc["lat"], "lon": loc["lon"]}])
            st.map(map_data)
            st.write(f"**Location:** {loc.get('address')}")
            st.write(f"**GPS:** {loc.get('lat')}, {loc.get('lon')}")

st.markdown("---")
st.caption("🚌 AI-Powered Vehicle Surveillance | Entry/Exit Tracking | Real-time Occupancy")
