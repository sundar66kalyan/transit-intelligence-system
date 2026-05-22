# Alternative: Keep the video file instead of deleting
import streamlit as st
import cv2
import requests
import tempfile
import os
import time
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Vehicle Surveillance", page_icon="🚌", layout="wide")

API_URL = "http://localhost:8000"

st.title("🚌 Vehicle Surveillance System")

# Session state for video path
if "video_file" not in st.session_state:
    st.session_state.video_file = None

# Sidebar
with st.sidebar:
    st.header("Controls")
    camera_id = st.selectbox("Camera", ["Front Door", "Main Cabin", "Exit"])
    
    if st.button("Clear Video"):
        st.session_state.video_file = None
        st.rerun()

# Main content
uploaded_file = st.file_uploader("Upload Video", type=["mp4", "avi", "mov"])

if uploaded_file:
    # Save to persistent location instead of temp
    video_path = f"D:/VehicleSurveillanceSystem/uploads/{uploaded_file.name}"
    os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
    
    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    st.session_state.video_file = video_path
    st.success(f"Video saved: {uploaded_file.name}")

if st.session_state.video_file and os.path.exists(st.session_state.video_file):
    if st.button("Process Video"):
        cap = cv2.VideoCapture(st.session_state.video_file)
        frame_placeholder = st.empty()
        count_placeholder = st.empty()
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            if frame_count % 10 == 0:
                _, buffer = cv2.imencode(".jpg", frame)
                response = requests.post(
                    f"{API_URL}/process_frame",
                    files={"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                    data={"camera_id": camera_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    count_placeholder.metric("Passengers", data.get("passenger_count", 0))
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
            time.sleep(0.033)
        
        cap.release()
        st.success("Processing complete!")
