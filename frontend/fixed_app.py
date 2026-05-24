# frontend/fixed_app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
import io
import webbrowser

st.set_page_config(page_title="AI Transit System", page_icon="🤖", layout="wide")

API_URL = "http://localhost:8001"

# Initialize session state
if "registered_persons" not in st.session_state:
    st.session_state.registered_persons = []
if "captured_image" not in st.session_state:
    st.session_state.captured_image = None

camera_locations = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def convert_to_rgb_bytes(image):
    """Convert PIL Image to RGB JPEG bytes"""
    if image.mode == 'RGBA':
        # Create white background for transparent images
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG', quality=95)
    return img_bytes.getvalue()

def capture_from_webcam():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        return None
    except:
        return None

def fetch_registered_persons():
    try:
        r = requests.get(f"{API_URL}/registered_passengers", timeout=3)
        if r.status_code == 200:
            st.session_state.registered_persons = r.json().get("passengers", [])
            return st.session_state.registered_persons
    except:
        pass
    return []

def register_person(name, pid, ptype, gender, phone, email, url, img_bytes):
    try:
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {
            "name": name,
            "passenger_id": pid,
            "passenger_type": ptype,
            "gender": gender,
            "phone": phone,
            "email": email,
            "live_url": url
        }
        r = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
        if r.status_code == 200:
            result = r.json()
            if result.get("status") == "success":
                return True, result.get("message")
            else:
                return False, result.get("message", "Registration failed")
        return False, f"Server error: {r.status_code}"
    except Exception as e:
        return False, str(e)

def auto_detect_face(img_bytes, camera_id):
    try:
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {"camera_id": camera_id}
        r = requests.post(f"{API_URL}/auto_detect_face", files=files, data=data)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        return {"status": "error", "message": str(e)}

def record_exit(pid, name, cam):
    try:
        data = {"passenger_id": pid, "passenger_name": name, "camera_id": cam}
        r = requests.post(f"{API_URL}/record_exit", data=data)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# Sidebar
with st.sidebar:
    st.header("📷 Camera Controls")
    selected_camera = st.selectbox("Select Camera", list(camera_locations.keys()))
    loc = camera_locations[selected_camera]
    st.info(f"📍 {loc['address']}\nGPS: {loc['lat']}, {loc['lon']}")
    st.markdown("---")
    st.header("📊 Live Status")
    try:
        s = requests.get(f"{API_URL}/vehicle_status", timeout=2).json()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Occupancy", s.get("current_occupancy", 0))
        with col2:
            st.metric("Unregistered", s.get("unregistered_count", 0))
        st.metric("Registered", s.get("total_registered", 0))
        st.metric("Alerts", s.get("active_alerts", 0))
    except:
        st.error("Backend not connected")
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        fetch_registered_persons()
        st.rerun()

tabs = st.tabs(["📝 REGISTER PERSON", "🤖 AI AUTO SCAN", "👥 CURRENT OCCUPANCY", "📊 JOURNEY HISTORY", "🚨 ALERTS"])

# ============ TAB 1: REGISTER PERSON ============
with tabs[0]:
    st.header("Register New Person")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter person name")
        pid = st.text_input("Person ID *", placeholder="Unique ID")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        ptype = st.selectbox("Person Type", ["Student", "Regular", "Staff", "VIP"])
        phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
        email = st.text_input("Email", placeholder="person@example.com")
        
        col_url, col_btn = st.columns([3, 1])
        with col_url:
            live_url = st.text_input("Live URL", placeholder="https://linkedin.com/in/username")
        with col_btn:
            if live_url:
                if st.button("🔗 CONNECT", use_container_width=True):
                    webbrowser.open_new_tab(live_url)
    
    with col2:
        st.subheader("📸 Capture or Upload Face Image")
        
        if st.button("📷 TAKE PHOTO WITH CAMERA", use_container_width=True):
            with st.spinner("Opening camera..."):
                captured = capture_from_webcam()
                if captured:
                    st.session_state.captured_image = captured
                    st.success("✅ Photo captured!")
        
        if st.session_state.captured_image:
            st.image(st.session_state.captured_image, caption="Captured Photo", width=200)
            img_bytes = convert_to_rgb_bytes(st.session_state.captured_image)
            
            if st.button("✅ USE THIS PHOTO", use_container_width=True):
                if name and pid:
                    success, msg = register_person(name, pid, ptype, gender, phone, email, live_url, img_bytes)
                    if success:
                        st.success(msg)
                        st.balloons()
                        st.session_state.captured_image = None
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill Name and ID")
        
        st.markdown("---")
        st.subheader("📤 OR Upload Image")
        
        uploaded_img = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_img:
            # Open and convert image
            image = Image.open(uploaded_img)
            st.image(image, caption="Uploaded Image", width=200)
            
            # Convert to RGB bytes
            img_bytes = convert_to_rgb_bytes(image)
            
            if st.button("✅ REGISTER WITH UPLOAD", type="primary", use_container_width=True):
                if name and pid:
                    with st.spinner("Processing face..."):
                        success, msg = register_person(name, pid, ptype, gender, phone, email, live_url, img_bytes)
                        if success:
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.warning("Please fill Name and ID")
    
    st.markdown("---")
    st.subheader("📋 Registered Persons Database")
    persons = fetch_registered_persons()
    if persons:
        df = pd.DataFrame(persons)
        st.dataframe(df, use_container_width=True)
        st.success(f"Total Registered: {len(persons)} persons")
    else:
        st.info("No registered persons yet. Register one above!")

# ============ TAB 2: AI AUTO SCAN ============
with tabs[1]:
    st.header(f"🤖 AI Auto Scan - {selected_camera}")
    
    st.info("""
    **AI Agent Auto Detection:**
    - Upload a face image
    - AI Agent automatically matches with database
    - **Registered Person** → Auto-marked PRESENT with GPS
    - **Unregistered Person** → Auto-triggers ALERT with GPS
    """)
    
    uploaded_face = st.file_uploader("Upload face for AI detection", type=["jpg", "jpeg", "png", "webp"], key="auto_scan")
    
    if uploaded_face:
        # Convert image to RGB
        image = Image.open(uploaded_face)
        st.image(image, caption="Uploaded Face", width=200)
        img_bytes = convert_to_rgb_bytes(image)
        
        if st.button("🤖 RUN AI DETECTION", type="primary", use_container_width=True):
            with st.spinner("AI Agent analyzing face..."):
                result = auto_detect_face(img_bytes, selected_camera)
                
                if result:
                    if result.get("event") == "REGISTERED_ENTRY":
                        st.success(f"✅ {result.get('message')}")
                        st.success(f"📍 Location: {result.get('location')}")
                        st.success(f"📍 GPS: {result.get('gps')}")
                        st.success(f"🕐 Time: {result.get('entry_time')}")
                        st.success(f"🎯 Confidence: {result.get('confidence')}%")
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
                    st.error("No response from backend")
    
    st.markdown("---")
    st.subheader("📋 Manual Exit Recording")
    
    persons = fetch_registered_persons()
    if persons:
        opts = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
        selected_exit = st.selectbox("Select Person for Exit", list(opts.keys()))
        passenger = opts[selected_exit]
        
        if st.button("✅ RECORD EXIT", type="primary", use_container_width=True):
            res = record_exit(passenger["passenger_id"], passenger["name"], selected_camera)
            if res and res.get("event") == "EXIT":
                st.success(res["message"])
                st.info(f"⏱️ Duration: {res.get('duration')}")
                st.info(f"👥 Remaining: {res.get('current_occupancy')}")

# ============ TAB 3: CURRENT OCCUPANCY ============
with tabs[2]:
    st.header("👥 Current Occupancy")
    try:
        s = requests.get(f"{API_URL}/vehicle_status").json()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🚪 Total Inside", s.get("current_occupancy", 0))
        with col2:
            st.metric("👨 Registered", s.get("current_occupancy", 0))
        with col3:
            st.metric("🚫 Unregistered", s.get("unregistered_count", 0))
        with col4:
            st.metric("🚨 Alerts", s.get("active_alerts", 0))
        
        active = s.get("active_passengers", [])
        if active:
            df = pd.DataFrame(active)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No persons currently inside")
    except:
        pass

# ============ TAB 4: JOURNEY HISTORY ============
with tabs[3]:
    st.header("📊 Journey History")
    try:
        r = requests.get(f"{API_URL}/completed_journeys")
        if r.status_code == 200:
            journeys = r.json().get("journeys", [])
            if journeys:
                df = pd.DataFrame(journeys)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No journeys yet")
    except:
        pass

# ============ TAB 5: ALERTS ============
with tabs[4]:
    st.header("🚨 Security Alerts")
    try:
        r = requests.get(f"{API_URL}/active_alerts")
        if r.status_code == 200:
            alerts = r.json().get("alerts", [])
            if alerts:
                for alert in alerts:
                    st.error(f"🚨 {alert['message']}\n📍 {alert['location']}\n📍 GPS: {alert['gps']}\n🕐 {alert['timestamp']}")
            else:
                st.success("No active alerts")
    except:
        pass

st.markdown("---")
st.caption("🤖 AI-Powered Transit Intelligence System | Fixed RGBA Image Support")
