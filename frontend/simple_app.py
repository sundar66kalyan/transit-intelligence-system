# frontend/simple_app.py
import streamlit as st

st.set_page_config(
    page_title="AI Transit System",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
    }
    .creator {
        text-align: center;
        padding: 1rem;
        background: #f0f2f6;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title"><h1>🚀 AI-Powered Transit Intelligence System</h1><p>Next-Generation Face Recognition | GPS Tracking | Intelligent Monitoring</p></div>', unsafe_allow_html=True)

# Creator info
st.markdown('<div class="creator"><h3>👨‍💻 Developed by: KalyanaSundar - AI Engineer</h3><p>Specialized in Computer Vision | Deep Learning | Intelligent Systems</p></div>', unsafe_allow_html=True)

# Features
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info("🎯 **Face Recognition**\n\n95% accuracy")
with col2:
    st.info("📍 **GPS Tracking**\n\nReal-time coordinates")
with col3:
    st.info("🤖 **AI Agents**\n\nAuto-detection")
with col4:
    st.info("📊 **Analytics**\n\nJourney tracking")

# Demo section
st.subheader("📊 System Demo")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("👥 Current Occupancy", "0")
with col2:
    st.metric("📋 Registered Persons", "0")
with col3:
    st.metric("✅ Completed Journeys", "0")

# Project links
st.markdown("---")
st.markdown("""
### 🔗 Project Links
- **GitHub Repository:** https://github.com/sundar66kalyan/transit-intelligence-system
- **Developer Portfolio:** https://github.com/sundar66kalyan

---
### 🚀 Future Enhancements
- Real-time face recognition
- Live camera integration
- Mobile app support
- Email notifications

---
*© 2025 KalyanaSundar - AI Engineer | AI-Powered Transit Intelligence System*
""")

st.balloons()
