# frontend/complete_app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import io

st.set_page_config(
    page_title="AI Transit Intelligence System",
    page_icon="🎯",
    layout="wide"
)

API_URL = "http://localhost:8001"

# Initialize session state
if "registered_persons" not in st.session_state:
    st.session_state.registered_persons = []
if "entry_method" not in st.session_state:
    st.session_state.entry_method = "Select from List"
if "exit_method" not in st.session_state:
    st.session_state.exit_method = "Select from List"

# Camera locations
camera_locations = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def fetch_registered_persons():
    try:
        response = requests.get(f"{API_URL}/registered_passengers", timeout=3)
        if response.status_code == 200:
            data = response.json()
            st.session_state.registered_persons = data.get("passengers", [])
            return st.session_state.registered_persons
    except:
        pass
    return []

def register_person(name, person_id, person_type, gender, phone, email, live_url, image_file):
    try:
        files = {"file": ("face.jpg", image_file, "image/jpeg")}
        data = {
            "name": name,
            "passenger_id": person_id,
            "passenger_type": person_type,
            "gender": gender,
            "phone": phone,
            "email": email,
            "live_url": live_url
        }
        response = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                fetch_registered_persons()
                return True, result.get("message")
        return False, "Registration failed"
    except:
        return False, "Connection error"

def record_entry(passenger_id, passenger_name, passenger_type, gender, camera_id):
    try:
        data = {
            "passenger_id": passenger_id,
            "passenger_name": passenger_name,
            "passenger_type": passenger_type,
            "gender": gender,
            "camera_id": camera_id
        }
        response = requests.post(f"{API_URL}/record_entry", data=data)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def record_exit(passenger_id, passenger_name, camera_id):
    try:
        data = {
            "passenger_id": passenger_id,
            "passenger_name": passenger_name,
            "camera_id": camera_id
        }
        response = requests.post(f"{API_URL}/record_exit", data=data)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

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
        st.metric("✅ Completed", status.get("completed_journeys_count", 0))
    except:
        st.error("❌ Backend not connected!")
        st.info("Start backend: python backend/simple_working_backend.py")
    
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
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        person_type = st.selectbox("Person Type", ["Student", "Regular", "Staff", "VIP"])
        
    with col2:
        phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
        email = st.text_input("Email", placeholder="person@example.com")
        live_url = st.text_input("Live URL", placeholder="https://linkedin.com/in/username")
        
        uploaded_face = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png"])
        if uploaded_face:
            image = Image.open(uploaded_face)
            st.image(image, caption="Face Preview", width=200)
    
    if st.button("✅ REGISTER", type="primary", use_container_width=True):
        if name and person_id and uploaded_face:
            success, msg = register_person(name, person_id, person_type, gender, phone, email, live_url, uploaded_face.getvalue())
            if success:
                st.success(f"✅ {name} registered!")
                st.balloons()
                st.rerun()
            else:
                st.error(msg)
        else:
            st.warning("Please fill name, ID and upload face image")
    
    st.markdown("---")
    st.subheader("📋 Registered Persons")
    persons = fetch_registered_persons()
    if persons:
        df = pd.DataFrame(persons)
        display_cols = ["passenger_id", "name", "gender", "passenger_type"]
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)

# ============ TAB 2: CAMERA SCAN ============
with tab2:
    st.header(f"📸 Camera Scan: {selected_camera}")
    
    persons = fetch_registered_persons()
    
    col1, col2 = st.columns(2)
    
    # ============ ENTRY SCAN ============
    with col1:
        st.subheader("🚪 ENTRY SCAN")
        
        # Radio button to choose method (exclusive)
        entry_method = st.radio(
            "Choose Entry Method",
            ["Select from Registered List", "Upload Face Image"],
            key="entry_method_radio",
            horizontal=True
        )
        
        if entry_method == "Select from Registered List":
            if persons:
                person_options = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
                selected = st.selectbox("Select Person", list(person_options.keys()), key="entry_select")
                passenger = person_options[selected]
                
                if st.button("✅ RECORD ENTRY", type="primary", use_container_width=True, key="entry_btn"):
                    with st.spinner("Recording entry..."):
                        result = record_entry(
                            passenger["passenger_id"],
                            passenger["name"],
                            passenger["passenger_type"],
                            passenger.get("gender", "Not specified"),
                            selected_camera
                        )
                        if result:
                            if result.get("event") == "ENTRY":
                                st.success(result.get("message"))
                                st.info(f"📍 {result.get('entry_location', 'N/A')}")
                                st.info(f"🕐 {result.get('entry_time', 'N/A')}")
                                st.info(f"👥 Occupancy: {result.get('current_occupancy', 0)}")
                                st.balloons()
                            elif result.get("event") == "ALREADY_INSIDE":
                                st.warning(result.get("message"))
                            else:
                                st.error("Failed to record entry")
                        else:
                            st.error("Backend error - Check if backend is running")
            else:
                st.warning("No registered persons. Please register first.")
        
        else:  # Upload Face Image method
            st.info("📸 Upload face image for recognition")
            uploaded_entry = st.file_uploader("Upload face for ENTRY", type=["jpg", "jpeg", "png"], key="entry_upload")
            
            if uploaded_entry:
                st.image(uploaded_entry, caption="Uploaded Face", width=150)
                st.warning("⚠️ Face matching will be available in full version")
                
                # Option to record as unknown
                if st.button("🚨 RECORD AS UNKNOWN", use_container_width=True, key="unknown_entry"):
                    st.error("🚨 Unknown person alert triggered!")
                    st.info(f"📍 Location: {selected_camera}")
    
    # ============ EXIT SCAN ============
    with col2:
        st.subheader("🚪 EXIT SCAN")
        
        # Radio button to choose method (exclusive)
        exit_method = st.radio(
            "Choose Exit Method",
            ["Select from Registered List", "Upload Face Image"],
            key="exit_method_radio",
            horizontal=True
        )
        
        if exit_method == "Select from Registered List":
            if persons:
                person_options = {f"{p['name']} ({p['passenger_id']})": p for p in persons}
                selected_exit = st.selectbox("Select Person for Exit", list(person_options.keys()), key="exit_select")
                exit_passenger = person_options[selected_exit]
                
                if st.button("✅ RECORD EXIT", type="primary", use_container_width=True, key="exit_btn"):
                    with st.spinner("Recording exit..."):
                        result = record_exit(
                            exit_passenger["passenger_id"],
                            exit_passenger["name"],
                            selected_camera
                        )
                        if result:
                            if result.get("event") == "EXIT":
                                st.success(result.get("message"))
                                st.info(f"⏱️ Duration: {result.get('duration', 'N/A')}")
                                st.info(f"👥 Remaining: {result.get('current_occupancy', 0)}")
                            elif result.get("event") == "NOT_INSIDE":
                                st.warning(result.get("message"))
                            else:
                                st.error("Failed to record exit")
                        else:
                            st.error("Backend error - Check if backend is running")
            else:
                st.warning("No registered persons")
        
        else:  # Upload Face Image method
            st.info("📸 Upload face image for recognition")
            uploaded_exit = st.file_uploader("Upload face for EXIT", type=["jpg", "jpeg", "png"], key="exit_upload")
            
            if uploaded_exit:
                st.image(uploaded_exit, caption="Uploaded Face", width=150)
                st.warning("⚠️ Face matching will be available in full version")

# ============ TAB 3: CURRENT OCCUPANCY ============
with tab3:
    st.header("👥 Persons Currently Inside")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=2).json()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🚪 Total Inside", status.get("current_occupancy", 0))
        with col2:
            st.metric("👨 Males", status.get("male_count", 0))
        with col3:
            st.metric("👩 Females", status.get("female_count", 0))
        
        st.markdown("---")
        
        active_passengers = status.get("active_passengers", [])
        if active_passengers:
            df_data = []
            for p in active_passengers:
                df_data.append({
                    "Name": p.get("passenger_name"),
                    "ID": p.get("passenger_id"),
                    "Gender": p.get("gender", "N/A"),
                    "Entry Time": p.get("entry_time_only"),
                    "Entry Location": p.get("entry_location"),
                    "Status": "🟢 INSIDE"
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No persons currently inside")
    
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 4: JOURNEY HISTORY ============
with tab4:
    st.header("📊 Journey History")
    
    if st.button("🔄 Refresh History", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/completed_journeys")
        if response.status_code == 200:
            data = response.json()
            journeys = data.get("journeys", [])
            
            if journeys:
                st.metric("Total Journeys", data.get("count", 0))
                df = pd.DataFrame(journeys)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No completed journeys yet")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TAB 5: ALERTS & LOGS ============
with tab5:
    st.header("🚨 Alerts & Logs")
    st.success("✅ No active alerts")

st.markdown("---")
st.caption("🎯 AI-Powered Transit Intelligence System")
