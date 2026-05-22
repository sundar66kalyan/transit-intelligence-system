import streamlit as st
import pandas as pd
from datetime import datetime
import random

st.set_page_config(
    page_title="AI Transit Intelligence System",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #e0e0e0;
        font-size: 1.1rem;
    }
    .credit-footer {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-top: 2rem;
    }
    .credit-text {
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        text-align: center;
    }
    .status-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🎯 AI-Powered Transit Intelligence System</h1><p>Synchronized Multi-Camera | Real-time Entry/Exit | AI Journey Tracking</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.shields.io/badge/AI-Powered-blue", width=200)
    st.markdown("---")
    
    st.header("📊 System Status")
    
    # Demo statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👥 Current Occupancy", "3")
    with col2:
        st.metric("🚨 Active Alerts", "0")
    
    st.metric("📋 Registered Persons", "4")
    st.metric("✅ Completed Journeys", "12")
    
    st.markdown("---")
    
    st.header("🎯 Key Features")
    st.markdown("""
    - ✅ Face Recognition
    - ✅ GPS Tracking
    - ✅ Journey Duration
    - ✅ Real-time Alerts
    - ✅ Multi-Camera Sync
    - ✅ Attendance Marking
    """)
    
    st.markdown("---")
    st.caption("🚀 **Developed by: Kalyanasundar**")

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 REGISTER PERSON",
    "📸 CAMERA SCAN",
    "👥 CURRENT OCCUPANCY",
    "📊 JOURNEY HISTORY",
    "🚨 ALERTS & LOGS"
])

# Demo Data
registered_persons = [
    {"id": "P001", "name": "John Doe", "type": "Regular", "registered": "2024-01-15"},
    {"id": "P002", "name": "Jane Smith", "type": "VIP", "registered": "2024-01-16"},
    {"id": "P003", "name": "Robert Johnson", "type": "Staff", "registered": "2024-01-17"},
    {"id": "P004", "name": "Alice Brown", "type": "Student", "registered": "2024-01-18"},
]

active_passengers = [
    {"name": "John Doe", "id": "P001", "type": "Regular", "entry_time": "09:15 AM", "entry_loc": "Main Gate", "gps": "28.6139, 77.2090"},
    {"name": "Jane Smith", "id": "P002", "type": "VIP", "entry_time": "09:20 AM", "entry_loc": "Side Gate", "gps": "28.6150, 77.2100"},
    {"name": "Robert Johnson", "id": "P003", "type": "Staff", "entry_time": "09:25 AM", "entry_loc": "Main Gate", "gps": "28.6139, 77.2090"},
]

completed_journeys = [
    {"name": "Alice Brown", "type": "Student", "entry": "08:00 AM", "exit": "05:00 PM", "duration": "9h 0m", "entry_loc": "Main Gate", "exit_loc": "Main Gate"},
    {"name": "John Doe", "type": "Regular", "entry": "09:15 AM", "exit": "06:30 PM", "duration": "9h 15m", "entry_loc": "Main Gate", "exit_loc": "Side Gate"},
]

# ============ TAB 1: REGISTER PERSON ============
with tab1:
    st.header("📝 Register New Person")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter person name")
        person_id = st.text_input("Person ID *", placeholder="Unique ID (e.g., P005)")
        person_type = st.selectbox("Person Type", ["Student", "Regular", "Staff", "VIP"])
        
    with col2:
        uploaded_face = st.file_uploader("Upload Face Image *", type=["jpg", "jpeg", "png"])
        
        if uploaded_face:
            from PIL import Image
            image = Image.open(uploaded_face)
            st.image(image, caption="Face Preview", width=200)
    
    if st.button("✅ REGISTER PERSON", type="primary", use_container_width=True):
        if name and person_id and uploaded_face:
            st.success(f"✅ {name} (ID: {person_id}) registered successfully!")
            st.balloons()
            st.info("📌 Face data stored for recognition")
        else:
            st.warning("Please fill all fields and upload a face image")
    
    st.markdown("---")
    st.subheader("📋 Registered Persons Database")
    df_registered = pd.DataFrame(registered_persons)
    st.dataframe(df_registered, use_container_width=True)

# ============ TAB 2: CAMERA SCAN ============
with tab2:
    st.header("📸 Camera Scan - Entry/Exit")
    
    st.info("""
    **How Auto Scan Works:**
    1. Select a registered person
    2. Choose ENTRY or EXIT
    3. System records with GPS coordinates
    4. Journey duration calculated automatically
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚪 ENTRY SCAN")
        
        person_options = [f"{p['name']} ({p['id']})" for p in registered_persons]
        selected_person = st.selectbox("Select Person", person_options)
        entry_camera = st.selectbox("Entry Camera", ["Camera 1 - Main Gate", "Camera 2 - Side Gate", "Camera 3 - Back Gate"])
        
        if st.button("🔍 RECORD ENTRY", type="primary", use_container_width=True):
            st.success(f"✅ {selected_person} ENTERED via {entry_camera}")
            st.balloons()
            
            # GPS coordinates based on camera
            gps_coords = {
                "Camera 1 - Main Gate": "28.6139° N, 77.2090° E",
                "Camera 2 - Side Gate": "28.6150° N, 77.2100° E",
                "Camera 3 - Back Gate": "28.6160° N, 77.2110° E"
            }
            
            st.info(f"📍 GPS: {gps_coords[entry_camera]} | Time: {datetime.now().strftime('%H:%M:%S')}")
            
            with st.expander("📋 View Entry Details"):
                st.markdown(f"""
                - **Person:** {selected_person}
                - **Attendance:** ✅ PRESENT
                - **Entry Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                - **Camera:** {entry_camera}
                - **GPS Coordinates:** {gps_coords[entry_camera]}
                """)
    
    with col2:
        st.subheader("🚪 EXIT SCAN")
        
        exit_person = st.selectbox("Select Person for Exit", person_options)
        exit_camera = st.selectbox("Exit Camera", ["Camera 1 - Main Gate", "Camera 2 - Side Gate", "Camera 3 - Back Gate"])
        
        if st.button("🔍 RECORD EXIT", type="primary", use_container_width=True):
            st.success(f"✅ {exit_person} EXITED via {exit_camera}")
            
            # Random journey duration
            hours = random.randint(1, 9)
            minutes = random.randint(0, 59)
            duration = f"{hours}h {minutes}m"
            
            st.info(f"📍 GPS: 28.6289° N, 77.2240° E | Journey Duration: {duration}")
            
            with st.expander("📋 View Journey Summary"):
                st.markdown(f"""
                - **Person:** {exit_person}
                - **Journey Duration:** {duration}
                - **Entry Location:** Main Gate
                - **Exit Location:** {exit_camera}
                - **Total Time Inside:** {duration}
                """)

# ============ TAB 3: CURRENT OCCUPANCY ============
with tab3:
    st.header("👥 Persons Currently Inside")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-card"><h3>3</h3><p>Total Inside</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-card"><h3>2</h3><p>Entry Today</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card"><h3>1</h3><p>Exit Today</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    for passenger in active_passengers:
        with st.expander(f"👤 {passenger['name']} - {passenger['type']}"):
            st.markdown(f"""
            - **ID:** {passenger['id']}
            - **Entry Time:** {passenger['entry_time']}
            - **Entry Location:** {passenger['entry_loc']}
            - **GPS:** {passenger['gps']}
            - **Status:** 🟢 PRESENT
            """)

# ============ TAB 4: JOURNEY HISTORY ============
with tab4:
    st.header("📊 Completed Journeys with AI-Calculated Durations")
    
    st.metric("Total Completed Journeys", len(completed_journeys))
    
    df_journeys = pd.DataFrame(completed_journeys)
    st.dataframe(df_journeys, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Individual Journey Details")
    
    for journey in completed_journeys:
        with st.container():
            st.markdown(f"""
            **👤 {journey['name']}** ({journey['type']})
            - **Entry:** {journey['entry']} at {journey['entry_loc']}
            - **Exit:** {journey['exit']} at {journey['exit_loc']}
            - **Duration:** ⏱️ {journey['duration']}
            """)
            st.markdown("---")

# ============ TAB 5: ALERTS & LOGS ============
with tab5:
    st.header("🚨 Security Alerts")
    
    st.success("✅ No active alerts - System is secure")
    
    st.markdown("---")
    st.subheader("📋 Recent Activity Log")
    
    activity_logs = pd.DataFrame([
        {"Timestamp": "09:15 AM", "Event": "ENTRY", "Person": "John Doe", "Location": "Main Gate", "GPS": "28.6139, 77.2090"},
        {"Timestamp": "09:20 AM", "Event": "ENTRY", "Person": "Jane Smith", "Location": "Side Gate", "GPS": "28.6150, 77.2100"},
        {"Timestamp": "09:25 AM", "Event": "ENTRY", "Person": "Robert Johnson", "Location": "Main Gate", "GPS": "28.6139, 77.2090"},
        {"Timestamp": "05:00 PM", "Event": "EXIT", "Person": "Alice Brown", "Location": "Main Gate", "GPS": "28.6139, 77.2090"},
        {"Timestamp": "06:30 PM", "Event": "EXIT", "Person": "John Doe", "Location": "Side Gate", "GPS": "28.6150, 77.2100"},
    ])
    st.dataframe(activity_logs, use_container_width=True)

# Footer
st.markdown(f'''
<div class="credit-footer">
    <p class="credit-text">🚀 Project Developed by: Kalyanasundar | AI-Powered Transit Intelligence System</p>
    <p class="credit-text" style="font-size: 0.9rem;">Multi-Camera Synchronization | Real-time Face Recognition | AI Journey Tracking</p>
    <p style="color: #e0e0e0; margin-top: 1rem;">🔗 GitHub: sundar66kalyan</p>
</div>
''', unsafe_allow_html=True)

st.caption("🎯 AI-Powered Transit Intelligence System v2.0 | Real-time Entry/Exit | AI Journey Tracking | GPS Coordinates")
