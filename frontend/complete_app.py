import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import time

st.set_page_config(
    page_title="AI Vehicle Surveillance",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8001"

st.title("🚌 AI-Powered Vehicle Surveillance System")
st.markdown("*Face Recognition | Real-time Tracking | AI Agents*")

# Initialize session state
if "last_scan" not in st.session_state:
    st.session_state.last_scan = None

# Sidebar - Real-time Status
with st.sidebar:
    st.header("📊 Real-time Dashboard")
    
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=2).json()
        st.metric("👥 Current Occupancy", status.get("current_occupancy", 0), delta="in vehicle")
        st.metric("🚨 Active Alerts", status.get("active_alerts", 0), delta="⚠️")
        st.metric("📋 Today's Journeys", status.get("completed_journeys_today", 0))
    except:
        st.error("⚠️ Connecting to backend...")
        st.info("Start backend: python backend/complete_system.py")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Status"):
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 REGISTER PERSON",
    "📸 ENTRY SCAN", 
    "🚪 EXIT SCAN",
    "👥 CURRENT OCCUPANCY",
    "📊 JOURNEY HISTORY",
    "🚨 ALERTS"
])

# ============ TAB 1: REGISTER PERSON ============
with tab1:
    st.header("📝 Register New Passenger")
    
    st.info("""
    **Registration Process:**
    1. Enter passenger details
    2. Upload a clear face image
    3. System will store face for future recognition
    4. Registered persons will be marked PRESENT on entry
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter passenger name")
        passenger_id = st.text_input("Passenger ID *", placeholder="Unique ID (e.g., P001)")
        passenger_type = st.selectbox("Passenger Type", ["Student", "Regular", "Staff", "VIP", "Elderly"])
        
    with col2:
        uploaded_face = st.file_uploader("Upload Face Image *", type=["jpg", "jpeg", "png"], key="register")
        
        if uploaded_face:
            image = Image.open(uploaded_face)
            st.image(image, caption="Face Preview - This image will be used for recognition", width=200)
            st.caption(f"File: {uploaded_face.name}")
    
    if st.button("✅ REGISTER PASSENGER", type="primary", use_container_width=True):
        if name and passenger_id and uploaded_face:
            files = {"file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")}
            data = {
                "name": name,
                "passenger_id": passenger_id,
                "passenger_type": passenger_type
            }
            
            with st.spinner("Registering passenger..."):
                try:
                    response = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.success(f"✅ {name} (ID: {passenger_id}) registered successfully!")
                            st.balloons()
                        else:
                            st.error(f"Registration failed: {result.get('message')}")
                    else:
                        st.error("Server error")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please fill all fields and upload a face image")
    
    # Show registered passengers
    st.markdown("---")
    st.subheader("📋 Registered Passengers Database")
    
    try:
        response = requests.get(f"{API_URL}/registered_passengers")
        if response.status_code == 200:
            passengers = response.json().get("passengers", [])
            if passengers:
                df = pd.DataFrame(passengers)
                if "image_hash" in df.columns:
                    df = df.drop(columns=["image_hash"])
                if "face_image_path" in df.columns:
                    df = df.drop(columns=["face_image_path"])
                st.dataframe(df, use_container_width=True)
                st.caption(f"Total Registered: {len(passengers)} passengers")
            else:
                st.info("No passengers registered yet. Use the form above to register.")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 2: ENTRY SCAN ============
with tab2:
    st.header("📸 Face Recognition - ENTRY")
    
    st.info("""
    **Entry Process:**
    1. Upload face image of person entering
    2. System matches with registered database
    3. **REGISTERED** → Marked PRESENT, GPS recorded, Occupancy +1
    4. **UNREGISTERED** → 🚨 ALERT triggered with GPS location
    """)
    
    entry_image = st.file_uploader("Upload face image for ENTRY", type=["jpg", "jpeg", "png"], key="entry")
    
    if entry_image:
        col1, col2 = st.columns(2)
        with col1:
            st.image(entry_image, caption="Face to Scan", width=200)
        
        with col2:
            if st.button("🔍 SCAN ENTRY", type="primary", use_container_width=True):
                with st.spinner("Scanning face and checking database..."):
                    files = {"file": ("face.jpg", entry_image.getvalue(), "image/jpeg")}
                    
                    response = requests.post(f"{API_URL}/scan_entry", files=files, data={"bus_id": "BUS-001"})
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.last_scan = result
                        
                        if result.get("result") == "registered":
                            st.success("✅ REGISTERED PASSENGER - ATTENDANCE MARKED")
                            st.balloons()
                            
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Passenger** | {result.get('passenger', {}).get('name')} |
                            | **ID** | {result.get('passenger', {}).get('passenger_id')} |
                            | **Type** | {result.get('passenger', {}).get('passenger_type')} |
                            | **Entry Time** | {result.get('entry_time', 'N/A')[:19]} |
                            | **Location** | {result.get('location', {}).get('address')} |
                            | **GPS Coordinates** | {result.get('gps', {}).get('lat')}, {result.get('gps', {}).get('lon')} |
                            | **Current Occupancy** | {result.get('current_occupancy', 0)} |
                            | **Attendance** | ✅ PRESENT |
                            """)
                            
                            # Show map
                            gps = result.get("gps", {})
                            if gps:
                                map_data = pd.DataFrame([{"lat": gps.get("lat"), "lon": gps.get("lon")}])
                                st.map(map_data)
                                
                        elif result.get("result") == "unauthorized":
                            st.error("🚨 UNREGISTERED PERSON - ALERT TRIGGERED")
                            
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Alert Type** | UNAUTHORIZED ENTRY |
                            | **Severity** | HIGH |
                            | **Location** | {result.get('location', {}).get('address')} |
                            | **GPS Coordinates** | {result.get('gps', {}).get('lat')}, {result.get('gps', {}).get('lon')} |
                            | **Time** | {result.get('timestamp', 'N/A')[:19]} |
                            | **Current Occupancy** | {result.get('current_occupancy', 0)} |
                            """)
                            
                            gps = result.get("gps", {})
                            if gps:
                                map_data = pd.DataFrame([{"lat": gps.get("lat"), "lon": gps.get("lon")}])
                                st.map(map_data)
                    else:
                        st.error("Scan failed")

# ============ TAB 3: EXIT SCAN ============
with tab3:
    st.header("🚪 Face Recognition - EXIT")
    
    st.info("""
    **Exit Process:**
    1. Upload face image of person exiting
    2. System calculates journey duration
    3. Records exit GPS location
    4. Occupancy decreases by 1
    """)
    
    exit_image = st.file_uploader("Upload face image for EXIT", type=["jpg", "jpeg", "png"], key="exit")
    
    if exit_image:
        st.image(exit_image, caption="Face to Scan", width=200)
        
        if st.button("🔍 SCAN EXIT", type="primary", use_container_width=True):
            with st.spinner("Processing exit..."):
                files = {"file": ("face.jpg", exit_image.getvalue(), "image/jpeg")}
                
                response = requests.post(f"{API_URL}/scan_exit", files=files, data={"bus_id": "BUS-001"})
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("result") == "exited":
                        st.success("✅ EXIT RECORDED - JOURNEY COMPLETED")
                        
                        st.markdown(f"""
                        | Field | Value |
                        |-------|-------|
                        | **Passenger** | {result.get('passenger', {}).get('name')} |
                        | **Entry Location** | {result.get('entry_location', 'N/A')} |
                        | **Entry GPS** | {result.get('entry_gps', {}).get('lat')}, {result.get('entry_gps', {}).get('lon')} |
                        | **Exit Location** | {result.get('exit_location', 'N/A')} |
                        | **Exit GPS** | {result.get('exit_gps', {}).get('lat')}, {result.get('exit_gps', {}).get('lon')} |
                        | **Journey Duration** | {result.get('journey_duration', 'N/A')} |
                        | **Remaining Occupancy** | {result.get('current_occupancy', 0)} |
                        """)
                    else:
                        st.warning(result.get("message", "Exit failed"))
                else:
                    st.error("Exit scan failed")

# ============ TAB 4: CURRENT OCCUPANCY ============
with tab4:
    st.header("👥 Passengers Currently in Vehicle")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_passengers")
        if response.status_code == 200:
            data = response.json()
            passengers = data.get("passengers", [])
            
            st.metric("Total Onboard", data.get("count", 0))
            
            if passengers:
                for passenger in passengers:
                    with st.expander(f"🚌 {passenger.get('passenger_name')} - {passenger.get('passenger_type')}"):
                        st.write(f"**Passenger ID:** {passenger.get('passenger_id')}")
                        st.write(f"**Entry Time:** {passenger.get('entry_time', 'N/A')[:19]}")
                        st.write(f"**Entry Location:** {passenger.get('entry_location', {}).get('address')}")
                        st.write(f"**Entry GPS:** {passenger.get('entry_gps', {}).get('lat')}, {passenger.get('entry_gps', {}).get('lon')}")
                        st.write(f"**Status:** 🟢 IN VEHICLE")
            else:
                st.info("No passengers currently in vehicle")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 5: JOURNEY HISTORY ============
with tab5:
    st.header("📊 Journey History with Durations")
    
    if st.button("🔄 Refresh History", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/journey_history")
        if response.status_code == 200:
            data = response.json()
            journeys = data.get("journeys", [])
            
            if journeys:
                st.metric("Total Completed Journeys", data.get("count", 0))
                
                df = pd.DataFrame(journeys)
                display_cols = ["passenger_name", "passenger_type", "entry_location", "exit_location", "journey_duration", "entry_time", "exit_time"]
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[available_cols], use_container_width=True)
            else:
                st.info("No completed journeys yet")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 6: ALERTS ============
with tab6:
    st.header("🚨 Security Alerts")
    
    if st.button("🔄 Refresh Alerts", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_alerts")
        if response.status_code == 200:
            alerts = response.json().get("alerts", [])
            
            if alerts:
                for alert in alerts:
                    st.error(f"""
                    **🚨 {alert.get('type')}** - Severity: {alert.get('severity')}
                    
                    **Message:** {alert.get('message')}
                    
                    **Location:** {alert.get('location')}
                    
                    **GPS:** {alert.get('gps', {}).get('lat')}, {alert.get('gps', {}).get('lon')}
                    
                    **Time:** {alert.get('timestamp', 'N/A')[:19]}
                    """)
                    st.markdown("---")
            else:
                st.success("✅ No active alerts")
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")
st.caption("🚌 AI-Powered Vehicle Surveillance | Face Recognition | Journey Tracking | Real-time Alerts")
