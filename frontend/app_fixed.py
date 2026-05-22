import streamlit as st
import cv2
import requests
import numpy as np
import tempfile
import os
import time
from datetime import datetime
import pandas as pd
import atexit

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
if "video_path" not in st.session_state:
    st.session_state.video_path = None
if "current_count" not in st.session_state:
    st.session_state.current_count = 0

# Function to cleanup on session end (not during processing)
def cleanup_temp_file():
    if st.session_state.video_path and os.path.exists(st.session_state.video_path):
        try:
            time.sleep(2)
            os.unlink(st.session_state.video_path)
            print(f"Cleaned up: {st.session_state.video_path}")
        except:
            pass

# Register cleanup on app exit
atexit.register(cleanup_temp_file)

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    camera_id = st.selectbox("Select Camera", ["Front Door", "Main Cabin", "Exit Door"])
    
    st.markdown("---")
    st.header("📊 Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Passengers", st.session_state.current_count)
    with col2:
        st.metric("System Mode", "🟢 Demo")
    
    st.markdown("---")
    if st.button("🔄 Reset Session"):
        st.session_state.processing = False
        st.session_state.current_count = 0
        # Don't delete file here - let atexit handle it
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
        else:
            st.warning("⚠️ Backend connection issue")
    except:
        st.error("❌ Backend not connected. Please start the backend first!")
        st.code("python backend/main_lite.py", language="bash")
        st.stop()
    
    # Video upload section
    uploaded_file = st.file_uploader("Upload Video for Analysis", type=["mp4", "avi", "mov", "mkv"])
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            start_processing = st.button("▶️ Start Processing", type="primary", use_container_width=True)
        with col2:
            stop_processing = st.button("⏹️ Stop", use_container_width=True)
        
        if stop_processing:
            st.session_state.processing = False
            st.rerun()
        
        if start_processing:
            st.session_state.processing = True
            
            # Save file to persistent location (not temp)
            save_dir = "D:/VehicleSurveillanceSystem/uploads"
            os.makedirs(save_dir, exist_ok=True)
            
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"upload_{timestamp}.mp4"
            video_path = os.path.join(save_dir, video_filename)
            
            # Save file
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.video_path = video_path
            st.info(f"📁 Video saved: {video_filename}")
        
        if st.session_state.processing and st.session_state.video_path and os.path.exists(st.session_state.video_path):
            try:
                # Open video
                cap = cv2.VideoCapture(st.session_state.video_path)
                if not cap.isOpened():
                    st.error("Could not open video file")
                    st.session_state.processing = False
                else:
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    if fps <= 0 or fps > 60:
                        fps = 30
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
                        if total_frames > 0:
                            progress_bar.progress(min(frame_count / total_frames, 1.0))
                        
                        # Process every 5th frame
                        if frame_count % 5 == 0:
                            _, buffer = cv2.imencode(".jpg", frame)
                            
                            try:
                                response = requests.post(
                                    f"{API_URL}/process_frame",
                                    files={"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                                    data={"camera_id": camera_id},
                                    timeout=2
                                )
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    current_count = data.get("passenger_count", 0)
                                    st.session_state.current_count = current_count
                                    passenger_history.append(current_count)
                                    
                                    # Draw bounding boxes
                                    for passenger in data.get("passengers", []):
                                        bbox = passenger.get("bbox", [0,0,0,0])
                                        if len(bbox) == 4:
                                            x1, y1, x2, y2 = map(int, bbox)
                                            # Ensure coordinates are within frame
                                            x1, y1 = max(0, x1), max(0, y1)
                                            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
                                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                                            label = passenger.get('identity', f'P{passenger.get("track_id", "?")}')
                                            cv2.putText(frame, label, (x1, y1-10), 
                                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                                    
                                    # Update metrics
                                    with metrics_placeholder.container():
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Current Count", current_count)
                                        with col2:
                                            st.metric("Frame", f"{frame_count}/{total_frames}")
                                        with col3:
                                            avg = sum(passenger_history[-10:]) / len(passenger_history[-10:]) if passenger_history else 0
                                            st.metric("Avg (last 10)", f"{avg:.1f}")
                            except requests.exceptions.Timeout:
                                pass
                            except Exception as e:
                                st.warning(f"Processing error: {e}")
                        
                        # Display frame
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                        
                        # Control playback speed
                        time.sleep(1/fps)
                    
                    cap.release()
                    
                    st.success("✅ Video processing completed!")
                    
                    # Show chart
                    if passenger_history:
                        st.subheader("📊 Passenger Count Over Time")
                        chart_data = pd.DataFrame({
                            "Frame": range(len(passenger_history)),
                            "Passenger Count": passenger_history
                        })
                        st.line_chart(chart_data.set_index("Frame"))
                    
                    st.session_state.processing = False
                    
                    # Offer to delete file
                    if st.button("🗑️ Delete Video File"):
                        try:
                            os.unlink(st.session_state.video_path)
                            st.success("Video file deleted")
                            st.session_state.video_path = None
                        except Exception as e:
                            st.warning(f"File will be deleted on next restart: {e}")
            
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.processing = False
        
        elif not st.session_state.processing and st.session_state.video_path:
            st.info("Processing stopped. Upload a new video to start again.")

with tab2:
    st.header("Register New Passenger")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Passenger Name", placeholder="Enter full name")
        passenger_id = st.text_input("Passenger ID", placeholder="Enter unique ID")
        passenger_type = st.selectbox("Passenger Type", ["Student", "Regular", "Staff", "VIP"])
    
    with col2:
        st.info("💡 Demo Mode")
        st.markdown("""
        Face registration is simulated in lite mode.
        
        **Features:**
        - Identity verification
        - Attendance tracking
        - Blacklist management
        """)
    
    if st.button("✅ Register Passenger", type="primary", use_container_width=True):
        if name and passenger_id:
            try:
                response = requests.post(
                    f"{API_URL}/register_face",
                    params={"name": name, "passenger_id": passenger_id}
                )
                if response.status_code == 200:
                    st.success(f"✅ {name} (ID: {passenger_id}) registered successfully!")
                    st.balloons()
                else:
                    st.error("Registration failed")
            except:
                st.success(f"✅ Demo: {name} registered successfully!")
                st.balloons()
        else:
            st.warning("Please enter both name and ID")

with tab3:
    st.header("📝 Attendance Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_date = st.date_input("Select Date", datetime.now())
    with col2:
        bus_id = st.selectbox("Bus ID", ["BUS-001 (Route A)", "BUS-002 (Route B)", "BUS-003 (Route C)"])
    with col3:
        shift = st.selectbox("Shift", ["Morning (6AM-12PM)", "Afternoon (12PM-6PM)", "Evening (6PM-10PM)"])
    
    if st.button("📊 Generate Report", type="primary", use_container_width=True):
        try:
            response = requests.get(f"{API_URL}/attendance/{bus_id.split()[0]}", params={"date": str(selected_date)})
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data["attendance"])
                st.dataframe(df, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Passengers", data["total_passengers"])
                with col2:
                    st.metric("Present", data["present_count"])
                with col3:
                    absent = data["total_passengers"] - data["present_count"]
                    st.metric("Absent", absent)
                with col4:
                    rate = (data["present_count"] / data["total_passengers"] * 100) if data["total_passengers"] > 0 else 0
                    st.metric("Attendance Rate", f"{rate:.0f}%")
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV Report",
                    csv,
                    f"attendance_{bus_id}_{selected_date}.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                st.error("Failed to fetch attendance")
        except:
            # Fallback mock data
            mock_df = pd.DataFrame({
                "Passenger ID": ["P001", "P002", "P003", "P004", "P005"],
                "Name": ["John Doe", "Jane Smith", "Bob Johnson", "Alice Brown", "Charlie Wilson"],
                "Boarding Time": ["08:15 AM", "08:20 AM", "08:25 AM", "08:30 AM", "08:35 AM"],
                "Status": ["Present", "Present", "Present", "Late", "Present"]
            })
            st.dataframe(mock_df, use_container_width=True)
            st.info("Demo data - Backend not available")

# Footer
st.markdown("---")
st.caption("🚌 Smart Vehicle Surveillance System v3.0 | Powered by AI")
