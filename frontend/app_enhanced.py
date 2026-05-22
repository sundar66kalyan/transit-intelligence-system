import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import io

st.set_page_config(
    page_title="Vehicle Surveillance System",
    page_icon="🚌",
    layout="wide"
)

API_URL = "http://localhost:8000"

st.title("🚌 AI-Powered Smart Vehicle Surveillance System")
st.markdown("*With Face Registration & Attendance Management*")

# Initialize session state
if "processing" not in st.session_state:
    st.session_state.processing = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    camera_id = st.selectbox("Select Camera", ["Front Door", "Main Cabin", "Exit Door", "Driver Area"])
    
    st.markdown("---")
    st.header("📊 Statistics")
    
    if "current_count" not in st.session_state:
        st.session_state.current_count = 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Passengers", st.session_state.current_count)
    with col2:
        st.metric("System Mode", "🟢 Active")
    
    st.markdown("---")
    
    # Check backend health
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Not Connected")
        st.info("Start backend: python backend/main_enhanced.py")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📹 Live Surveillance", "👤 Face Registration", "📝 Attendance Report", "📋 Registered Passengers"])

with tab1:
    st.header("Real-Time Passenger Monitoring")
    
    st.info("""
    **Demo Mode**: 
    - Upload a video to see passenger detection
    - Recognized passengers are automatically marked present
    - Unknown persons are flagged for review
    """)
    
    uploaded_file = st.file_uploader("Upload Video for Analysis", type=["mp4", "avi", "mov", "mkv"])
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Processing", type="primary"):
                st.session_state.processing = True
        with col2:
            if st.button("⏹️ Stop"):
                st.session_state.processing = False
        
        if st.session_state.processing:
            # Save uploaded file
            os.makedirs("D:/VehicleSurveillanceSystem/uploads", exist_ok=True)
            video_path = f"D:/VehicleSurveillanceSystem/uploads/demo_video.mp4"
            
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.video(video_path)
            st.success("✅ Video loaded - Detection simulation active")
            
            # Simulate detection results
            st.subheader("Detection Results")
            
            # Get registered passengers
            try:
                response = requests.get(f"{API_URL}/passengers")
                if response.status_code == 200:
                    passengers = response.json().get("passengers", [])
                    if passengers:
                        st.write(f"**Recognized Passengers:** {len(passengers)}")
                        for p in passengers[:5]:
                            st.success(f"✅ {p['name']} (ID: {p['passenger_id']}) - Marked Present")
                    else:
                        st.info("No registered passengers yet. Add some in the Face Registration tab!")
            except:
                pass

with tab2:
    st.header("📸 Register New Passenger with Face Image")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Passenger Details")
        name = st.text_input("Full Name *", placeholder="Enter passenger name")
        passenger_id = st.text_input("Passenger ID *", placeholder="Enter unique ID")
        passenger_type = st.selectbox("Passenger Type", ["Student", "Regular Commuter", "Staff", "VIP", "Elderly", "Disabled"])
        
    with col2:
        st.subheader("Face Image Upload")
        uploaded_face = st.file_uploader("Upload a clear face image", type=["jpg", "jpeg", "png"], key="face_upload")
        
        if uploaded_face:
            # Display uploaded image
            image = Image.open(uploaded_face)
            st.image(image, caption="Face Preview", width=250)
            
            # Display image info
            st.caption(f"Image size: {uploaded_face.size} bytes")
            st.caption(f"Format: {uploaded_face.type}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Register Passenger", type="primary", use_container_width=True):
            if name and passenger_id and uploaded_face:
                # Prepare form data
                files = {
                    "file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")
                }
                data = {
                    "name": name,
                    "passenger_id": passenger_id,
                    "passenger_type": passenger_type
                }
                
                try:
                    response = requests.post(
                        f"{API_URL}/register_face",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.success(f"✅ {name} (ID: {passenger_id}) registered successfully!")
                            st.balloons()
                            
                            # Show registration details
                            with st.expander("Registration Details"):
                                st.json(result)
                        else:
                            st.error(f"Registration failed: {result.get('message', 'Unknown error')}")
                    else:
                        st.error(f"Server error: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Connection error: {e}")
                    st.info("Make sure the backend is running: python backend/main_enhanced.py")
            else:
                st.warning("Please fill all required fields (*) and upload a face image")

with tab3:
    st.header("📊 Attendance Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_date = st.date_input("Select Date", datetime.now())
    with col2:
        bus_id = st.selectbox("Select Bus", ["BUS-001", "BUS-002", "BUS-003", "BUS-004"])
    with col3:
        report_type = st.selectbox("Report Type", ["Daily", "Weekly", "Monthly"])
    
    if st.button("📊 Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating report..."):
            try:
                response = requests.get(
                    f"{API_URL}/attendance/{bus_id}",
                    params={"date": selected_date.strftime("%Y-%m-%d")}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Summary Cards
                    st.subheader("📈 Summary Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Passengers", data["total_passengers"])
                    with col2:
                        st.metric("Present", data["present_count"], delta="✅")
                    with col3:
                        st.metric("Absent", data["absent_count"], delta="❌")
                    with col4:
                        st.metric("Attendance Rate", f"{data['attendance_rate']:.1f}%")
                    
                    # Detailed Table
                    st.subheader("📋 Detailed Attendance List")
                    
                    # Create DataFrame
                    df = pd.DataFrame(data["attendance"])
                    
                    # Color code the status
                    def color_status(val):
                        if val == "Present":
                            return "background-color: #90EE90"
                        elif val == "Absent":
                            return "background-color: #FFB6C1"
                        return ""
                    
                    # Display styled dataframe
                    styled_df = df.style.applymap(color_status, subset=["attendance"])
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Download options
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            f"attendance_{bus_id}_{selected_date}.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        # Mark absentees manually
                        st.info("💡 To mark attendance, passengers are auto-detected when recognized")
                    
                else:
                    st.error("Failed to fetch attendance data")
                    
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure backend is running")

with tab4:
    st.header("📋 Registered Passengers Database")
    
    try:
        response = requests.get(f"{API_URL}/passengers")
        if response.status_code == 200:
            passengers = response.json().get("passengers", [])
            
            if passengers:
                st.success(f"Total Registered: {len(passengers)} passengers")
                
                # Create display dataframe
                df = pd.DataFrame(passengers)
                if "face_image" in df.columns:
                    df = df.drop(columns=["face_image"])
                
                st.dataframe(df, use_container_width=True)
                
                # Display face images in grid
                st.subheader("Registered Face Images")
                cols = st.columns(3)
                for idx, passenger in enumerate(passengers):
                    with cols[idx % 3]:
                        if passenger.get("face_image") and os.path.exists(passenger["face_image"]):
                            st.image(passenger["face_image"], caption=passenger["name"], width=150)
                        else:
                            st.info(f"📷 {passenger['name']}\nNo image available")
            else:
                st.info("No passengers registered yet. Go to 'Face Registration' tab to add some!")
        else:
            st.error("Could not fetch passenger list")
    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("🚌 Smart Vehicle Surveillance System v3.0 | Face Recognition & Attendance Management")
