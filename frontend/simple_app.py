import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="AI Transit System", page_icon="🤖", layout="wide")

API_URL = "http://localhost:8001"

# Camera locations
camera_locations = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def convert_image_to_rgb_bytes(uploaded_file):
    """Convert uploaded image to RGB JPEG bytes"""
    try:
        image = Image.open(uploaded_file)
        
        # Convert to RGB
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=90)
        return img_bytes.getvalue()
    except Exception as e:
        st.error(f"Image conversion error: {e}")
        return None

def register_passenger(name, pid, ptype, gender, phone, email, url, img_bytes):
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
        response = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def auto_detect(img_bytes, camera_id):
    try:
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {"camera_id": camera_id}
        response = requests.post(f"{API_URL}/auto_detect_face", files=files, data=data)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def record_exit(pid, name, cam):
    try:
        data = {"passenger_id": pid, "passenger_name": name, "camera_id": cam}
        response = requests.post(f"{API_URL}/record_exit", data=data)
        if response.status_code == 200:
            return response.json()
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
        st.metric("Current Occupancy", s.get("current_occupancy", 0))
        st.metric("Registered", s.get("total_registered", 0))
        st.metric("Completed", s.get("completed_journeys_count", 0))
        st.metric("Alerts", s.get("active_alerts", 0))
    except:
        st.error("Backend not connected")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

tabs = st.tabs(["📝 REGISTER", "🤖 AI SCAN", "👥 OCCUPANCY", "📊 HISTORY", "🚨 ALERTS"])

# ============ TAB 1: REGISTER ============
with tabs[0]:
    st.header("Register New Person")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name", placeholder="Enter name")
        pid = st.text_input("Person ID", placeholder="Enter ID")
        gender = st.selectbox("Gender", ["Male", "Female"])
        ptype = st.selectbox("Type", ["Student", "Regular", "Staff", "VIP"])
        phone = st.text_input("Phone", placeholder="Phone number")
        email = st.text_input("Email", placeholder="Email")
        live_url = st.text_input("Live URL", placeholder="https://...")
    
    with col2:
        st.subheader("Upload Face Image")
        uploaded = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])
        
        if uploaded:
            st.image(uploaded, caption="Preview", width=200)
            
            if st.button("✅ REGISTER", type="primary", use_container_width=True):
                if name and pid:
                    img_bytes = convert_image_to_rgb_bytes(uploaded)
                    if img_bytes:
                        result = register_passenger(name, pid, ptype, gender, phone, email, live_url, img_bytes)
                        if result.get("status") == "success":
                            st.success(result.get("message"))
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(result.get("message", "Registration failed"))
                else:
                    st.warning("Please enter Name and ID")
    
    st.markdown("---")
    st.subheader("Registered Persons")
    try:
        r = requests.get(f"{API_URL}/registered_passengers")
        if r.status_code == 200:
            persons = r.json().get("passengers", [])
            if persons:
                df = pd.DataFrame(persons)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No registered persons")
    except:
        pass

# ============ TAB 2: AI SCAN ============
with tabs[1]:
    st.header(f"AI Auto Scan - {selected_camera}")
    
    uploaded = st.file_uploader("Upload face for detection", type=["jpg", "jpeg", "png"])
    
    if uploaded:
        st.image(uploaded, caption="Uploaded Face", width=200)
        
        if st.button("🤖 RUN AI DETECTION", type="primary", use_container_width=True):
            img_bytes = convert_image_to_rgb_bytes(uploaded)
            if img_bytes:
                result = auto_detect(img_bytes, selected_camera)
                if result:
                    if result.get("event") == "REGISTERED_ENTRY":
                        st.success(f"✅ {result.get('message')}")
                        st.info(f"📍 Location: {result.get('location')}")
                        st.info(f"📍 GPS: {result.get('gps')}")
                        st.info(f"🕐 Time: {result.get('entry_time')}")
                        st.balloons()
                    elif result.get("event") == "UNREGISTERED_ENTRY":
                        st.error(f"🚨 {result.get('message')}")
                        st.info(f"📍 Location: {result.get('location')}")
                        st.info(f"📍 GPS: {result.get('gps')}")
                else:
                    st.error("Detection failed")
    
    st.markdown("---")
    st.subheader("Manual Exit")
    try:
        r = requests.get(f"{API_URL}/registered_passengers")
        if r.status_code == 200:
            persons = r.json().get("passengers", [])
            if persons:
                opts = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
                selected = st.selectbox("Select Person to Exit", list(opts.keys()))
                passenger = opts[selected]
                
                if st.button("✅ RECORD EXIT", type="primary", use_container_width=True):
                    res = record_exit(passenger["passenger_id"], passenger["name"], selected_camera)
                    if res and res.get("event") == "EXIT":
                        st.success(res["message"])
                        st.info(f"Duration: {res.get('duration')}")
    except:
        pass

# ============ TAB 3: OCCUPANCY ============
with tabs[2]:
    st.header("Current Occupancy")
    try:
        s = requests.get(f"{API_URL}/vehicle_status").json()
        active = s.get("active_passengers", [])
        if active:
            df = pd.DataFrame(active)
            st.dataframe(df, use_container_width=True)
            st.metric("Total Inside", len(active))
        else:
            st.info("No one inside")
    except:
        pass

# ============ TAB 4: HISTORY ============
with tabs[3]:
    st.header("Journey History")
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
    st.header("Security Alerts")
    try:
        r = requests.get(f"{API_URL}/active_alerts")
        if r.status_code == 200:
            alerts = r.json().get("alerts", [])
            if alerts:
                for alert in alerts:
                    st.error(f"🚨 {alert['message']}\n📍 {alert['location']}\n📍 GPS: {alert['gps']}")
            else:
                st.success("No alerts")
    except:
        pass

st.markdown("---")
st.caption("AI Transit System | Working Version")
