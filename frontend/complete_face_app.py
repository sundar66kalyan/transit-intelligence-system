# frontend/complete_face_app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
import io

st.set_page_config(page_title="AI Transit System", page_icon="🎯", layout="wide")

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
        r = requests.get(f"{API_URL}/registered_passengers", timeout=2)
        if r.status_code == 200:
            st.session_state.registered_persons = r.json().get("passengers", [])
    except:
        pass

def register_person(name, pid, ptype, gender, phone, email, url, img_bytes):
    files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
    data = {"name": name, "passenger_id": pid, "passenger_type": ptype, "gender": gender, "phone": phone, "email": email, "live_url": url}
    r = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
    if r.status_code == 200:
        return True, r.json().get("message")
    return False, "Failed"

def match_face(img_bytes):
    files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
    r = requests.post(f"{API_URL}/match_face", files=files)
    if r.status_code == 200:
        return r.json()
    return {"matched": False, "reason": "Error"}

def record_entry(pid, name, ptype, gender, cam):
    data = {"passenger_id": pid, "passenger_name": name, "passenger_type": ptype, "gender": gender, "camera_id": cam}
    r = requests.post(f"{API_URL}/record_entry", data=data)
    if r.status_code == 200:
        return r.json()
    return None

def record_unknown_entry(cam):
    data = {"camera_id": cam}
    r = requests.post(f"{API_URL}/record_unknown_entry", data=data)
    if r.status_code == 200:
        return r.json()
    return None

def record_exit(pid, name, cam):
    data = {"passenger_id": pid, "passenger_name": name, "camera_id": cam}
    r = requests.post(f"{API_URL}/record_exit", data=data)
    if r.status_code == 200:
        return r.json()
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
            st.metric("Active Alerts", s.get("active_alerts", 0))
        st.metric("Registered", s.get("total_registered", 0))
        st.metric("Completed", s.get("completed_journeys_count", 0))
    except:
        st.error("Backend not connected")
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        fetch_registered_persons()
        st.rerun()

tabs = st.tabs(["📝 REGISTER PERSON", "📸 CAMERA SCAN", "👥 CURRENT OCCUPANCY", "📊 JOURNEY HISTORY", "🚨 ALERTS & LOGS"])

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
        live_url = st.text_input("Live URL", placeholder="https://linkedin.com/in/username")
    
    with col2:
        st.subheader("📸 Capture or Upload Face Image")
        
        # Camera button
        if st.button("📷 TAKE PHOTO WITH CAMERA", use_container_width=True):
            with st.spinner("Opening camera..."):
                captured = capture_from_webcam()
                if captured:
                    st.session_state.captured_image = captured
                    st.success("✅ Photo captured!")
        
        if st.session_state.captured_image:
            st.image(st.session_state.captured_image, caption="Captured Photo", width=200)
            img_bytes = io.BytesIO()
            st.session_state.captured_image.save(img_bytes, format='JPEG')
            img_value = img_bytes.getvalue()
            
            if st.button("✅ USE THIS PHOTO", use_container_width=True):
                if name and pid:
                    success, msg = register_person(name, pid, ptype, gender, phone, email, live_url, img_value)
                    if success:
                        st.success(msg)
                        st.balloons()
                        st.session_state.captured_image = None
                        fetch_registered_persons()
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill Name and ID")
        
        st.markdown("---")
        st.subheader("📤 OR Upload Image")
        
        uploaded_img = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png"])
        if uploaded_img:
            image = Image.open(uploaded_img)
            st.image(image, caption="Uploaded Image", width=200)
            
            if st.button("✅ REGISTER WITH UPLOAD", type="primary", use_container_width=True):
                if name and pid:
                    success, msg = register_person(name, pid, ptype, gender, phone, email, live_url, uploaded_img.getvalue())
                    if success:
                        st.success(msg)
                        st.balloons()
                        fetch_registered_persons()
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
        display_cols = ["passenger_id", "name", "gender", "passenger_type", "phone", "email", "live_url"]
        available = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available], use_container_width=True)

# ============ TAB 2: CAMERA SCAN ============
with tabs[1]:
    st.header(f"Camera Scan: {selected_camera}")
    
    persons = fetch_registered_persons()
    
    col1, col2 = st.columns(2)
    
    # ============ ENTRY SCAN ============
    with col1:
        st.subheader("🚪 ENTRY SCAN")
        method = st.radio("Choose Entry Method", ["Select from List", "Upload Face for Recognition"], key="entry_method", horizontal=True)
        
        if method == "Select from List":
            if persons:
                opts = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
                selected = st.selectbox("Select Person", list(opts.keys()), key="entry_select")
                passenger = opts[selected]
                if st.button("✅ RECORD ENTRY", type="primary", use_container_width=True):
                    res = record_entry(passenger["passenger_id"], passenger["name"], passenger["passenger_type"], passenger.get("gender", "N/A"), selected_camera)
                    if res:
                        if res.get("event") == "ENTRY":
                            st.success(res["message"])
                            st.info(f"📍 {res.get('entry_location')}")
                            st.info(f"🕐 {res.get('entry_time')}")
                            st.info(f"👥 Occupancy: {res.get('current_occupancy')}")
                            st.balloons()
                        else:
                            st.warning(res.get("message"))
            else:
                st.warning("No registered persons")
        
        else:  # Upload Face for Recognition
            st.info("📸 Upload face - System will auto-match with database")
            uploaded_entry = st.file_uploader("Upload face for ENTRY", type=["jpg", "jpeg", "png"], key="entry_upload")
            
            if uploaded_entry:
                st.image(uploaded_entry, caption="Uploaded Face", width=150)
                
                if st.button("🔍 VERIFY & RECORD ENTRY", type="primary", use_container_width=True):
                    with st.spinner("Matching face with database..."):
                        match_result = match_face(uploaded_entry.getvalue())
                        
                        if match_result.get("matched"):
                            # Registered person found
                            st.success(f"✅ FACE MATCHED: {match_result['name']} (Confidence: {match_result.get('confidence', 0)}%)")
                            
                            # Record entry
                            res = record_entry(
                                match_result["passenger_id"],
                                match_result["name"],
                                match_result.get("passenger_type", "Regular"),
                                match_result.get("gender", "N/A"),
                                selected_camera
                            )
                            if res and res.get("event") == "ENTRY":
                                st.success(res["message"])
                                st.info(f"📍 {res.get('entry_location')}")
                                st.info(f"📍 GPS: {res.get('entry_gps')}")
                                st.info(f"🕐 {res.get('entry_time')}")
                                st.balloons()
                            else:
                                st.error("Failed to record entry")
                        else:
                            # Unknown person - Trigger alert
                            st.error(f"🚨 {match_result.get('reason', 'UNKNOWN PERSON DETECTED')}")
                            
                            # Record unknown entry with alert
                            alert_result = record_unknown_entry(selected_camera)
                            if alert_result:
                                st.error(alert_result["message"])
                                st.info(f"📍 Location: {alert_result.get('location')}")
                                st.info(f"📍 GPS: {alert_result.get('gps')}")
                                st.info(f"🕐 Time: {alert_result.get('timestamp')}")
                                st.warning("⚠️ Alert recorded in Alerts tab")
    
    # ============ EXIT SCAN ============
    with col2:
        st.subheader("🚪 EXIT SCAN")
        method = st.radio("Choose Exit Method", ["Select from List", "Upload Face for Recognition"], key="exit_method", horizontal=True)
        
        if method == "Select from List":
            if persons:
                opts = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
                selected = st.selectbox("Select Person", list(opts.keys()), key="exit_select")
                passenger = opts[selected]
                if st.button("✅ RECORD EXIT", type="primary", use_container_width=True):
                    res = record_exit(passenger["passenger_id"], passenger["name"], selected_camera)
                    if res:
                        if res.get("event") == "EXIT":
                            st.success(res["message"])
                            st.info(f"⏱️ Duration: {res.get('duration')}")
                            st.info(f"👥 Remaining: {res.get('current_occupancy')}")
                        else:
                            st.warning(res.get("message"))
            else:
                st.warning("No registered persons")
        
        else:  # Upload Face for Exit
            st.info("📸 Upload face to record exit")
            uploaded_exit = st.file_uploader("Upload face for EXIT", type=["jpg", "jpeg", "png"], key="exit_upload")
            
            if uploaded_exit:
                st.image(uploaded_exit, caption="Uploaded Face", width=150)
                
                if st.button("🔍 VERIFY & RECORD EXIT", type="primary", use_container_width=True):
                    with st.spinner("Matching face..."):
                        match_result = match_face(uploaded_exit.getvalue())
                        
                        if match_result.get("matched"):
                            res = record_exit(match_result["passenger_id"], match_result["name"], selected_camera)
                            if res and res.get("event") == "EXIT":
                                st.success(res["message"])
                                st.info(f"⏱️ Duration: {res.get('duration')}")
                                st.info(f"👥 Remaining: {res.get('current_occupancy')}")
                            else:
                                st.warning(res.get("message", "Person not inside"))
                        else:
                            st.warning("Face not recognized - Please use list selection for exit")

# ============ TAB 3: CURRENT OCCUPANCY ============
with tabs[2]:
    st.header("👥 Persons Currently Inside")
    try:
        s = requests.get(f"{API_URL}/vehicle_status").json()
        active = s.get("active_passengers", [])
        if active:
            df = pd.DataFrame(active)
            st.dataframe(df, use_container_width=True)
            st.metric("Total Inside", len(active))
        else:
            st.info("No persons currently inside")
    except:
        st.error("Error fetching data")

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
                st.metric("Total Journeys", len(journeys))
            else:
                st.info("No completed journeys yet")
    except:
        pass

# ============ TAB 5: ALERTS & LOGS ============
with tabs[4]:
    st.header("🚨 Security Alerts")
    try:
        r = requests.get(f"{API_URL}/active_alerts")
        if r.status_code == 200:
            alerts = r.json().get("alerts", [])
            if alerts:
                for alert in alerts:
                    st.error(f"""
                    **🚨 {alert.get('type', 'ALERT')}** - Severity: {alert.get('severity', 'HIGH')}
                    
                    **Message:** {alert.get('message')}
                    
                    **Location:** {alert.get('location')}
                    
                    **GPS:** {alert.get('gps')}
                    
                    **Camera:** {alert.get('camera')}
                    
                    **Time:** {alert.get('timestamp')}
                    """)
                    st.markdown("---")
            else:
                st.success("✅ No active alerts")
    except:
        pass

st.markdown("---")
st.caption("🎯 AI-Powered Transit Intelligence System | Face Recognition Enabled | Camera Capture Available")
