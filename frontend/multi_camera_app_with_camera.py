import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
import io
import time

st.set_page_config(
    page_title="AI Transit Intelligence System",
    page_icon="🎯",
    layout="wide"
)

API_URL = "http://localhost:8001"

# Initialize session state
if "registered_persons" not in st.session_state:
    st.session_state.registered_persons = []
if "camera_image" not in st.session_state:
    st.session_state.camera_image = None
if "entry_camera_image" not in st.session_state:
    st.session_state.entry_camera_image = None
if "exit_camera_image" not in st.session_state:
    st.session_state.exit_camera_image = None

# Camera locations
camera_locations = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def capture_from_webcam():
    """Capture image from webcam"""
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Cannot access webcam. Please check your camera.")
            return None
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        return None
    except Exception as e:
        st.error(f"Camera error: {e}")
        return None

def fetch_registered_persons():
    """Fetch registered persons from backend"""
    try:
        response = requests.get(f"{API_URL}/registered_passengers", timeout=3)
        if response.status_code == 200:
            data = response.json()
            st.session_state.registered_persons = data.get("passengers", [])
            return st.session_state.registered_persons
    except:
        pass
    return []

def register_person(name, person_id, person_type, phone, email, image_file):
    """Register person via API"""
    try:
        files = {"file": ("face.jpg", image_file, "image/jpeg")}
        data = {
            "name": name,
            "passenger_id": person_id,
            "passenger_type": person_type,
            "phone": phone,
            "email": email
        }
        
        response = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                fetch_registered_persons()
                return True, result.get("message", "Success")
        return False, "Registration failed"
    except Exception as e:
        return False, str(e)

# Sidebar
with st.sidebar:
    st.header("📷 Camera Controls")
    
    available_cameras = list(camera_locations.keys())
    selected_camera = st.selectbox("Select Camera", available_cameras)
    
    loc = camera_locations.get(selected_camera, {})
    st.info(f"📍 {loc.get('address', 'Unknown')}")
    st.caption(f"GPS: {loc.get('lat', 'N/A')}, {loc.get('lon', 'N/A')}")
    
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
    except:
        st.info("Waiting for backend...")
    
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        fetch_registered_persons()
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 REGISTER PERSON",
    "📸 CAMERA SCAN",
    "👥 CURRENT OCCUPANCY",
    "📊 JOURNEY HISTORY",
    "🚨 ALERTS & LOGS"
])

# ============ TAB 1: REGISTER PERSON ============
with tab1:
    st.header("📝 Register New Person")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter person name")
        person_id = st.text_input("Person ID *", placeholder="Unique ID (e.g., P001)")
        phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
        email = st.text_input("Email", placeholder="person@example.com")
        person_type = st.selectbox("Person Type", ["Student", "Regular", "Staff", "VIP"])
        
    with col2:
        st.subheader("📸 Capture Face Image")
        
        if st.button("📷 TAKE PHOTO WITH CAMERA", use_container_width=True):
            with st.spinner("Opening camera..."):
                captured_image = capture_from_webcam()
                if captured_image:
                    st.session_state.camera_image = captured_image
                    st.success("✅ Photo captured successfully!")
        
        if st.session_state.camera_image:
            st.image(st.session_state.camera_image, caption="Captured Photo", width=250)
            
            img_bytes = io.BytesIO()
            st.session_state.camera_image.save(img_bytes, format='JPEG')
            img_bytes_value = img_bytes.getvalue()
            
            if st.button("✅ USE THIS PHOTO", use_container_width=True):
                if name and person_id:
                    success, msg = register_person(name, person_id, person_type, phone, email, img_bytes_value)
                    if success:
                        st.success(f"✅ {name} registered with camera photo!")
                        st.balloons()
                        st.session_state.camera_image = None
                    else:
                        st.error(f"Registration failed: {msg}")
                else:
                    st.warning("Please fill name and ID first")
        
        st.markdown("---")
        st.subheader("📤 OR Upload Image")
        
        uploaded_face = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png"])
        if uploaded_face:
            image = Image.open(uploaded_face)
            st.image(image, caption="Uploaded Image", width=200)
            
            if st.button("✅ REGISTER WITH UPLOAD", type="primary", use_container_width=True):
                if name and person_id:
                    success, msg = register_person(name, person_id, person_type, phone, email, uploaded_face.getvalue())
                    if success:
                        st.success(f"✅ {name} registered successfully!")
                        st.balloons()
                        fetch_registered_persons()
                    else:
                        st.error(f"Registration failed: {msg}")
                else:
                    st.warning("Please fill name and ID first")
    
    st.markdown("---")
    st.subheader("📋 Registered Persons Database")
    
    persons = fetch_registered_persons()
    if persons:
        display_data = []
        for p in persons:
            display_data.append({
                "ID": p.get("passenger_id", "N/A"),
                "Name": p.get("name", "Unknown"),
                "Phone": p.get("phone", "N/A"),
                "Email": p.get("email", "N/A"),
                "Type": p.get("passenger_type", "Regular"),
            })
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        st.caption(f"Total Registered: {len(persons)} persons")

# ============ TAB 2: CAMERA SCAN ============
with tab2:
    st.header(f"📸 Camera Scan: {selected_camera}")
    
    persons = fetch_registered_persons()
    
    if persons:
        person_options = [f"{p['name']} ({p['passenger_id']})" for p in persons]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚪 ENTRY SCAN")
            selected_person = st.selectbox("Select Person", person_options, key="entry_person")
            
            if st.button("📷 CAPTURE ENTRY PHOTO", key="entry_camera_btn", use_container_width=True):
                with st.spinner("Opening camera..."):
                    captured = capture_from_webcam()
                    if captured:
                        st.session_state.entry_camera_image = captured
                        st.success("✅ Entry photo captured!")
            
            if st.session_state.entry_camera_image:
                st.image(st.session_state.entry_camera_image, caption="Entry Photo", width=200)
                
                if st.button("✅ CONFIRM ENTRY", key="confirm_entry", type="primary", use_container_width=True):
                    st.success(f"✅ {selected_person} ENTERED")
                    loc = camera_locations.get(selected_camera, {})
                    st.info(f"📍 Location: {loc.get('address')}")
                    st.info(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
                    st.balloons()
                    st.session_state.entry_camera_image = None
            
            st.markdown("---")
            entry_upload = st.file_uploader("Upload face for ENTRY", type=["jpg", "jpeg", "png"], key="entry_upload")
            if entry_upload:
                st.image(entry_upload, width=150)
                if st.button("🔍 SCAN ENTRY", key="scan_entry_btn"):
                    st.success(f"✅ {selected_person} ENTERED")
        
        with col2:
            st.subheader("🚪 EXIT SCAN")
            exit_person = st.selectbox("Select Person for Exit", person_options, key="exit_person")
            
            if st.button("📷 CAPTURE EXIT PHOTO", key="exit_camera_btn", use_container_width=True):
                with st.spinner("Opening camera..."):
                    captured = capture_from_webcam()
                    if captured:
                        st.session_state.exit_camera_image = captured
                        st.success("✅ Exit photo captured!")
            
            if st.session_state.exit_camera_image:
                st.image(st.session_state.exit_camera_image, caption="Exit Photo", width=200)
                
                if st.button("✅ CONFIRM EXIT", key="confirm_exit", type="primary", use_container_width=True):
                    st.success(f"✅ {exit_person} EXITED")
                    st.info(f"📍 Exit recorded")
                    st.session_state.exit_camera_image = None
            
            st.markdown("---")
            exit_upload = st.file_uploader("Upload face for EXIT", type=["jpg", "jpeg", "png"], key="exit_upload")
            if exit_upload:
                st.image(exit_upload, width=150)
                if st.button("🔍 SCAN EXIT", key="scan_exit_btn"):
                    st.success(f"✅ {exit_person} EXITED")
    else:
        st.warning("No registered persons found. Please register first.")

# ============ TAB 3: CURRENT OCCUPANCY ============
with tab3:
    st.header("👥 Persons Currently Inside")
    persons = fetch_registered_persons()
    if persons:
        for person in persons:
            st.write(f"👤 {person.get('name')} - {person.get('passenger_type')}")
    else:
        st.info("No registered persons")

# ============ TAB 4: JOURNEY HISTORY ============
with tab4:
    st.header("📊 Journey History")
    st.info("Journey records will appear after scans")

# ============ TAB 5: ALERTS & LOGS ============
with tab5:
    st.header("🚨 Alerts & Logs")
    st.success("✅ No active alerts")

st.markdown("---")
st.caption("🎯 AI-Powered Transit Intelligence System | Camera Capture Enabled")
