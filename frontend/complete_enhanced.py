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
st.markdown("*Automatic Entry/Exit Detection | Real-time Journey Tracking | AI Agents*")

# Initialize session state
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# Sidebar - Live Status
with st.sidebar:
    st.header("📊 Live Status")
    
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=2).json()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👥 Current Occupancy", status.get("current_occupancy", 0))
        with col2:
            st.metric("🚨 Active Alerts", status.get("active_alerts", 0))
        
        st.metric("📋 Registered", status.get("total_registered", 0))
        st.metric("✅ Completed Journeys", status.get("completed_journeys_count", 0))
    except Exception as e:
        st.error("⚠️ Backend connecting...")
        st.info("Start: python backend/enhanced_system.py")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh All Data", use_container_width=True):
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 REGISTER PERSON",
    "🤖 AUTO SCAN (Entry/Exit)",
    "👥 CURRENT OCCUPANCY",
    "📊 JOURNEY HISTORY",
    "🚨 ALERTS & LOGS"
])

# ============ TAB 1: REGISTER PERSON ============
with tab1:
    st.header("📝 Register New Passenger")
    
    st.info("""
    **Registration Instructions:**
    1. Enter passenger details
    2. Upload a clear face image
    3. System will use this face for automatic recognition
    4. Registered persons will be auto-marked PRESENT on entry
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
            st.image(image, caption="Face for Recognition", width=200)
            st.caption(f"File: {uploaded_face.name}")
    
    if st.button("✅ REGISTER PASSENGER", type="primary", use_container_width=True):
        if name and passenger_id and uploaded_face:
            files = {"file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")}
            data = {
                "name": name,
                "passenger_id": passenger_id,
                "passenger_type": passenger_type
            }
            
            with st.spinner("Registering..."):
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
                st.info("No passengers registered yet")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 2: AUTO SCAN (Entry/Exit) ============
with tab2:
    st.header("🤖 Automatic Entry/Exit Scanner")
    
    st.info("""
    **How Auto Scan Works:**
    1. Upload a face image
    2. System automatically recognizes the face
    3. **If person NOT in vehicle** → ENTRY detected → Marks PRESENT, Records Entry GPS
    4. **If person IN vehicle** → EXIT detected → Calculates Journey Duration, Records Exit GPS
    5. **If unknown face** → 🚨 ALERT triggered with GPS location
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 Upload Face Image")
        uploaded_image = st.file_uploader("Choose image for auto-scan", type=["jpg", "jpeg", "png"], key="auto_scan")
        
        if uploaded_image:
            st.session_state.uploaded_image = uploaded_image
            image = Image.open(uploaded_image)
            st.image(image, caption="Face to Scan", width=250)
            st.caption(f"File: {uploaded_image.name}")
            
            if st.button("🔍 RUN AUTO SCAN", type="primary", use_container_width=True):
                with st.spinner("AI Agent analyzing face..."):
                    files = {"file": ("face.jpg", uploaded_image.getvalue(), "image/jpeg")}
                    
                    response = requests.post(f"{API_URL}/auto_scan", files=files, data={"action": "auto"})
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.scan_result = result
                        
                        if result.get("event") == "ENTRY":
                            st.success("✅ REGISTERED PERSON - ENTRY DETECTED")
                            st.balloons()
                            
                            passenger = result.get("passenger", {})
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Passenger Name** | {passenger.get('name', 'N/A')} |
                            | **Passenger ID** | {passenger.get('passenger_id', 'N/A')} |
                            | **Passenger Type** | {passenger.get('passenger_type', 'N/A')} |
                            | **Attendance Status** | ✅ PRESENT (Auto-marked) |
                            | **Entry Time** | {result.get('entry_time', 'N/A')[:19]} |
                            | **Entry Location** | {result.get('entry_location', 'N/A')} |
                            | **Entry GPS** | {result.get('entry_coordinates', {}).get('lat')}, {result.get('entry_coordinates', {}).get('lon')} |
                            | **Current Occupancy** | {result.get('current_occupancy', 0)} |
                            """)
                            
                            # Show map
                            coords = result.get("entry_coordinates", {})
                            if coords:
                                map_data = pd.DataFrame([{"lat": coords.get("lat"), "lon": coords.get("lon")}])
                                st.map(map_data)
                                
                        elif result.get("event") == "EXIT":
                            st.info("🚪 REGISTERED PERSON - EXIT DETECTED")
                            
                            passenger = result.get("passenger", {})
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Passenger Name** | {passenger.get('name', 'N/A')} |
                            | **Passenger ID** | {passenger.get('passenger_id', 'N/A')} |
                            | **Entry Location** | {result.get('entry_location', 'N/A')} |
                            | **Entry GPS** | {result.get('entry_coordinates', {}).get('lat')}, {result.get('entry_coordinates', {}).get('lon')} |
                            | **Exit Location** | {result.get('exit_location', 'N/A')} |
                            | **Exit GPS** | {result.get('exit_coordinates', {}).get('lat')}, {result.get('exit_coordinates', {}).get('lon')} |
                            | **Journey Duration** | ⏱️ {result.get('journey_duration', 'N/A')} |
                            | **Remaining Occupancy** | {result.get('current_occupancy', 0)} |
                            """)
                            
                        elif result.get("event") == "UNAUTHORIZED":
                            st.error("🚨 UNKNOWN PERSON DETECTED - ALERT TRIGGERED")
                            
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Alert Type** | UNAUTHORIZED ENTRY |
                            | **Severity** | HIGH |
                            | **Location** | {result.get('location', 'N/A')} |
                            | **GPS Coordinates** | {result.get('coordinates', {}).get('lat')}, {result.get('coordinates', {}).get('lon')} |
                            | **Time** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
                            """)
                            
                            coords = result.get("coordinates", {})
                            if coords:
                                map_data = pd.DataFrame([{"lat": coords.get("lat"), "lon": coords.get("lon")}])
                                st.map(map_data)
                    else:
                        st.error("Scan failed. Make sure backend is running.")
    
    with col2:
        st.subheader("📋 Scan History")
        try:
            logs = requests.get(f"{API_URL}/recent_logs").json().get("logs", [])
            for log in logs[-5:]:
                if log.get("type") == "ENTRY":
                    st.success(f"✅ {log.get('passenger')} entered at {log.get('location')}")
                elif log.get("type") == "EXIT":
                    st.info(f"🚪 {log.get('passenger')} exited - Duration: {log.get('duration', 'N/A')}")
                elif log.get("type") == "UNAUTHORIZED":
                    st.error(f"⚠️ Unknown person at {log.get('location')}")
        except:
            pass

# ============ TAB 3: CURRENT OCCUPANCY ============
with tab3:
    st.header("👥 Passengers Currently in Vehicle")
    
    if st.button("🔄 Refresh Occupancy", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_passengers")
        if response.status_code == 200:
            data = response.json()
            passengers = data.get("passengers", [])
            
            st.metric("Total Onboard", data.get("count", 0), delta="in vehicle")
            
            if passengers:
                for passenger in passengers:
                    with st.expander(f"🚌 {passenger.get('passenger_name')} - {passenger.get('passenger_type')}"):
                        st.write(f"**Passenger ID:** {passenger.get('passenger_id')}")
                        st.write(f"**Entry Time:** {passenger.get('entry_time', 'N/A')[:19]}")
                        st.write(f"**Entry Location:** {passenger.get('entry_location', 'N/A')}")
                        st.write(f"**Entry GPS:** {passenger.get('entry_coordinates', {}).get('lat')}, {passenger.get('entry_coordinates', {}).get('lon')}")
                        st.write(f"**Attendance:** ✅ PRESENT")
                        st.write(f"**Status:** 🟢 In Vehicle")
            else:
                st.info("No passengers currently in vehicle")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 4: JOURNEY HISTORY ============
with tab4:
    st.header("📊 Completed Journeys with AI-Calculated Durations")
    
    if st.button("🔄 Refresh Journeys", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/completed_journeys")
        if response.status_code == 200:
            data = response.json()
            journeys = data.get("journeys", [])
            
            if journeys:
                st.metric("Total Completed Journeys", data.get("count", 0))
                
                # Create display dataframe
                df = pd.DataFrame(journeys)
                
                # Format for display
                display_cols = ["passenger_name", "passenger_type", "entry_location", "exit_location", "journey_duration", "entry_time", "exit_time"]
                available_cols = [col for col in display_cols if col in df.columns]
                
                if available_cols:
                    st.dataframe(df[available_cols], use_container_width=True)
                
                st.markdown("---")
                st.subheader("📈 Journey Details")
                
                # Show detailed journey cards
                for journey in journeys[-10:]:
                    with st.container():
                        st.markdown(f"""
                        **🚌 {journey.get('passenger_name')}** ({journey.get('passenger_type')})
                        - **Journey ID:** {journey.get('journey_id', 'N/A')}
                        - **Entry:** {journey.get('entry_location', 'N/A')} at {journey.get('entry_time', 'N/A')[:19]}
                        - **Exit:** {journey.get('exit_location', 'N/A')} at {journey.get('exit_time', 'N/A')[:19]}
                        - **Duration:** ⏱️ **{journey.get('journey_duration', 'N/A')}**
                        - **Entry GPS:** {journey.get('entry_coordinates', {}).get('lat')}, {journey.get('entry_coordinates', {}).get('lon')}
                        - **Exit GPS:** {journey.get('exit_coordinates', {}).get('lat')}, {journey.get('exit_coordinates', {}).get('lon')}
                        """)
                        st.markdown("---")
            else:
                st.info("No completed journeys yet. Use Auto Scan tab to test entry/exit.")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 5: ALERTS & LOGS ============
with tab5:
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
                    
                    **GPS:** {alert.get('coordinates', {}).get('lat')}, {alert.get('coordinates', {}).get('lon')}
                    
                    **Time:** {alert.get('timestamp', 'N/A')[:19]}
                    """)
                    st.markdown("---")
            else:
                st.success("✅ No active alerts")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    st.subheader("📋 Recent Activity Log")
    
    try:
        logs = requests.get(f"{API_URL}/recent_logs").json().get("logs", [])
        if logs:
            for log in logs[-20:]:
                if log.get("type") == "ENTRY":
                    st.success(f"✅ {log.get('passenger')} - ENTRY at {log.get('location')} ({log.get('timestamp', 'N/A')[:19]})")
                elif log.get("type") == "EXIT":
                    st.info(f"🚪 {log.get('passenger')} - EXIT at {log.get('location')} - Duration: {log.get('duration', 'N/A')}")
                elif log.get("type") == "UNAUTHORIZED":
                    st.error(f"⚠️ UNKNOWN PERSON at {log.get('location')} ({log.get('timestamp', 'N/A')[:19]})")
        else:
            st.info("No activity logs yet")
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")
st.caption("🚌 AI-Powered Vehicle Surveillance | Automatic Entry/Exit | Real-time Journey Tracking | GPS Coordinates")
