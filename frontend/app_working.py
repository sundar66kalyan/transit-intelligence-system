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

API_URL = "http://localhost:8001"

st.title("🚌 AI-Powered Vehicle Surveillance System")
st.markdown("*Real-Time Entry Detection & GPS Alerts*")

# Initialize session state
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Sidebar
with st.sidebar:
    st.header("📍 System Status")
    
    # Check backend connection
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ Backend Connected")
            st.info(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Not Connected")
        st.warning("Please start backend: python backend/main_simple.py")
        st.stop()
    
    st.markdown("---")
    st.header("📊 Statistics")
    
    # Get passenger count
    try:
        resp = requests.get(f"{API_URL}/passengers")
        if resp.status_code == 200:
            passenger_count = len(resp.json().get("passengers", []))
            st.metric("Registered Passengers", passenger_count)
    except:
        pass
    
    # Get alert count
    try:
        resp = requests.get(f"{API_URL}/active_alerts")
        if resp.status_code == 200:
            alert_count = resp.json().get("count", 0)
            st.metric("Active Alerts", alert_count, delta="🚨" if alert_count > 0 else None)
    except:
        pass
    
    st.markdown("---")
    bus_id = st.selectbox("Select Bus", ["BUS-001", "BUS-002", "BUS-003"])
    
    # Clear data button
    if st.button("🗑️ Clear All Data", use_container_width=True):
        try:
            requests.delete(f"{API_URL}/clear_data")
            st.success("Data cleared!")
            st.rerun()
        except:
            st.error("Failed to clear data")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚪 Entry Detection", "🚨 Live Alerts", "📋 Entry Logs", 
    "👤 Register Passenger", "📍 GPS Location"
])

with tab1:
    st.header("Real-Time Entry Detection")
    
    st.info("""
    **How it works:**
    1. **Upload the SAME image** you used for registration → System recognizes as REGISTERED
    2. **Upload a DIFFERENT image** → System detects as UNREGISTERED and triggers alert
    3. System compares image hash to identify matches
    """)
    
    # Show registered passengers for reference
    try:
        resp = requests.get(f"{API_URL}/passengers")
        if resp.status_code == 200:
            passengers = resp.json().get("passengers", [])
            if passengers:
                st.subheader("📋 Registered Passengers (For Reference)")
                for p in passengers:
                    st.caption(f"- {p['name']} (ID: {p['passenger_id']}) - Use the SAME face image to test")
    except:
        pass
    
    st.markdown("---")
    
    uploaded_image = st.file_uploader("Upload person's image for detection", type=["jpg", "jpeg", "png"], key="entry_test")
    
    if uploaded_image:
        col1, col2 = st.columns(2)
        with col1:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", width=250)
            st.caption(f"Image size: {uploaded_image.size} bytes")
        
        with col2:
            if st.button("🔍 Detect Person", type="primary", use_container_width=True):
                with st.spinner("Processing entry..."):
                    files = {"file": ("image.jpg", uploaded_image.getvalue(), "image/jpeg")}
                    data = {"bus_id": bus_id}
                    
                    try:
                        response = requests.post(f"{API_URL}/process_entry", files=files, data=data)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.last_result = result
                            
                            if result.get("result") == "registered":
                                st.success("✅ REGISTERED PERSON DETECTED")
                                st.balloons()
                                
                                passenger = result.get("passenger", {})
                                st.markdown(f"""
                                **✅ Entry Authorized**
                                - **Name:** {passenger.get('name', 'N/A')}
                                - **ID:** {passenger.get('passenger_id', 'N/A')}
                                - **Type:** {passenger.get('passenger_type', 'N/A')}
                                - **Location:** {result.get('location', {}).get('address', 'Unknown')}
                                - **Time:** {result.get('timestamp', 'N/A')[:19]}
                                """)
                                
                            elif result.get("result") == "unauthorized":
                                st.error("🚨 UNREGISTERED PERSON DETECTED!")
                                
                                # Add to alerts
                                if result.get("alert"):
                                    st.session_state.alerts.insert(0, result["alert"])
                                
                                alert = result.get("alert", {})
                                st.markdown(f"""
                                **🚨 SECURITY ALERT TRIGGERED**
                                - **Alert Type:** {alert.get('type', 'UNAUTHORIZED_ENTRY')}
                                - **Severity:** {alert.get('severity', 'HIGH')}
                                - **Location:** {result.get('location', {}).get('address', 'Unknown')}
                                - **Time:** {result.get('timestamp', 'N/A')[:19]}
                                
                                **Action Required:** Security team notified. Please verify identity.
                                """)
                                
                                # Show location on map
                                loc = result.get("location", {})
                                if loc:
                                    map_data = pd.DataFrame([{"lat": loc.get("lat", 0), "lon": loc.get("lon", 0)}])
                                    st.map(map_data)
                        else:
                            st.error(f"Server error: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"Connection error: {e}")
    
    # Show last result
    if st.session_state.last_result:
        st.markdown("---")
        st.subheader("Last Detection Result")
        if st.session_state.last_result.get("result") == "registered":
            st.success(st.session_state.last_result.get("message"))
        else:
            st.error(st.session_state.last_result.get("message"))

with tab2:
    st.header("🚨 Live Security Alerts")
    
    if st.button("🔄 Refresh Alerts", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/active_alerts")
        if response.status_code == 200:
            alerts_data = response.json()
            alerts_list = alerts_data.get("alerts", [])
            
            if alerts_list:
                st.warning(f"⚠️ {len(alerts_list)} Active Alerts")
                
                for alert in alerts_list:
                    with st.container():
                        st.error(f"""
                        **🚨 {alert.get('type', 'ALERT')}** - Severity: {alert.get('severity', 'HIGH')}
                        
                        **Message:** {alert.get('message', 'Unauthorized entry detected')}
                        
                        **Location:** {alert.get('location', {}).get('address', 'Unknown')}
                        - Latitude: {alert.get('location', {}).get('lat', 'N/A')}
                        - Longitude: {alert.get('location', {}).get('lon', 'N/A')}
                        
                        **Time:** {alert.get('timestamp', 'N/A')[:19]}
                        """)
                        st.markdown("---")
            else:
                st.success("✅ No active alerts. System is secure!")
    except Exception as e:
        st.error(f"Could not fetch alerts: {e}")

with tab3:
    st.header("📋 Entry/Exit Logs")
    
    if st.button("🔄 Refresh Logs", use_container_width=True):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/recent_entries")
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", [])
            
            if entries:
                df = pd.DataFrame(entries)
                st.dataframe(df, use_container_width=True)
                
                st.subheader("📊 Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    registered = len([e for e in entries if e.get("is_registered")])
                    st.metric("Registered Entries", registered, "✅")
                with col2:
                    unknown = len([e for e in entries if not e.get("is_registered")])
                    st.metric("Unknown Persons (Alerts)", unknown, "🚨")
                with col3:
                    st.metric("Total Events", len(entries))
            else:
                st.info("No entries recorded yet. Test by uploading images!")
    except Exception as e:
        st.error(f"Error: {e}")

with tab4:
    st.header("👤 Register New Passenger")
    
    st.info("""
    **Registration Instructions:**
    1. Enter passenger details
    2. Upload a CLEAR face image
    3. **Remember this image** - You'll need to upload the SAME image to test registered entry
    4. Different images will be detected as UNREGISTERED and trigger alerts
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        name = st.text_input("Full Name *", placeholder="Enter passenger name")
        passenger_id = st.text_input("Passenger ID *", placeholder="Enter unique ID (e.g., P001)")
        passenger_type = st.selectbox("Passenger Type", ["Student", "Regular", "Staff", "VIP"])
        is_blacklisted = st.checkbox("Mark as Blacklisted", help="Blacklisted persons trigger critical alerts")
        
    with col2:
        uploaded_face = st.file_uploader("Upload Face Image *", type=["jpg", "jpeg", "png"], key="register_face")
        
        if uploaded_face:
            image = Image.open(uploaded_face)
            st.image(image, caption="Face Preview - Use this same image for testing", width=200)
            st.caption(f"File: {uploaded_face.name}")
            st.info("💡 Save this image! You'll need to upload the SAME image to test registered entry.")
    
    if st.button("✅ Register Passenger", type="primary", use_container_width=True):
        if name and passenger_id and uploaded_face:
            files = {"file": ("face.jpg", uploaded_face.getvalue(), "image/jpeg")}
            data = {
                "name": name,
                "passenger_id": passenger_id,
                "passenger_type": passenger_type,
                "is_blacklisted": str(is_blacklisted).lower()
            }
            
            with st.spinner("Registering passenger..."):
                try:
                    response = requests.post(f"{API_URL}/register_face", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.success(f"✅ {name} (ID: {passenger_id}) registered successfully!")
                            st.balloons()
                            st.info("📌 Remember: Use the SAME face image to test registered entry. Different images will be detected as unregistered.")
                        else:
                            st.error(f"Registration failed: {result.get('message', 'Unknown error')}")
                    else:
                        st.error(f"Server error: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please fill all required fields")
    
    st.markdown("---")
    st.subheader("📋 Registered Passengers")
    
    try:
        response = requests.get(f"{API_URL}/passengers")
        if response.status_code == 200:
            passengers = response.json().get("passengers", [])
            if passengers:
                df = pd.DataFrame(passengers)
                if "image_hash" in df.columns:
                    df = df.drop(columns=["image_hash"])
                if "face_image_path" in df.columns:
                    df = df.drop(columns=["face_image_path"])
                st.dataframe(df, use_container_width=True)
                
                st.info("💡 To test registered entry, upload the EXACT SAME image you used for registration.")
            else:
                st.info("No passengers registered yet.")
    except Exception as e:
        st.error(f"Error: {e}")

with tab5:
    st.header("📍 GPS Location Tracking")
    
    if st.button("📍 Get Current Location", use_container_width=True):
        try:
            response = requests.get(f"{API_URL}/current_location")
            if response.status_code == 200:
                location = response.json()
                
                map_data = pd.DataFrame([{
                    "lat": location.get("lat", 28.6139),
                    "lon": location.get("lon", 77.2090)
                }])
                st.map(map_data)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Latitude", f"{location.get('lat', 0):.4f}")
                    st.metric("Location", location.get("address", "Unknown"))
                with col2:
                    st.metric("Longitude", f"{location.get('lon', 0):.4f}")
                    st.metric("Updated", datetime.now().strftime("%H:%M:%S"))
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.subheader("Journey Route")
    route_stops = pd.DataFrame([
        {"stop": "Central Station", "lat": 28.6139, "lon": 77.2090},
        {"stop": "City Mall", "lat": 28.6189, "lon": 77.2140},
        {"stop": "University", "lat": 28.6239, "lon": 77.2190},
        {"stop": "Downtown", "lat": 28.6289, "lon": 77.2240}
    ])
    st.map(route_stops)

st.markdown("---")
st.caption("🚌 Smart Vehicle Surveillance System v4.0 | Image Hash Based Recognition")
