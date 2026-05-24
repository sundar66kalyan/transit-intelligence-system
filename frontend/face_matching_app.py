# frontend/face_matching_app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="AI Transit System", page_icon="🎯", layout="wide")

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

def fetch_registered_persons():
    try:
        r = requests.get(f"{API_URL}/registered_passengers", timeout=2)
        if r.status_code == 200:
            st.session_state.registered_persons = r.json().get("passengers", [])
    except:
        pass

def register_person(name, pid, ptype, gender, phone, email, url, img):
    files = {"file": ("face.jpg", img, "image/jpeg")}
    data = {"name": name, "passenger_id": pid, "passenger_type": ptype, "gender": gender, "phone": phone, "email": email, "live_url": url}
    r = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
    if r.status_code == 200:
        return True, r.json().get("message")
    return False, "Failed"

def record_entry(pid, name, ptype, gender, cam):
    data = {"passenger_id": pid, "passenger_name": name, "passenger_type": ptype, "gender": gender, "camera_id": cam}
    r = requests.post(f"{API_URL}/record_entry", data=data)
    if r.status_code == 200:
        return r.json()
    return None

def record_exit(pid, name, cam):
    data = {"passenger_id": pid, "passenger_name": name, "camera_id": cam}
    r = requests.post(f"{API_URL}/record_exit", data=data)
    if r.status_code == 200:
        return r.json()
    return None

def match_face(img_bytes):
    files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
    r = requests.post(f"{API_URL}/match_face", files=files)
    if r.status_code == 200:
        return r.json()
    return {"matched": False, "reason": "Error"}

def record_unknown(cam):
    data = {"camera_id": cam}
    r = requests.post(f"{API_URL}/record_unknown", data=data)
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
        st.metric("Current Occupancy", s.get("current_occupancy", 0))
        st.metric("Registered", s.get("total_registered", 0))
        st.metric("Completed", s.get("completed_journeys_count", 0))
    except:
        st.error("Backend not connected")
    st.markdown("---")
    if st.button("Refresh"):
        fetch_registered_persons()
        st.rerun()

tabs = st.tabs(["📝 REGISTER", "📸 SCAN", "👥 OCCUPANCY", "📊 HISTORY", "🚨 ALERTS"])

# TAB 1: REGISTER
with tabs[0]:
    st.header("Register New Person")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Full Name")
        pid = st.text_input("ID")
        gender = st.selectbox("Gender", ["Male", "Female"])
        ptype = st.selectbox("Type", ["Student", "Regular", "Staff", "VIP"])
    with c2:
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        url = st.text_input("Live URL")
        img = st.file_uploader("Face Image", type=["jpg", "png", "jpeg"])
        if img:
            st.image(img, width=150)
    if st.button("REGISTER", type="primary"):
        if name and pid and img:
            ok, msg = register_person(name, pid, ptype, gender, phone, email, url, img.getvalue())
            if ok:
                st.success(msg)
                st.balloons()
                fetch_registered_persons()
            else:
                st.error(msg)
        else:
            st.warning("Fill all required fields")

# TAB 2: SCAN
with tabs[1]:
    st.header(f"Camera: {selected_camera}")
    persons = fetch_registered_persons()
    
    col1, col2 = st.columns(2)
    
    # ENTRY
    with col1:
        st.subheader("🚪 ENTRY")
        method = st.radio("Method", ["Select from List", "Upload Face"], key="entry_method")
        
        if method == "Select from List":
            if persons:
                opts = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
                sel = st.selectbox("Person", list(opts.keys()), key="entry_sel")
                p = opts[sel]
                if st.button("RECORD ENTRY", type="primary"):
                    res = record_entry(p["passenger_id"], p["name"], p["passenger_type"], p.get("gender", "N/A"), selected_camera)
                    if res:
                        if res.get("event") == "ENTRY":
                            st.success(res["message"])
                            st.info(f"📍 {res.get('entry_location')}")
                            st.info(f"🕐 {res.get('entry_time')}")
                            st.balloons()
                        else:
                            st.warning(res.get("message"))
        else:
            uploaded = st.file_uploader("Upload Face for ENTRY", type=["jpg", "png", "jpeg"], key="entry_upload")
            if uploaded:
                st.image(uploaded, width=150)
                if st.button("VERIFY & ENTER", type="primary"):
                    with st.spinner("Matching face..."):
                        result = match_face(uploaded.getvalue())
                        if result.get("matched"):
                            st.success(f"✅ REGISTERED: {result['name']}")
                            res = record_entry(result["passenger_id"], result["name"], result.get("passenger_type", "Regular"), result.get("gender", "N/A"), selected_camera)
                            if res and res.get("event") == "ENTRY":
                                st.success(res["message"])
                                st.info(f"📍 {res.get('entry_location')}")
                                st.balloons()
                        else:
                            st.error(f"🚨 {result.get('reason', 'UNKNOWN PERSON')}")
                            alert = record_unknown(selected_camera)
                            if alert:
                                st.error(alert["message"])
                                st.info(f"📍 {alert.get('location')}")
                                st.info(f"📍 GPS: {alert.get('gps')}")
    
    # EXIT
    with col2:
        st.subheader("🚪 EXIT")
        method = st.radio("Method", ["Select from List", "Upload Face"], key="exit_method")
        
        if method == "Select from List":
            if persons:
                opts = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
                sel = st.selectbox("Person", list(opts.keys()), key="exit_sel")
                p = opts[sel]
                if st.button("RECORD EXIT", type="primary"):
                    res = record_exit(p["passenger_id"], p["name"], selected_camera)
                    if res:
                        if res.get("event") == "EXIT":
                            st.success(res["message"])
                            st.info(f"⏱️ Duration: {res.get('duration')}")
                        else:
                            st.warning(res.get("message"))
        else:
            uploaded = st.file_uploader("Upload Face for EXIT", type=["jpg", "png", "jpeg"], key="exit_upload")
            if uploaded:
                st.image(uploaded, width=150)
                if st.button("VERIFY & EXIT", type="primary"):
                    with st.spinner("Matching face..."):
                        result = match_face(uploaded.getvalue())
                        if result.get("matched"):
                            res = record_exit(result["passenger_id"], result["name"], selected_camera)
                            if res and res.get("event") == "EXIT":
                                st.success(res["message"])
                                st.info(f"⏱️ Duration: {res.get('duration')}")
                        else:
                            st.warning("Face not recognized - Please use list selection")

# TAB 3: OCCUPANCY
with tabs[2]:
    st.header("Current Occupancy")
    try:
        s = requests.get(f"{API_URL}/vehicle_status").json()
        active = s.get("active_passengers", [])
        if active:
            df = pd.DataFrame(active)
            st.dataframe(df)
        else:
            st.info("No one inside")
    except:
        st.error("Error fetching data")

# TAB 4: HISTORY
with tabs[3]:
    st.header("Journey History")
    try:
        r = requests.get(f"{API_URL}/completed_journeys")
        if r.status_code == 200:
            journeys = r.json().get("journeys", [])
            if journeys:
                df = pd.DataFrame(journeys)
                st.dataframe(df)
            else:
                st.info("No journeys yet")
    except:
        pass

# TAB 5: ALERTS
with tabs[4]:
    st.header("Security Alerts")
    try:
        r = requests.get(f"{API_URL}/active_alerts")
        if r.status_code == 200:
            alerts = r.json().get("alerts", [])
            if alerts:
                for a in alerts:
                    st.error(f"🚨 {a['message']}\n📍 {a['location']}\n📍 GPS: {a['gps']}\n🕐 {a['timestamp']}")
            else:
                st.success("No alerts")
    except:
        pass

st.caption("AI Transit System | Face Recognition Enabled")
