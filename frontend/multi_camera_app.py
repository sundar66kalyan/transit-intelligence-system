# frontend/multi_camera_app.py (Updated with new name)
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import time

st.set_page_config(
    page_title="AI-Powered Transit Intelligence System",
    page_icon="🎯",
    layout="wide"
)

API_URL = "http://localhost:8001"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
    }
    .credit-footer {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-top: 2rem;
    }
    .credit-text {
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🎯 AI-Powered Transit Intelligence System")
st.markdown("*Synchronized Multi-Camera | Real-time Entry/Exit | AI Journey Tracking*")
st.markdown('</div>', unsafe_allow_html=True)

# Initialize session state
if "selected_camera" not in st.session_state:
    st.session_state.selected_camera = "camera_1"
if "last_scan_result" not in st.session_state:
    st.session_state.last_scan_result = None

# Sidebar - Camera Selection & Status
with st.sidebar:
    st.header("📷 Camera Controls")
    
    # Get available cameras
    try:
        cameras_resp = requests.get(f"{API_URL}/cameras", timeout=2)
        if cameras_resp.status_code == 200:
            cameras = cameras_resp.json().get("cameras", [])
            camera_locations = cameras_resp.json().get("locations", {})
            
            selected_camera = st.selectbox("Select Camera", cameras, format_func=lambda x: f"{x} - {camera_locations.get(x, {}).get('address', 'Unknown')[:35]}")
            st.session_state.selected_camera = selected_camera
            
            # Show camera location
            cam_location = camera_locations.get(selected_camera, {})
            st.info(f"📍 {cam_location.get('address', 'Unknown')}")
            st.caption(f"GPS: {cam_location.get('lat', 'N/A')}, {cam_location.get('lon', 'N/A')}")
    except:
        st.error("⚠️ Backend connecting...")
        st.info("Start: python backend/multi_camera_system.py")
    
    st.markdown("---")
    st.header("📊 Live Status")
    
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=2).json()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👥 Current Occupancy", status.get("current_occupancy", 0))
        with col2:
            st.metric("🚨 Active Alerts", status.get("active_alerts", 0))
        
        st.metric("📋 Registered", status.get("total_registered", 0))
        st.metric("✅ Completed Journeys", status.get("completed_journeys", 0))
        st.metric("📊 Total Entries", status.get("total_entries", 0))
        st.metric("🚪 Total Exits", status.get("total_exits", 0))
    except Exception as e:
        st.info("Waiting for backend...")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 REGISTER PERSON",
    "📸 CAMERA SCAN (Entry/Exit)",
    "👥 CURRENT OCCUPANCY",
    "📊 JOURNEY HISTORY",
    "🚨 ALERTS & LOGS"
])

# ============ TAB 1: REGISTER PERSON ============
with tab1:
    st.header("📝 Register New Person")
    
    st.info("""
    **Registration Process:**
    1. Enter person details
    2. Upload a clear face image
    3. System stores face in database
    4. Registered persons will be auto-recognized by any camera
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter person name")
        person_id = st.text_input("Person ID *", placeholder="Unique ID (e.g., P001)")
        person_type = st.selectbox("Person Type", ["Student", "Regular", "Staff", "VIP", "Elderly"])
        
    with col2:
        uploaded_face = st.file_uploader("Upload Face Image *", type=["jpg", "jpeg", "png"], key="register")
        
        if uploaded_face:
            image = Image.open(uploaded_face)
            st.image(image, caption="Face for Recognition", width=200)
            st.caption(f"File: {uploaded_face.name}")
    
    if st.button("✅ REGISTER PERSON", type="primary", use_container_width=True):
        if name and person_id and uploaded_face:
            files = {"file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")}
            data = {"name": name, "passenger_id": person_id, "passenger_type": person_type}
            
            with st.spinner("Registering..."):
                try:
                    response = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.success(f"✅ {name} (ID: {person_id}) registered successfully!")
                            st.balloons()
                        else:
                            st.error(f"Registration failed")
                    else:
                        st.error("Server error")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please fill all fields and upload a face image")
    
    # Show registered persons
    st.markdown("---")
    st.subheader("📋 Registered Persons Database")
    
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
                st.caption(f"Total Registered: {len(passengers)} persons")
            else:
                st.info("No persons registered yet")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 2: CAMERA SCAN (Entry/Exit) ============
with tab2:
    st.header(f"📸 Camera Scan: {st.session_state.selected_camera}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚪 ENTRY SCAN")
        st.caption("Scan person entering")
        
        entry_image = st.file_uploader("Upload face for ENTRY", type=["jpg", "jpeg", "png"], key="entry")
        
        if entry_image:
            st.image(entry_image, width=200)
            
            if st.button("🔍 SCAN ENTRY", type="primary", use_container_width=True):
                with st.spinner("Processing entry..."):
                    files = {"file": ("face.jpg", entry_image.getvalue(), "image/jpeg")}
                    data = {"camera_id": st.session_state.selected_camera, "bus_id": "BUS-001"}
                    
                    response = requests.post(f"{API_URL}/scan_entry", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.last_scan_result = result
                        
                        if result.get("event") == "ENTRY":
                            st.success("✅ REGISTERED PERSON - ENTRY RECORDED")
                            st.balloons()
                            
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Person** | {result.get('passenger', {}).get('name')} |
                            | **ID** | {result.get('passenger', {}).get('passenger_id')} |
                            | **Type** | {result.get('passenger', {}).get('passenger_type')} |
                            | **Attendance** | ✅ PRESENT |
                            | **Entry Time** | {result.get('entry_time', 'N/A')[:19]} |
                            | **Camera** | {result.get('camera_id')} |
                            | **Location** | {result.get('entry_location')} |
                            | **GPS** | {result.get('entry_gps', {}).get('lat')}, {result.get('entry_gps', {}).get('lon')} |
                            | **Current Occupancy** | {result.get('current_occupancy', 0)} |
                            """)
                            
                            # Show map
                            gps = result.get("entry_gps", {})
                            if gps:
                                map_data = pd.DataFrame([{"lat": gps.get("lat"), "lon": gps.get("lon")}])
                                st.map(map_data)
                                
                        elif result.get("event") == "UNAUTHORIZED":
                            st.error("🚨 UNKNOWN PERSON - ALERT TRIGGERED")
                            
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Alert Type** | UNAUTHORIZED ENTRY |
                            | **Location** | {result.get('location')} |
                            | **GPS** | {result.get('gps', {}).get('lat')}, {result.get('gps', {}).get('lon')} |
                            | **Camera** | {result.get('camera_id')} |
                            | **Time** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
                            """)
                            
                            gps = result.get("gps", {})
                            if gps:
                                map_data = pd.DataFrame([{"lat": gps.get("lat"), "lon": gps.get("lon")}])
                                st.map(map_data)
                                
                        elif result.get("event") == "ALREADY_IN_VEHICLE":
                            st.warning(result.get("message"))
                            
                        st.info(f"📊 Total Entries: {result.get('total_entries', 'N/A')} | Total Exits: {result.get('total_exits', 'N/A')}")
                    else:
                        st.error("Scan failed")
    
    with col2:
        st.subheader("🚪 EXIT SCAN")
        st.caption("Scan person exiting")
        
        exit_image = st.file_uploader("Upload face for EXIT", type=["jpg", "jpeg", "png"], key="exit")
        
        if exit_image:
            st.image(exit_image, width=200)
            
            if st.button("🔍 SCAN EXIT", type="primary", use_container_width=True):
                with st.spinner("Processing exit..."):
                    files = {"file": ("face.jpg", exit_image.getvalue(), "image/jpeg")}
                    data = {"camera_id": st.session_state.selected_camera, "bus_id": "BUS-001"}
                    
                    response = requests.post(f"{API_URL}/scan_exit", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.last_scan_result = result
                        
                        if result.get("event") == "EXIT":
                            st.success("✅ EXIT RECORDED - JOURNEY COMPLETED")
                            
                            st.markdown(f"""
                            | Field | Value |
                            |-------|-------|
                            | **Person** | {result.get('passenger', {}).get('name')} |
                            | **ID** | {result.get('passenger', {}).get('passenger_id')} |
                            | **Entry Location** | {result.get('entry_location')} |
                            | **Entry GPS** | {result.get('entry_gps', {}).get('lat')}, {result.get('entry_gps', {}).get('lon')} |
                            | **Exit Location** | {result.get('exit_location')} |
                            | **Exit GPS** | {result.get('exit_gps', {}).get('lat')}, {result.get('exit_gps', {}).get('lon')} |
                            | **Journey Duration** | ⏱️ {result.get('journey_duration')} |
                            | **Remaining Occupancy** | {result.get('current_occupancy', 0)} |
                            """)
                            
                        elif result.get("event") == "NOT_IN_VEHICLE":
                            st.warning(result.get("message"))
                        elif result.get("event") == "NOT_REGISTERED":
                            st.error(result.get("message"))
                            
                        st.info(f"📊 Total Entries: {result.get('total_entries', 'N/A')} | Total Exits: {result.get('total_exits', 'N/A')}")
                    else:
                        st.error("Exit scan failed")
    
    # Display Recent Scan Results
    if st.session_state.last_scan_result:
        st.markdown("---")
        st.subheader("📋 Last Scan Result")
        event = st.session_state.last_scan_result.get("event")
        if event == "ENTRY":
            st.success(f"✅ {st.session_state.last_scan_result.get('message')}")
        elif event == "EXIT":
            st.info(f"🚪 {st.session_state.last_scan_result.get('message')}")
        elif event == "UNAUTHORIZED":
            st.error(f"🚨 {st.session_state.last_scan_result.get('message')}")

# ============ TAB 3: CURRENT OCCUPANCY ============
with tab3:
    st.header("👥 Persons Currently Inside")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_passengers")
        if response.status_code == 200:
            data = response.json()
            passengers = data.get("passengers", [])
            
            st.metric("Total Inside", data.get("count", 0), delta="currently inside")
            
            if passengers:
                for passenger in passengers:
                    with st.expander(f"👤 {passenger.get('passenger_name')} - {passenger.get('passenger_type')}"):
                        st.write(f"**ID:** {passenger.get('passenger_id')}")
                        st.write(f"**Entry Time:** {passenger.get('entry_time', 'N/A')[:19]}")
                        st.write(f"**Entry Location:** {passenger.get('entry_location', {}).get('address')}")
                        st.write(f"**Entry GPS:** {passenger.get('entry_gps', {}).get('lat')}, {passenger.get('entry_gps', {}).get('lon')}")
                        st.write(f"**Entry Camera:** {passenger.get('entry_camera')}")
                        st.write(f"**Status:** ✅ PRESENT")
            else:
                st.info("No persons currently inside")
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
                display_cols = ["passenger_name", "passenger_type", "entry_location", "exit_location", "journey_duration", "entry_time", "exit_time"]
                available_cols = [col for col in display_cols if col in df.columns]
                
                if available_cols:
                    st.dataframe(df[available_cols], use_container_width=True)
                
                st.markdown("---")
                st.subheader("📈 Individual Journey Details")
                
                # Show detailed journey cards
                for journey in journeys[-15:]:
                    with st.container():
                        st.markdown(f"""
                        **👤 {journey.get('passenger_name')}** ({journey.get('passenger_type')})
                        - **Journey ID:** {journey.get('journey_id', 'N/A')}
                        - **Entry Camera:** {journey.get('entry_camera', 'N/A')}
                        - **Entry Location:** {journey.get('entry_location', 'N/A')} at {journey.get('entry_time', 'N/A')[:19]}
                        - **Entry GPS:** {journey.get('entry_gps', {}).get('lat')}, {journey.get('entry_gps', {}).get('lon')}
                        - **Exit Camera:** {journey.get('exit_camera', 'N/A')}
                        - **Exit Location:** {journey.get('exit_location', 'N/A')} at {journey.get('exit_time', 'N/A')[:19]}
                        - **Exit GPS:** {journey.get('exit_gps', {}).get('lat')}, {journey.get('exit_gps', {}).get('lon')}
                        - **Journey Duration:** ⏱️ **{journey.get('journey_duration', 'N/A')}**
                        """)
                        st.markdown("---")
            else:
                st.info("No completed journeys yet. Test by scanning entry then exit.")
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
                    
                    **Camera:** {alert.get('camera_id', 'N/A')}
                    
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
    st.subheader("📋 Recent Scan History")
    
    if st.button("🔄 Refresh History", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/scan_history")
        if response.status_code == 200:
            history = response.json().get("history", [])
            if history:
                df = pd.DataFrame(history)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No scan history yet")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ FOOTER WITH CREDIT ============
st.markdown("---")
st.markdown(f'''
<div class="credit-footer">
    <p class="credit-text">🚀 Project Developed by: Kalyanasundar | AI-Powered Transit Intelligence System</p>
    <p class="credit-text" style="font-size: 0.9rem;">Multi-Camera Synchronization | Real-time Face Recognition | AI Journey Tracking</p>
</div>
''', unsafe_allow_html=True)

st.markdown("---")
st.caption("🎯 AI-Powered Transit Intelligence System v2.0 | Real-time Entry/Exit | AI Journey Tracking | GPS Coordinates")
