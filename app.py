import streamlit as st

st.set_page_config(page_title="AI Transit System", page_icon="🚀")

st.title("🚀 AI-Powered Transit Intelligence System")
st.markdown("### 👨‍💻 Developed by: KalyanaSundar - AI Engineer")

st.info("""
**Features:**
- ✅ Face Recognition
- ✅ GPS Tracking
- ✅ AI Agents
- ✅ Journey Duration
""")

st.success("✅ System is ready!")

# Demo metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Occupancy", "0")
with col2:
    st.metric("Registered", "0")
with col3:
    st.metric("Completed", "0")

st.markdown("---")
st.markdown("🔗 **GitHub:** https://github.com/sundar66kalyan/transit-intelligence-system")
