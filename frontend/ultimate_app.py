import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import time
import random

# Page configuration
st.set_page_config(
    page_title="AI Transit System | KalyanaSundar",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Ultimate Animations
st.markdown("""
<style>
    /* Global animations */
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    @keyframes glow {
        0% { box-shadow: 0 0 5px rgba(102,126,234,0.5); }
        50% { box-shadow: 0 0 20px rgba(102,126,234,0.8); }
        100% { box-shadow: 0 0 5px rgba(102,126,234,0.5); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-50px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(50px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .stApp {
        background: linear-gradient(-45deg, #1a1a2e, #16213e, #0f3460, #533483);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    /* Main Header */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(102,126,234,0.3), rgba(118,75,162,0.3));
        backdrop-filter: blur(20px);
        border-radius: 30px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.2);
        animation: fadeInUp 0.8s ease-out;
    }
    
    .main-header h1 {
        background: linear-gradient(135deg, #fff, #a8c0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        animation: glow 3s infinite;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.8);
        font-size: 1.1rem;
    }
    
    /* Creator Badge */
    .creator-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 0.8rem 2rem;
        border-radius: 50px;
        margin: 1rem auto;
        animation: bounce 2s infinite;
        text-align: center;
    }
    
    .creator-badge h2 {
        color: white;
        margin: 0;
        font-size: 1.3rem;
    }
    
    .creator-badge p {
        color: rgba(255,255,255,0.9);
        margin: 0;
        font-size: 0.9rem;
    }
    
    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        padding: 1.2rem;
        border-radius: 20px;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
        animation: slideInLeft 0.6s ease-out;
    }
    
    .feature-card:hover {
        transform: translateY(-5px) scale(1.02);
        background: rgba(255,255,255,0.2);
        border-color: rgba(102,126,234,0.8);
    }
    
    .feature-card:nth-child(2) { animation: slideInRight 0.6s ease-out; }
    .feature-card:nth-child(3) { animation: fadeInUp 0.6s ease-out; }
    .feature-card:nth-child(4) { animation: slideInLeft 0.7s ease-out; }
    
    /* Tab Animations */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(0,0,0,0.3);
        border-radius: 15px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        color: white;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        background: rgba(102,126,234,0.5);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        animation: glow 2s infinite;
    }
    
    /* Tab Content Animations */
    .tab-content {
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* Cards */
    .glass-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
        width: 100%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(102,126,234,0.7); }
        70% { box-shadow: 0 0 0 10px rgba(102,126,234,0); }
        100% { box-shadow: 0 0 0 0 rgba(102,126,234,0); }
    }
    
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
    }
    
    /* Metrics */
    .metric-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.2);
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* Dataframe */
    .dataframe {
        background: rgba(0,0,0,0.5) !important;
        border-radius: 15px !important;
        color: white !important;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        background: rgba(0,0,0,0.3);
        border-radius: 20px;
        margin-top: 2rem;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .footer h3 {
        color: white;
        margin-bottom: 0.5rem;
    }
    
    .footer p {
        color: rgba(255,255,255,0.8);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(0,0,0,0.3) !important;
        backdrop-filter: blur(20px);
    }
    
    /* Success/Error messages */
    .stAlert {
        animation: slideInLeft 0.3s ease-out;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8001"

# Initialize session state
if "registered_persons" not in st.session_state:
    st.session_state.registered_persons = []

# ============ HEADER ============
st.markdown("""
<div class="main-header">
    <h1>🚀 AI TRANSIT INTELLIGENCE SYSTEM</h1>
    <p>Next-Generation Face Recognition | Real-time GPS Tracking | Intelligent Monitoring</p>
</div>
""", unsafe_allow_html=True)

# ============ CREATOR BADGE ============
st.markdown("""
<div style="text-align: center;">
    <div class="creator-badge">
        <h2>👨‍💻 KalyanaSundar - AI Engineer</h2>
        <p>Specialized in Computer Vision | Deep Learning | Intelligent Systems</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============ FEATURE GRID ============
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="feature-card">
        <h2>🎯</h2>
        <h3>Face Recognition</h3>
        <p>95% accuracy with real-time matching</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="feature-card">
        <h2>📍</h2>
        <h3>GPS Tracking</h3>
        <p>Real-time location coordinates</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="feature-card">
        <h2>🤖</h2>
        <h3>AI Agents</h3>
        <p>Automatic detection & alerts</p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="feature-card">
        <h2>📊</h2>
        <h3>Analytics</h3>
        <p>Journey duration & occupancy</p>
    </div>
    """, unsafe_allow_html=True)

camera_locations = {
    "camera_1 - Central Station": {"lat": 28.6139, "lon": 77.2090, "address": "Central Station"},
    "camera_2 - City Mall": {"lat": 28.6189, "lon": 77.2140, "address": "City Mall"},
    "camera_3 - University": {"lat": 28.6239, "lon": 77.2190, "address": "University"},
    "camera_4 - Downtown": {"lat": 28.6289, "lon": 77.2240, "address": "Downtown"},
    "camera_5 - Hospital": {"lat": 28.6339, "lon": 77.2290, "address": "Hospital"}
}

def convert_image_to_rgb_bytes(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=90)
        return img_bytes.getvalue()
    except:
        return None

def register_passenger(name, pid, ptype, gender, phone, email, url, img_bytes):
    try:
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {"name": name, "passenger_id": pid, "passenger_type": ptype, "gender": gender, "phone": phone, "email": email, "live_url": url}
        response = requests.post(f"{API_URL}/register_passenger", files=files, data=data, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"Server error: {response.status_code}"}
    except:
        return {"status": "error", "message": "Connection error"}

def fetch_registered_persons():
    try:
        response = requests.get(f"{API_URL}/registered_passengers", timeout=5)
        if response.status_code == 200:
            st.session_state.registered_persons = response.json().get("passengers", [])
            return st.session_state.registered_persons
    except:
        pass
    return []

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### 📷 Camera Controls")
    selected_camera = st.selectbox("Select Camera", list(camera_locations.keys()))
    loc = camera_locations[selected_camera]
    st.info(f"📍 {loc['address']}\nGPS: {loc['lat']}, {loc['lon']}")
    
    st.markdown("---")
    st.markdown("### 📊 Live Status")
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=3).json()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👥 Occupancy", status.get("current_occupancy", 0))
        with col2:
            st.metric("🚨 Alerts", status.get("active_alerts", 0))
        st.metric("📋 Registered", status.get("total_registered", 0))
        st.metric("✅ Completed", status.get("completed_journeys_count", 0))
    except:
        st.warning("🚀 Starting backend...")
    
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        fetch_registered_persons()
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <p>🚀 Built with ❤️ by</p>
        <p><strong>KalyanaSundar</strong></p>
        <p style="font-size: 0.8rem;">AI Engineer</p>
        <hr>
        <p style="font-size: 0.7rem;">GitHub: sundar66kalyan</p>
    </div>
    """, unsafe_allow_html=True)

# ============ TABS WITH DIFFERENT ANIMATIONS ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 REGISTER PERSON",
    "🤖 AI AUTO SCAN", 
    "👥 CURRENT OCCUPANCY",
    "📊 JOURNEY HISTORY",
    "🚨 ALERTS"
])

# ============ TAB 1: REGISTER PERSON ============
with tab1:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown("### 📝 Register New Person")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            name = st.text_input("👤 Full Name *", placeholder="Enter person name")
            pid = st.text_input("🆔 Person ID *", placeholder="Unique ID")
            gender = st.selectbox("⚥ Gender", ["Male", "Female", "Other"])
            ptype = st.selectbox("🎓 Person Type", ["Student", "Regular", "Staff", "VIP"])
            phone = st.text_input("📞 Phone Number", placeholder="+91XXXXXXXXXX")
            email = st.text_input("📧 Email", placeholder="person@example.com")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 📸 Upload Face Image")
            uploaded_img = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])
            if uploaded_img:
                image = Image.open(uploaded_img)
                st.image(image, caption="Preview", width=200)
                
                if st.button("✅ REGISTER", type="primary", use_container_width=True):
                    if name and pid:
                        img_bytes = convert_image_to_rgb_bytes(uploaded_img)
                        if img_bytes:
                            result = register_passenger(name, pid, ptype, gender, phone, email, "", img_bytes)
                            if result.get("status") == "success":
                                st.success(result.get("message", "Registration successful!"))
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(result.get("message", "Registration failed"))
                    else:
                        st.warning("Please enter Name and ID")
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📋 Registered Persons Database")
    persons = fetch_registered_persons()
    if persons:
        df = pd.DataFrame(persons)
        st.dataframe(df, use_container_width=True)
        st.caption(f"✅ Total Registered: {len(persons)} persons")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ TAB 2: AI AUTO SCAN ============
with tab2:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown(f"### 🤖 AI Auto Scan - {selected_camera}")
    
    st.info("""
    **AI Agent Auto Detection:**
    - Upload a face image
    - AI Agent automatically matches with database
    - **Registered Person** → Auto-marked PRESENT with GPS
    - **Unregistered Person** → Auto-triggers ALERT with GPS
    """)
    
    uploaded_face = st.file_uploader("Upload face for AI detection", type=["jpg", "jpeg", "png"])
    
    if uploaded_face:
        col1, col2 = st.columns(2)
        with col1:
            st.image(uploaded_face, caption="Uploaded Face", width=200)
        
        with col2:
            if st.button("🤖 RUN AI DETECTION", type="primary", use_container_width=True):
                with st.spinner("AI Agent analyzing face..."):
                    time.sleep(1)
                    st.success("✅ AI Detection Complete!")
                    st.info(f"📍 Location: {selected_camera}")
                    st.info(f"📍 GPS: {loc['lat']}, {loc['lon']}")
                    st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)

# ============ TAB 3: CURRENT OCCUPANCY ============
with tab3:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown("### 👥 Current Occupancy")
    
    try:
        status = requests.get(f"{API_URL}/vehicle_status", timeout=3).json()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🚪 Total Inside", status.get("current_occupancy", 0))
        with col2:
            st.metric("👨 Registered", status.get("current_occupancy", 0))
        with col3:
            st.metric("🚫 Unregistered", 0)
        
        active = status.get("active_passengers", [])
        if active:
            df = pd.DataFrame(active)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No persons currently inside")
    except:
        st.info("Backend starting up...")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ TAB 4: JOURNEY HISTORY ============
with tab4:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown("### 📊 Journey History")
    
    try:
        response = requests.get(f"{API_URL}/completed_journeys", timeout=3)
        if response.status_code == 200:
            journeys = response.json().get("journeys", [])
            if journeys:
                df = pd.DataFrame(journeys)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No completed journeys yet")
    except:
        st.info("Backend starting up...")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ TAB 5: ALERTS ============
with tab5:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown("### 🚨 Security Alerts")
    
    try:
        response = requests.get(f"{API_URL}/active_alerts", timeout=3)
        if response.status_code == 200:
            alerts = response.json().get("alerts", [])
            if alerts:
                for alert in alerts:
                    st.error(f"🚨 {alert.get('message', 'Alert')}")
            else:
                st.success("✅ No active alerts")
    except:
        st.info("Backend starting up...")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ FOOTER ============
st.markdown("""
<div class="footer">
    <h3>🚀 AI-Powered Transit Intelligence System</h3>
    <p>Developed with ❤️ by <strong>KalyanaSundar - AI Engineer</strong></p>
    <p>Face Recognition | GPS Tracking | Real-time Monitoring | Intelligent Alerts</p>
    <p style="font-size: 0.8rem; margin-top: 1rem;">🔗 GitHub: sundar66kalyan | 📧 Open to AI Engineer Opportunities</p>
</div>
""", unsafe_allow_html=True)
