# frontend/ultimate_app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import time

st.set_page_config(page_title="AI Transit System", page_icon="🚀", layout="wide")

import os
API_URL = os.environ.get("API_URL", "http://localhost:8001")

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

# Sidebar
with st.sidebar:
    st.markdown("### 📷 Camera Controls")
    selected_camera = st.selectbox("Select Camera", list(camera_locations.keys()))
    loc = camera_locations[selected_camera]
    st.info(f"📍 {loc['address']}\nGPS: {loc['lat']}, {loc['lon']}")
    
    st.markdown("---")
    st.markdown("### 📊 Live Status")
    try:
        s = requests.get(f"{API_URL}/vehicle_status", timeout=3).json()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👥 Occupancy", s.get("current_occupancy", 0))
        with col2:
            st.metric("🚨 Alerts", s.get("active_alerts", 0))
        st.metric("📋 Registered", s.get("total_registered", 0))
        st.metric("✅ Completed", s.get("completed_journeys_count", 0))
    except:
        st.info("Starting backend...")
    
    st.markdown("---")
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_registered_persons()
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center;">
        <p>🚀 Built with ❤️ by</p>
        <p><strong>KalyanaSundar - AI Engineer</strong></p>
        <p style="font-size: 0.8rem;">GitHub: sundar66kalyan</p>
    </div>
    """, unsafe_allow_html=True)

tabs = st.tabs(["📝 REGISTER", "🤖 AUTO SCAN", "👥 OCCUPANCY", "📊 JOURNEY", "🚨 ALERTS"])

# ============ TAB 1: REGISTER ============
with tabs[0]:
    st.markdown("### Register New Person")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", placeholder="Enter name")
        pid = st.text_input("Person ID", placeholder="Unique ID")
        gender = st.selectbox("Gender", ["Male", "Female"])
        ptype = st.selectbox("Type", ["Student", "Regular", "Staff", "VIP"])
        phone = st.text_input("Phone")
        email = st.text_input("Email")
    with col2:
        uploaded = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.image(uploaded, width=200)
            if st.button("✅ REGISTER", type="primary"):
                if name and pid:
                    img_bytes = convert_image_to_rgb_bytes(uploaded)
                    if img_bytes:
                        result = register_passenger(name, pid, ptype, gender, phone, email, "", img_bytes)
                        if result.get("status") == "success":
                            st.success(result.get("message"))
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(result.get("message"))
    st.markdown("---")
    st.subheader("Registered Persons")
    fetch_registered_persons()
    if st.session_state.registered_persons:
        df = pd.DataFrame(st.session_state.registered_persons)
        st.dataframe(df, use_container_width=True)

# ============ TAB 2: AUTO SCAN (Entry & Exit) ============
with tabs[1]:
    st.markdown(f"### 🤖 AI Auto Scan - {selected_camera}")
    
    st.info("""
    **AI Agent Auto Detection:**
    - **ENTRY SCAN:** Registered = Marked PRESENT with GPS | Unregistered = ALERT triggered
    - **EXIT SCAN:** Records exit time and calculates journey duration
    """)
    
    col1, col2 = st.columns(2)
    
    # ============ ENTRY SCAN ============
    with col1:
        st.markdown("### 🚪 ENTRY SCAN")
        st.caption("Upload face for ENTRY detection")
        
        entry_face = st.file_uploader("Upload face for ENTRY", type=["jpg", "jpeg", "png"], key="entry")
        
        if entry_face:
            st.image(entry_face, caption="Entry Face", width=150)
            
            if st.button("🔍 SCAN ENTRY", type="primary", use_container_width=True, key="entry_btn"):
                with st.spinner("AI Agent analyzing face for ENTRY..."):
                    img_bytes = convert_image_to_rgb_bytes(entry_face)
                    if img_bytes:
                        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
                        data = {"camera_id": selected_camera}
                        
                        try:
                            response = requests.post(f"{API_URL}/auto_entry", files=files, data=data, timeout=10)
                            if response.status_code == 200:
                                result = response.json()
                                
                                if result.get("event") == "REGISTERED_ENTRY":
                                    st.success(f"✅ {result.get('message')}")
                                    st.success(f"👤 Person: {result.get('passenger', {}).get('name')}")
                                    st.success(f"📍 Location: {result.get('location')}")
                                    st.success(f"📍 GPS: {result.get('gps')}")
                                    st.success(f"🕐 Time: {result.get('entry_time')}")
                                    st.success(f"🎯 Confidence: {result.get('confidence')}%")
                                    st.success(f"👥 Current Occupancy: {result.get('current_occupancy')}")
                                    st.balloons()
                                    
                                elif result.get("event") == "UNREGISTERED_ENTRY":
                                    st.error(f"🚨 {result.get('message')}")
                                    st.error(f"📍 Location: {result.get('location')}")
                                    st.error(f"📍 GPS: {result.get('gps')}")
                                    st.error(f"🕐 Time: {result.get('timestamp')}")
                                    st.warning("⚠️ Alert recorded in Alerts tab")
                                    
                                elif result.get("event") == "ALREADY_INSIDE":
                                    st.warning(result.get("message"))
                            else:
                                st.error(f"Server error: {response.status_code}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            st.info("Make sure backend is running")
    
    # ============ EXIT SCAN ============
    with col2:
        st.markdown("### 🚪 EXIT SCAN")
        st.caption("Upload face for EXIT detection")
        
        exit_face = st.file_uploader("Upload face for EXIT", type=["jpg", "jpeg", "png"], key="exit")
        
        if exit_face:
            st.image(exit_face, caption="Exit Face", width=150)
            
            if st.button("🔍 SCAN EXIT", type="primary", use_container_width=True, key="exit_btn"):
                with st.spinner("AI Agent analyzing face for EXIT..."):
                    img_bytes = convert_image_to_rgb_bytes(exit_face)
                    if img_bytes:
                        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
                        data = {"camera_id": selected_camera}
                        
                        try:
                            response = requests.post(f"{API_URL}/auto_exit", files=files, data=data, timeout=10)
                            if response.status_code == 200:
                                result = response.json()
                                
                                if result.get("event") == "EXIT":
                                    st.success(f"✅ {result.get('message')}")
                                    st.info(f"👤 Person: {result.get('passenger', {}).get('name')}")
                                    st.info(f"📍 Exit Location: {result.get('exit_location')}")
                                    st.info(f"📍 Exit GPS: {result.get('exit_gps')}")
                                    st.info(f"🕐 Exit Time: {result.get('exit_time')}")
                                    st.info(f"⏱️ Journey Duration: {result.get('journey_duration')}")
                                    st.info(f"👥 Remaining Occupancy: {result.get('current_occupancy')}")
                                    
                                elif result.get("event") == "NOT_INSIDE":
                                    st.warning(result.get("message"))
                                elif result.get("event") == "NOT_REGISTERED":
                                    st.warning(result.get("message"))
                            else:
                                st.error(f"Server error: {response.status_code}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            st.info("Make sure backend is running")

# ============ TAB 3: OCCUPANCY ============
with tabs[2]:
    st.markdown("### 👥 Current Occupancy")
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

# ============ TAB 4: JOURNEY ============
with tabs[3]:
    st.markdown("### 📊 Journey History")
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

# ============ TAB 5: ALERTS ============
with tabs[4]:
    st.markdown("### 🚨 Security Alerts")
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
