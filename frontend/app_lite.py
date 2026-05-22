import streamlit as st
import cv2
import requests
import numpy as np
import tempfile
import os
import time
from datetime import datetime
import pandas as pd
import random

st.set_page_config(
    page_title="Vehicle Surveillance System",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8000"

st.title("🚌 AI-Powered Smart Vehicle Surveillance System")
st.markdown("*Lite Mode - With Simulated Detection*")

# Initialize session state
if "processing" not in st.session_state:
    st.session_state.processing = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    camera_id = st.selectbox("Select Camera", ["Front Door", "Main Cabin", "Exit Door"])
    
    st.markdown("---")
    st.header("📊 Statistics")
    
    if "current_count" not in st.session_state:
        st.session_state.current_count = 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Passengers", st.session_state.current_count)
    with col2:
        st.metric("System Mode", "🟢 Demo")
    
    st.markdown("---")
    if st.button("🔄 Reset System"):
        st.session_state.processing = False
        st.session_state.current_count = 0
        st.rerun()

# Main content
tab1, tab2, tab3 = st.tabs(["📹 Live Surveillance", "👤 Face Registration", "📝 Attendance"])

with tab1:
    st.header("Real-Time Passenger Monitoring")
    
    # Check backend health
    try:
        health = requests.get(f"{API_URL}/health", timeout=2)
        if health.status_code == 200:
            st.success("✅ Backend connected")
    except:
        st.error("❌ Backend not connected. Please start the backend first!")
        st.code("python backend/main_lite.py", language="bash")
        st.stop()
    
    # Video upload
    uploaded_file = st.file_uploader("Upload Video for Analysis", type=["mp4", "avi", "mov"])
    
    if uploaded_file:
        if st.button("▶️ Start Processing", type="primary"):
            st.session_state.processing = True
        
        if st.session_state.processing:
            # Save uploaded file
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(uploaded_file.read())
            video_path = tfile.name
            
            # Process video
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            video_placeholder = st.empty()
            progress_bar = st.progress(0)
            metrics_placeholder = st.empty()
            
            frame_count = 0
            passenger_history = []
            
            while cap.isOpened() and st.session_state.processing:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                progress_bar.progress(frame_count / total_frames)
                
                # Process every 5th frame
                if frame_count % 5 == 0:
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
                            current_count = data.get("passenger_count", 0)
                            st.session_state.current_count = current_count
                            passenger_history.append(current_count)
                            
                            # Draw boxes
                            for passenger in data.get("passengers", []):
                                bbox = passenger.get("bbox", [0,0,0,0])
                                if len(bbox) == 4:
                                    x1, y1, x2, y2 = map(int, bbox)
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                                    cv2.putText(frame, f"{passenger.get('identity', '?')}", 
                                              (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                            
                            # Update metrics
                            with metrics_placeholder.container():
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Current Count", current_count)
                                with col2:
                                    st.metric("Frame", f"{frame_count}/{total_frames}")
                                with col3:
                                    st.metric("Mode", "AI Demo")
                    except Exception as e:
                        pass
                
                # Display frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                
                # Simulate real-time
                time.sleep(1/fps)
            
            cap.release()
            os.unlink(video_path)
            
            st.success("✅ Video processing completed!")
            
            # Show chart
            if passenger_history:
                st.subheader("Passenger Count Over Time")
                chart_data = pd.DataFrame({
                    "Frame": range(len(passenger_history)),
                    "Count": passenger_history
                })
                st.line_chart(chart_data.set_index("Frame"))
            
            st.session_state.processing = False

with tab2:
    st.header("Register New Passenger")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Passenger Name")
        passenger_id = st.text_input("Passenger ID")
    
    with col2:
        st.info("Demo mode: Face registration is simulated")
    
    if st.button("Register", type="primary"):
        if name and passenger_id:
            response = requests.post(
                f"{API_URL}/register_face",
                params={"name": name, "passenger_id": passenger_id}
            )
            if response.status_code == 200:
                st.success(f"✅ {name} registered successfully!")
                st.balloons()

with tab3:
    st.header("Attendance Report")
    
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", datetime.now())
    with col2:
        bus_id = st.selectbox("Bus ID", ["BUS-001", "BUS-002", "BUS-003"])
    
    if st.button("Generate Report"):
        response = requests.get(f"{API_URL}/attendance/{bus_id}", params={"date": str(date)})
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data["attendance"])
            st.dataframe(df, use_container_width=True)
            
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total", data["total_passengers"])
            with col2:
                st.metric("Present", data["present_count"])
            with col3:
                st.metric("Attendance Rate", f"{(data['present_count']/data['total_passengers']*100):.0f}%")
            
            # Download
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, f"attendance_{bus_id}.csv")

st.markdown("---")
st.caption("🚌 Smart Vehicle Surveillance System v3.0 (Lite Mode) | Simulated AI Detection")
