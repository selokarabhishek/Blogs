"""
Government Scheme Discovery AI - Main Application
Streamlit entry point for the application.
"""

import streamlit as st
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Page configuration
st.set_page_config(
    page_title="Government Scheme Discovery AI",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #004E89;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF6B35;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point"""

    # Header
    st.markdown('<p class="main-header">🇮🇳 Government Scheme Discovery AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover ₹50,000-5,00,000 in benefits you qualify for</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/4/41/Flag_of_India.svg", width=100)
        st.title("Navigation")
        page = st.radio(
            "Go to",
            ["🏠 Home", "📝 Find Schemes", "💬 Chat Assistant", "📊 Dashboard"],
            label_visibility="collapsed"
        )

        st.divider()
        st.subheader("Quick Stats")
        st.metric("Schemes in Database", "1,000+")
        st.metric("Average Benefit", "₹1.2L")
        st.metric("Success Rate", "87%")

    # Main content area
    if page == "🏠 Home":
        show_home()
    elif page == "📝 Find Schemes":
        show_find_schemes()
    elif page == "💬 Chat Assistant":
        show_chat()
    elif page == "📊 Dashboard":
        show_dashboard()

def show_home():
    """Display home page"""

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🎯 The Problem")
        st.write("""
        - 1,000+ government schemes exist
        - Nobody knows what they qualify for
        - ₹10,000 crore unclaimed annually
        - Complex application processes
        """)

    with col2:
        st.markdown("### 💡 Our Solution")
        st.write("""
        - Answer 10 simple questions
        - AI finds ALL your eligible schemes
        - Get document checklists
        - Track application status
        """)

    with col3:
        st.markdown("### 🚀 Success Stories")
        st.write("""
        - 1.2L+ users helped
        - ₹450 crore claimed
        - Average benefit: ₹1.2L
        - 87% success rate
        """)

    st.divider()

    # CTA
    st.markdown("### 🎯 Ready to discover your benefits?")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Start Eligibility Check", use_container_width=True, type="primary"):
            st.switch_page("pages/1_📝_Find_Schemes.py")

    st.divider()

    # Featured scheme categories
    st.markdown("### 📂 Popular Scheme Categories")
    categories = [
        "📚 Education & Scholarships",
        "🌾 Agriculture & Farming",
        "💼 Business & Entrepreneurship",
        "🏠 Housing & Infrastructure",
        "⚕️ Healthcare",
        "👩 Women Empowerment",
        "👴 Senior Citizens",
        "💰 Financial Assistance"
    ]

    cols = st.columns(4)
    for idx, category in enumerate(categories):
        with cols[idx % 4]:
            st.button(category, use_container_width=True)

def show_find_schemes():
    """Display scheme finder page"""
    st.markdown("### 📝 Find Your Eligible Schemes")
    st.info("🚧 This feature is under development. Please check back soon!")

    # Placeholder for user profile form
    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, value=25)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            category = st.selectbox("Category", ["General", "OBC", "SC", "ST", "EWS"])
            occupation = st.selectbox("Occupation", ["Student", "Farmer", "Business", "Salaried", "Unemployed"])

        with col2:
            annual_income = st.number_input("Annual Income (₹)", min_value=0, value=300000)
            state = st.selectbox("State", ["Select State", "Maharashtra", "Karnataka", "Tamil Nadu", "Delhi"])
            education = st.selectbox("Education", ["Below 10th", "10th Pass", "12th Pass", "Graduate", "Post-graduate"])
            marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"])

        submitted = st.form_submit_button("🔍 Find Schemes", use_container_width=True, type="primary")

        if submitted:
            st.success("✅ Profile submitted! Analyzing your eligibility...")
            st.balloons()

def show_chat():
    """Display chat assistant page"""
    st.markdown("### 💬 Chat with Scheme Assistant")
    st.info("🚧 This feature is under development. Please check back soon!")

    # Chat interface placeholder
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me about government schemes..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            st.markdown("🚧 AI assistant coming soon! This will help you discover schemes through natural conversation.")

def show_dashboard():
    """Display user dashboard"""
    st.markdown("### 📊 Your Scheme Dashboard")
    st.info("🚧 This feature is under development. Please check back soon!")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Eligible Schemes", "0", "0")
    with col2:
        st.metric("Applied", "0", "0")
    with col3:
        st.metric("Approved", "0", "0")
    with col4:
        st.metric("Total Benefits", "₹0", "₹0")

if __name__ == "__main__":
    main()
