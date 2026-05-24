import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import time
import os

st.set_page_config(page_title="AI Transit System", page_icon="🚀", layout="wide")

API_URL = "http://localhost:8001"

# Initialize session state
if "registered_persons" not in st.session_state:
    st.session_state.registered_persons = []

camera_locations = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def convert_image_to_rgb_bytes(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=90)
        return img_bytes.getvalue()
    except:
        return None

def register_passenger(name, pid, ptype, gender, phone, email, url, img_bytes):
    files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
    data = {"name": name, "passenger_id": pid, "passenger_type": ptype, "gender": gender, "phone": phone, "email": email, "live_url": url}
    try:
        r = requests.post(f"{API_URL}/register_passenger", files=files, data=data, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"status": "error", "message": "Connection failed"}

def fetch_registered_persons():
    try:
        r = requests.get(f"{API_URL}/registered_passengers", timeout=5)
        if r.status_code == 200:
            st.session_state.registered_persons = r.json().get("passengers", [])
    except:
        pass

def scan_entry(img_bytes, camera_id):
    try:
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {"camera_id": camera_id}
        r = requests.post(f"{API_URL}/auto_entry", files=files, data=data, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def scan_exit(img_bytes, camera_id):
    try:
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {"camera_id": camera_id}
        r = requests.post(f"{API_URL}/auto_exit", files=files, data=data, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# Sidebar
with st.sidebar:
    st.markdown("### Camera Controls")
    selected_camera = st.selectbox("Select Camera", list(camera_locations.keys()))
    loc = camera_locations[selected_camera]
    st.info(f"📍 {loc['address']}\nGPS: {loc['lat']}, {loc['lon']}")
    
    st.markdown("---")
    st.markdown("### Live Status")
    try:
        s = requests.get(f"{API_URL}/vehicle_status", timeout=3).json()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Occupancy", s.get("current_occupancy", 0))
        with col2:
            st.metric("Active Alerts", s.get("active_alerts", 0))
        st.metric("Total Registered", s.get("total_registered", 0))
        st.metric("Completed Journeys", s.get("completed_journeys_count", 0))
    except:
        st.info("Starting backend...")
    
    st.markdown("---")
    if st.button("Refresh Data", use_container_width=True):
        fetch_registered_persons()
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center;">
        <p>Built with ❤️ by</p>
        <p><strong>KalyanaSundar - AI Engineer</strong></p>
        <p style="font-size: 0.8rem;">GitHub: sundar66kalyan</p>
    </div>
    """, unsafe_allow_html=True)

tabs = st.tabs(["REGISTER PERSON", "AUTO SCAN", "CURRENT OCCUPANCY", "JOURNEY HISTORY", "ALERTS"])

# REGISTER TAB
with tabs[0]:
    st.markdown("### Register New Person")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name", placeholder="Enter person name")
        pid = st.text_input("Person ID", placeholder="Unique ID")
        gender = st.selectbox("Gender", ["Male", "Female"])
        ptype = st.selectbox("Person Type", ["Student", "Regular", "Staff", "VIP"])
        phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
        email = st.text_input("Email", placeholder="person@example.com")
        
    with col2:
        st.markdown("### Upload Face Image")
        uploaded_img = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])
        if uploaded_img:
            image = Image.open(uploaded_img)
            st.image(image, caption="Preview", width=200)
            
            if st.button("REGISTER", type="primary", use_container_width=True):
                if name and pid:
                    img_bytes = convert_image_to_rgb_bytes(uploaded_img)
                    if img_bytes:
                        result = register_passenger(name, pid, ptype, gender, phone, email, "", img_bytes)
                        if result.get("status") == "success":
                            st.success(result.get("message"))
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(result.get("message", "Registration failed"))
                else:
                    st.warning("Please enter Name and ID")
    
    st.markdown("---")
    st.subheader("Registered Persons Database")
    fetch_registered_persons()
    if st.session_state.registered_persons:
        df = pd.DataFrame(st.session_state.registered_persons)
        st.dataframe(df, use_container_width=True)
        st.caption(f"Total Registered: {len(st.session_state.registered_persons)} persons")
    else:
        st.info("No registered persons yet")

# AUTO SCAN TAB
with tabs[1]:
    st.markdown(f"### AI Auto Scan - {selected_camera}")
    
    st.info("""
    **AI Agent Auto Detection:**
    - **ENTRY SCAN:** Registered = Marked PRESENT with GPS | Unregistered = ALERT triggered
    - **EXIT SCAN:** Records exit time and calculates journey duration
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ENTRY SCAN")
        entry_face = st.file_uploader("Upload face for ENTRY", type=["jpg", "jpeg", "png"], key="entry")
        if entry_face:
            st.image(entry_face, width=150)
            if st.button("SCAN ENTRY", type="primary", key="entry_btn"):
                img_bytes = convert_image_to_rgb_bytes(entry_face)
                if img_bytes:
                    result = scan_entry(img_bytes, selected_camera)
                    if result:
                        if result.get("event") == "REGISTERED_ENTRY":
                            st.success(result.get("message"))
                            st.info(f"Location: {result.get('location')}")
                            st.info(f"GPS: {result.get('gps')}")
                            st.balloons()
                        elif result.get("event") == "UNREGISTERED_ENTRY":
                            st.error(result.get("message"))
    
    with col2:
        st.markdown("### EXIT SCAN")
        exit_face = st.file_uploader("Upload face for EXIT", type=["jpg", "jpeg", "png"], key="exit")
        if exit_face:
            st.image(exit_face, width=150)
            if st.button("SCAN EXIT", type="primary", key="exit_btn"):
                img_bytes = convert_image_to_rgb_bytes(exit_face)
                if img_bytes:
                    result = scan_exit(img_bytes, selected_camera)
                    if result and result.get("event") == "EXIT":
                        st.success(result.get("message"))
                        st.info(f"Duration: {result.get('duration')}")

# OCCUPANCY TAB
with tabs[2]:
    st.markdown("### Current Occupancy")
    try:
        s = requests.get(f"{API_URL}/vehicle_status").json()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Inside", s.get("current_occupancy", 0))
        with col2:
            st.metric("Males", 0)
        with col3:
            st.metric("Females", 0)
        
        active = s.get("active_passengers", [])
        if active:
            df = pd.DataFrame(active)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No persons currently inside")
    except:
        st.info("No data yet")

# JOURNEY TAB
with tabs[3]:
    st.markdown("### Journey History")
    try:
        r = requests.get(f"{API_URL}/completed_journeys")
        if r.status_code == 200:
            journeys = r.json().get("journeys", [])
            if journeys:
                df = pd.DataFrame(journeys)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No completed journeys yet")
    except:
        pass

# ALERTS TAB
with tabs[4]:
    st.markdown("### Security Alerts")
    try:
        r = requests.get(f"{API_URL}/active_alerts")
        if r.status_code == 200:
            alerts = r.json().get("alerts", [])
            if alerts:
                for alert in alerts:
                    st.error(f"🚨 {alert.get('message')}")
            else:
                st.success("No active alerts")
    except:
        pass

st.markdown("---")
st.caption("🚀 AI-Powered Transit Intelligence System | Developed by KalyanaSundar - AI Engineer")
