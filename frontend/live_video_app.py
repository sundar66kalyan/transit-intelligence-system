import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import cv2
import numpy as np
import tempfile
import time
from PIL import Image
import io

st.set_page_config(
    page_title="AI Vehicle Surveillance",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8001"

st.title("🚌 AI-Powered Vehicle Surveillance System")
st.markdown("*Live Video | Automatic Entry/Exit Detection | AI Agents*")

# Initialize session state
if "camera_active" not in st.session_state:
    st.session_state.camera_active = False
if "auto_detection" not in st.session_state:
    st.session_state.auto_detection = False

# Sidebar
with st.sidebar:
    st.header("📊 Live Status")
    
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=2).json()
        st.metric("👥 Current Occupancy", status.get("current_occupancy", 0))
        st.metric("🚨 Active Alerts", status.get("active_alerts", 0))
        st.metric("📋 Registered", status.get("total_registered", 0))
    except:
        st.error("⚠️ Connecting...")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh"):
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎥 LIVE VIDEO",
    "📝 REGISTER",
    "🤖 AUTO SCAN",
    "👥 OCCUPANCY",
    "📊 JOURNEYS",
    "🚨 ALERTS"
])

# ============ TAB 1: LIVE VIDEO ============
with tab1:
    st.header("🎥 Live Video Surveillance")
    st.info("""
    **Automatic Detection Active:**
    - Camera automatically detects people entering/exiting
    - AI Agent recognizes faces in real-time
    - Registered persons → Auto-mark attendance
    - Unknown persons → Auto-trigger alerts
    - GPS location recorded for every event
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Video Feed")
        
        # Option 1: Upload video for processing
        uploaded_video = st.file_uploader("Upload Video for Auto-Detection", type=["mp4", "avi", "mov", "mkv"])
        
        if uploaded_video:
            # Save video
            video_path = f"D:/VehicleSurveillanceSystem/uploads/live_video.mp4"
            with open(video_path, "wb") as f:
                f.write(uploaded_video.getbuffer())
            
            st.video(video_path)
            
            if st.button("🔍 START AUTO DETECTION", type="primary"):
                st.session_state.auto_detection = True
                
                # Process video frame by frame
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                detection_log = st.empty()
                
                frame_count = 0
                detections = []
                
                while cap.isOpened() and st.session_state.auto_detection:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frame_count += 1
                    progress_bar.progress(frame_count / total_frames)
                    
                    # Process every 15th frame
                    if frame_count % 15 == 0:
                        _, buffer = cv2.imencode(".jpg", frame)
                        
                        # Send to backend for auto-detection
                        files = {"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")}
                        response = requests.post(f"{API_URL}/process_video_frame", files=files, data={"bus_id": "BUS-001"})
                        
                        if response.status_code == 200:
                            result = response.json()
                            event = result.get("event")
                            
                            if event == "ENTRY":
                                passenger = result.get("passenger", {})
                                detections.append(f"✅ ENTRY: {passenger.get('name')} at {result.get('location', {}).get('address')}")
                                status_text.success(f"✅ {passenger.get('name')} ENTERED!")
                            elif event == "EXIT":
                                passenger = result.get("passenger", {})
                                detections.append(f"🚪 EXIT: {passenger.get('name')}")
                                status_text.info(f"🚪 {passenger.get('name')} EXITED")
                            elif event == "UNKNOWN":
                                detections.append(f"⚠️ UNKNOWN PERSON at {result.get('location', {}).get('address')}")
                                status_text.warning("⚠️ Unknown person detected!")
                    
                    # Display recent detections
                    with detection_log.container():
                        st.caption("Recent Detections:")
                        for det in detections[-10:]:
                            st.text(det)
                    
                    time.sleep(1/fps)
                
                cap.release()
                st.success("✅ Video processing complete!")
                st.session_state.auto_detection = False
        
        # Option 2: Webcam live feed
        st.markdown("---")
        st.subheader("📸 Webcam Live Feed")
        
        if st.button("🎥 START WEBCAM", use_container_width=True):
            st.session_state.camera_active = True
            
            cap = cv2.VideoCapture(0)
            frame_placeholder = st.empty()
            detection_status = st.empty()
            
            frame_skip = 0
            while st.session_state.camera_active:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_skip += 1
                if frame_skip % 10 == 0:  # Process every 10th frame
                    _, buffer = cv2.imencode(".jpg", frame)
                    files = {"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")}
                    
                    try:
                        response = requests.post(f"{API_URL}/auto_detect", files=files, data={"bus_id": "BUS-001"}, timeout=1)
                        if response.status_code == 200:
                            result = response.json()
                            event = result.get("event")
                            
                            if event == "ENTRY":
                                detection_status.success(f"✅ {result.get('passenger', {}).get('name')} ENTERED - Attendance Marked")
                            elif event == "EXIT":
                                detection_status.info(f"🚪 {result.get('passenger', {}).get('name')} EXITED")
                            elif event == "UNAUTHORIZED":
                                detection_status.error("🚨 UNKNOWN PERSON DETECTED!")
                    except:
                        pass
                
                # Convert to RGB for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                
                time.sleep(0.033)  # ~30 fps
            
            cap.release()
            
            if st.button("⏹️ STOP WEBCAM"):
                st.session_state.camera_active = False
                st.rerun()
    
    with col2:
        st.subheader("📋 Live Detection Log")
        try:
            events = requests.get(f"{API_URL}/recent_events").json().get("events", [])
            for event in events[-10:]:
                if event.get("event_type") == "ENTRY":
                    st.success(f"🚪 {event.get('passenger_name')} ENTERED")
                    st.caption(f"📍 {event.get('location')}")
                elif event.get("event_type") == "EXIT":
                    st.info(f"🚪 {event.get('passenger_name')} EXITED")
                    st.caption(f"⏱️ Duration: {event.get('journey_duration', 'N/A')}")
        except:
            pass

# ============ TAB 2: REGISTER PERSON ============
with tab2:
    st.header("📝 Register New Passenger")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter passenger name")
        passenger_id = st.text_input("Passenger ID *", placeholder="Unique ID")
        passenger_type = st.selectbox("Passenger Type", ["Student", "Regular", "Staff", "VIP"])
        
    with col2:
        uploaded_face = st.file_uploader("Upload Face Image *", type=["jpg", "jpeg", "png"])
        if uploaded_face:
            image = Image.open(uploaded_face)
            st.image(image, caption="Face for Recognition", width=200)
    
    if st.button("✅ REGISTER", type="primary", use_container_width=True):
        if name and passenger_id and uploaded_face:
            files = {"file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")}
            data = {"name": name, "passenger_id": passenger_id, "passenger_type": passenger_type}
            
            response = requests.post(f"{API_URL}/register_passenger", files=files, data=data)
            if response.status_code == 200:
                st.success(f"✅ {name} registered!")
                st.balloons()
    
    # Show registered passengers
    st.markdown("---")
    st.subheader("Registered Passengers")
    try:
        resp = requests.get(f"{API_URL}/registered_passengers").json()
        passengers = resp.get("passengers", [])
        if passengers:
            df = pd.DataFrame(passengers)
            st.dataframe(df, use_container_width=True)
    except:
        pass

# ============ TAB 3: AUTO SCAN TEST ============
with tab3:
    st.header("🤖 Automatic Entry/Exit Scanner")
    st.info("Upload a face image - System will automatically detect if it's ENTRY or EXIT")
    
    test_image = st.file_uploader("Upload face for auto-detection", type=["jpg", "jpeg", "png"])
    
    if test_image:
        st.image(test_image, width=200)
        
        if st.button("🤖 AUTO DETECT", type="primary"):
            files = {"file": ("face.jpg", test_image.getvalue(), "image/jpeg")}
            response = requests.post(f"{API_URL}/auto_detect", files=files, data={"bus_id": "BUS-001"})
            
            if response.status_code == 200:
                result = response.json()
                event = result.get("event")
                
                if event == "ENTRY":
                    st.success(f"✅ ENTRY DETECTED")
                    st.markdown(f"""
                    - **Passenger:** {result.get('passenger', {}).get('name')}
                    - **Location:** {result.get('location', {}).get('address')}
                    - **GPS:** {result.get('location', {}).get('lat')}, {result.get('location', {}).get('lon')}
                    - **Current Occupancy:** {result.get('current_occupancy', 0)}
                    """)
                elif event == "EXIT":
                    st.info(f"🚪 EXIT DETECTED")
                    st.markdown(f"""
                    - **Passenger:** {result.get('passenger', {}).get('name')}
                    - **Exit Location:** {result.get('exit_location', {}).get('address')}
                    - **Journey Duration:** {result.get('journey_duration', 'N/A')}
                    - **Remaining Occupancy:** {result.get('current_occupancy', 0)}
                    """)
                elif event == "UNAUTHORIZED":
                    st.error("🚨 UNAUTHORIZED PERSON DETECTED!")
                    st.markdown(f"""
                    - **Location:** {result.get('location', {}).get('address')}
                    - **GPS:** {result.get('location', {}).get('lat')}, {result.get('location', {}).get('lon')}
                    """)

# ============ TAB 4: CURRENT OCCUPANCY ============
with tab4:
    st.header("👥 Passengers Currently in Vehicle")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_passengers").json()
        passengers = response.get("passengers", [])
        
        st.metric("Total Onboard", response.get("count", 0))
        
        for passenger in passengers:
            with st.expander(f"🚌 {passenger.get('passenger_name')}"):
                st.write(f"**Entry Time:** {passenger.get('entry_time', 'N/A')[:19]}")
                st.write(f"**Entry Location:** {passenger.get('entry_location', {}).get('address')}")
                st.write(f"**GPS:** {passenger.get('entry_gps', {}).get('lat')}, {passenger.get('entry_gps', {}).get('lon')}")
    except:
        pass

# ============ TAB 5: JOURNEY HISTORY ============
with tab5:
    st.header("📊 Completed Journeys")
    
    try:
        response = requests.get(f"{API_URL}/journey_history").json()
        journeys = response.get("journeys", [])
        
        if journeys:
            df = pd.DataFrame(journeys)
            display_cols = ["passenger_name", "passenger_type", "entry_location", "exit_location", "journey_duration"]
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("No completed journeys yet")
    except:
        pass

# ============ TAB 6: ALERTS ============
with tab6:
    st.header("🚨 Security Alerts")
    
    try:
        response = requests.get(f"{API_URL}/active_alerts").json()
        alerts = response.get("alerts", [])
        
        if alerts:
            for alert in alerts:
                st.error(f"""
                **🚨 {alert.get('type')}** - Severity: {alert.get('severity')}
                
                {alert.get('message')}
                
                **Location:** {alert.get('location')}
                **GPS:** {alert.get('gps', {}).get('lat')}, {alert.get('gps', {}).get('lon')}
                **Time:** {alert.get('timestamp', 'N/A')[:19]}
                """)
        else:
            st.success("✅ No active alerts")
    except:
        pass

st.markdown("---")
st.caption("🚌 AI Vehicle Surveillance | Automatic Entry/Exit Detection | Real-time Tracking")
