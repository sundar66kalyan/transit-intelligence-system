import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import base64
import io

st.set_page_config(
    page_title="Face Recognition Entry System",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8001"

st.title("🚌 AI-Powered Vehicle Surveillance System")
st.markdown("*Face Recognition | Entry/Exit Tracking | GPS Alerts*")

# Initialize session state
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None

# Sidebar
with st.sidebar:
    st.header("📍 Vehicle Status")
    
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=2).json()
        st.metric("👥 Current Occupancy", status.get("current_occupancy", 0))
        st.metric("🚨 Active Alerts", status.get("active_alerts", 0))
    except:
        st.error("⚠️ Backend connecting...")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Status"):
        st.rerun()

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📸 Face Scan Entry", "🚪 Exit Scan", "📋 Demo Testing", 
    "🚨 Alerts", "📊 Reports"
])

with tab1:
    st.header("📸 Face Recognition - ENTRY")
    
    st.info("""
    **How it works:**
    1. Upload or capture a face image
    2. System matches against database
    3. **Registered** → ✅ Marked present, GPS recorded, occupancy +1
    4. **Unknown** → 🚨 Alert triggered with GPS location
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Upload Face Image")
        uploaded_image = st.file_uploader("Choose image for ENTRY", type=["jpg", "jpeg", "png"], key="entry_scan")
        
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Face to Scan", width=200)
            
            if st.button("🔍 SCAN FOR ENTRY", type="primary", use_container_width=True):
                with st.spinner("Scanning face..."):
                    files = {"file": ("face.jpg", uploaded_image.getvalue(), "image/jpeg")}
                    data = {"bus_id": "BUS-001"}
                    
                    response = requests.post(f"{API_URL}/scan_entry", files=files, data=data)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.scan_result = result
                        
                        if result.get("result") == "registered":
                            st.success("✅ REGISTERED PASSENGER DETECTED")
                            st.balloons()
                            
                            passenger = result.get("passenger", {})
                            st.markdown(f"""
                            **Passenger Details:**
                            - **Name:** {passenger.get('name', 'N/A')}
                            - **ID:** {passenger.get('passenger_id', 'N/A')}
                            - **Type:** {passenger.get('passenger_type', 'N/A')}
                            
                            **Entry Recorded:**
                            - **Location:** {result.get('location', {}).get('address', 'Unknown')}
                            - **GPS:** {result.get('gps', {}).get('lat', 'N/A')}, {result.get('gps', {}).get('lon', 'N/A')}
                            - **Time:** {result.get('timestamp', 'N/A')[:19]}
                            - **Current Occupancy:** {result.get('current_occupancy', 0)}
                            """)
                            
                            # Show map
                            gps = result.get("gps", {})
                            if gps:
                                map_data = pd.DataFrame([{"lat": gps.get("lat"), "lon": gps.get("lon")}])
                                st.map(map_data)
                            
                        elif result.get("result") == "unauthorized":
                            st.error("🚨 UNREGISTERED PERSON DETECTED!")
                            
                            st.markdown(f"""
                            **⚠️ SECURITY ALERT**
                            - **Message:** {result.get('message', 'Unauthorized entry')}
                            - **Location:** {result.get('location', {}).get('address', 'Unknown')}
                            - **GPS:** {result.get('gps', {}).get('lat', 'N/A')}, {result.get('gps', {}).get('lon', 'N/A')}
                            - **Time:** {result.get('timestamp', 'N/A')[:19]}
                            """)
                            
                            gps = result.get("gps", {})
                            if gps:
                                map_data = pd.DataFrame([{"lat": gps.get("lat"), "lon": gps.get("lon")}])
                                st.map(map_data)
                    else:
                        st.error("Scan failed. Make sure backend is running.")
    
    with col2:
        st.subheader("📷 Live Camera")
        st.caption("For best results, use a clear face image")
        st.info("💡 **Tip:** Use the Demo Testing tab to try with pre-registered faces!")

with tab2:
    st.header("🚪 Face Recognition - EXIT")
    
    st.info("Record passenger exit with GPS coordinates and journey duration")
    
    exit_image = st.file_uploader("Upload face image for EXIT", type=["jpg", "jpeg", "png"], key="exit_scan")
    
    if exit_image:
        st.image(exit_image, width=200)
        
        if st.button("🔍 SCAN FOR EXIT", type="primary", use_container_width=True):
            files = {"file": ("face.jpg", exit_image.getvalue(), "image/jpeg")}
            data = {"bus_id": "BUS-001"}
            
            response = requests.post(f"{API_URL}/scan_exit", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                
                if result.get("result") == "exited":
                    st.success("✅ EXIT RECORDED")
                    
                    st.markdown(f"""
                    **Passenger:** {result.get('passenger', {}).get('name', 'N/A')}
                    - **Entry Location:** {result.get('entry_location', {}).get('address', 'N/A')}
                    - **Exit Location:** {result.get('exit_location', {}).get('address', 'N/A')}
                    - **Journey Duration:** {result.get('journey_duration', 'N/A')}
                    - **Exit GPS:** {result.get('gps', {}).get('lat', 'N/A')}, {result.get('gps', {}).get('lon', 'N/A')}
                    - **Remaining Occupancy:** {result.get('current_occupancy', 0)}
                    """)
                else:
                    st.warning(result.get("message", "Passenger not found in vehicle"))

with tab3:
    st.header("📋 Demo Testing - Try with Pre-registered Faces")
    
    st.info("""
    **Demo Faces Available:**
    Click any demo passenger to test entry/exit with pre-registered faces
    """)
    
    try:
        response = requests.get(f"{API_URL}/demo_faces")
        if response.status_code == 200:
            demo_faces = response.json().get("demo_faces", [])
            
            if demo_faces:
                cols = st.columns(3)
                for idx, face in enumerate(demo_faces):
                    with cols[idx % 3]:
                        # Display demo face info
                        st.markdown(f"**{face['name']}**")
                        st.caption(f"ID: {face['passenger_id']} | Type: {face['type']}")
                        
                        # Load and display image
                        if os.path.exists(face["image_path"]):
                            image = Image.open(face["image_path"])
                            st.image(image, width=150)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"🚪 ENTER", key=f"enter_{face['passenger_id']}"):
                                # Read image file
                                with open(face["image_path"], "rb") as f:
                                    files = {"file": ("face.jpg", f.read(), "image/jpeg")}
                                    data = {"bus_id": "BUS-001"}
                                    
                                    resp = requests.post(f"{API_URL}/scan_entry", files=files, data=data)
                                    if resp.status_code == 200:
                                        result = resp.json()
                                        if result.get("result") == "registered":
                                            st.success(f"✅ {face['name']} entered!")
                                            st.info(f"📍 {result.get('location', {}).get('address')}")
                                        else:
                                            st.error("Scan failed")
                        
                        with col2:
                            if st.button(f"🚪 EXIT", key=f"exit_{face['passenger_id']}"):
                                with open(face["image_path"], "rb") as f:
                                    files = {"file": ("face.jpg", f.read(), "image/jpeg")}
                                    resp = requests.post(f"{API_URL}/scan_exit", files=files, data=data)
                                    if resp.status_code == 200:
                                        result = resp.json()
                                        if result.get("result") == "exited":
                                            st.success(f"✅ {face['name']} exited!")
                
                st.markdown("---")
                st.warning("**Unknown Face Test:** Upload any other image (not in demo) to test alert system")
                
                unknown_image = st.file_uploader("Upload unknown face for testing", type=["jpg", "jpeg", "png"], key="unknown_test")
                if unknown_image and st.button("Test Unknown Face"):
                    files = {"file": ("unknown.jpg", unknown_image.getvalue(), "image/jpeg")}
                    response = requests.post(f"{API_URL}/scan_entry", files=files, data={"bus_id": "BUS-001"})
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("result") == "unauthorized":
                            st.error("🚨 ALERT: Unknown person detected! Check Alerts tab.")
                            st.info(f"📍 Location: {result.get('location', {}).get('address')}")
            else:
                st.info("No demo faces found. Run demo_data.py first")
    except Exception as e:
        st.error(f"Error loading demo faces: {e}")

with tab4:
    st.header("🚨 Security Alerts")
    
    if st.button("🔄 Refresh Alerts"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_alerts")
        if response.status_code == 200:
            alerts = response.json().get("alerts", [])
            
            if alerts:
                for alert in alerts[::-1]:  # Show newest first
                    with st.container():
                        st.error(f"""
                        **🚨 {alert.get('type', 'ALERT')}**
                        - **Message:** {alert.get('message', 'N/A')}
                        - **Location:** {alert.get('location', {}).get('address', 'Unknown')}
                        - **Time:** {alert.get('timestamp', 'N/A')[:19]}
                        """)
                        st.markdown("---")
            else:
                st.success("✅ No active alerts")
    except Exception as e:
        st.error(f"Error: {e}")

with tab5:
    st.header("📊 Entry/Exit Reports")
    
    if st.button("🔄 Refresh Reports"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/recent_entries")
        if response.status_code == 200:
            entries = response.json().get("entries", [])
            
            if entries:
                df = pd.DataFrame(entries)
                st.dataframe(df, use_container_width=True)
                
                # Summary
                st.subheader("Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    entries_count = len([e for e in entries if e.get("type") == "ENTRY"])
                    st.metric("Total Entries", entries_count)
                with col2:
                    exits_count = len([e for e in entries if e.get("type") == "EXIT"])
                    st.metric("Total Exits", exits_count)
                with col3:
                    unauth = len([e for e in entries if e.get("type") == "UNAUTHORIZED"])
                    st.metric("Unauthorized Attempts", unauth)
            else:
                st.info("No entries recorded yet")
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")
st.caption("🚌 Face Recognition System | Real-time Entry/Exit with GPS | Automated Alerts")
