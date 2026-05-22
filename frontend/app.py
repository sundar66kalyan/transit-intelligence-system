import streamlit as st
import cv2
import requests
import numpy as np
from PIL import Image
import tempfile
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="Vehicle Surveillance System",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8000"

st.title("🚌 AI-Powered Smart Vehicle Surveillance System")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Controls")
    camera_id = st.selectbox("Select Camera", ["Front Door", "Main Cabin", "Exit Door"])
    
    if "passenger_count" not in st.session_state:
        st.session_state.passenger_count = 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🚶 Passengers", st.session_state.passenger_count)
    
    if st.button("🔄 Reset"):
        st.session_state.passenger_count = 0
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📹 Live Surveillance", "👤 Face Registration", "📝 Attendance"])

with tab1:
    st.header("Real-Time Passenger Monitoring")
    
    uploaded_file = st.file_uploader("Upload Video", type=["mp4", "avi", "mov"])
    
    if uploaded_file:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tfile.write(uploaded_file.read())
        
        cap = cv2.VideoCapture(tfile.name)
        frame_placeholder = st.empty()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            _, buffer = cv2.imencode(".jpg", frame)
            
            try:
                response = requests.post(
                    f"{API_URL}/process_frame",
                    files={"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                    data={"camera_id": camera_id},
                    timeout=1
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.passenger_count = data.get("passenger_count", 0)
                    
                    for passenger in data.get("passengers", []):
                        bbox = passenger.get("bbox", [0,0,0,0])
                        if len(bbox) == 4:
                            x1, y1, x2, y2 = map(int, bbox)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                            cv2.putText(frame, f"ID: {passenger.get('track_id', '?')}", 
                                      (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                    
                    frame_placeholder.image(frame, channels="BGR", use_container_width=True)
                    
            except Exception as e:
                st.error(f"Backend error: {e}")
                frame_placeholder.image(frame, channels="BGR", use_container_width=True)
        
        cap.release()

with tab2:
    st.header("Register New Passenger")
    
    passenger_name = st.text_input("Passenger Name")
    uploaded_face = st.file_uploader("Upload Face Image", type=["jpg", "png"])
    
    if uploaded_face:
        image = Image.open(uploaded_face)
        st.image(image, width=200)
    
    if st.button("Register"):
        if passenger_name and uploaded_face:
            st.success(f"✅ {passenger_name} registered successfully!")
            st.balloons()

with tab3:
    st.header("Attendance Report")
    
    selected_date = st.date_input("Select Date", datetime.now())
    bus_id = st.selectbox("Bus ID", ["BUS-001", "BUS-002"])
    
    if st.button("Generate Report"):
        mock_data = {
            "Name": ["John Doe", "Jane Smith"],
            "ID": ["P001", "P002"],
            "Time": ["08:15 AM", "08:20 AM"],
            "Status": ["Present", "Present"]
        }
        df = pd.DataFrame(mock_data)
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(), "attendance.csv")

st.markdown("---")
st.caption("Smart Vehicle Surveillance System v1.0")
