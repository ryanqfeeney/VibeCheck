import streamlit as st
from datetime import datetime
import hashlib
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from models import VibeAnalyzer
from utils.security import RateLimiter
from utils.validators import validate_file
from config.security_config import SecurityConfig
import os

# Load environment variables
load_dotenv()

# Initialize components
rate_limiter = RateLimiter()

# Add these near the top of the file, after imports
st.set_page_config(
    page_title="Vibe Check",
    page_icon="🎭",
    layout="centered",  # Changed from "wide" to "centered" for better mobile display
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Add this immediately after set_page_config
if 'STREAMLIT_SERVER_PORT' not in os.environ:
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'

# Add this CSS for better mobile responsiveness
st.markdown("""
<style>
    .stApp {
        background-color: #1E3D59;  /* Dark blue background */
    }
    .main-header {
        font-size: clamp(1.5em, 5vw, 2.5em);
        text-align: center;
        padding: 1rem 0;
        color: white;  /* White text for contrast */
    }
    .stTextArea textarea {
        font-size: 16px !important;
    }
    .uploadedFile {
        max-width: 100%;
    }
    .stButton>button {
        width: 100%;
        padding: 0.5rem;
        font-size: 16px !important;
    }
    @media (max-width: 768px) {
        .stExpander {
            margin: 0 -1rem;
        }
        .row-widget.stButton {
            padding: 0.5rem 0;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        .stTextArea>div>div>textarea {
            min-height: 100px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False
            # Clear the password field
            st.session_state["password"] = ""
            # Show error message
            st.error("😕 Password incorrect. Please try again.")

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    
    # Return True if the password is correct
    return st.session_state["password_correct"]

def main():
    st.markdown("<h1 class='main-header'>🎭 Vibe Check</h1>", unsafe_allow_html=True)
    
    if not check_password():
        st.stop()  # Don't run the rest of the app
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()

    analyzer = VibeAnalyzer()

    # File uploader with mobile-friendly container
    st.markdown("<div class='uploadedFile'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload screenshot or image", type=['png', 'jpg', 'jpeg'])
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Text input area with adjusted height for mobile
    text_input = st.text_area(
        "Or paste text directly:",
        height=150,  # Reduced height for mobile
        placeholder="Paste your conversation here..."
    )
    
    # Process uploaded file
    if uploaded_file:
        error = validate_file(uploaded_file)
        if error:
            st.error(error)
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            text_input = pytesseract.image_to_string(image)
            st.text_area(
                "Extracted Text (edit if needed):", 
                value=text_input, 
                height=150  # Reduced height for mobile
            )
    
    # Additional context and questions - Modified for better mobile layout
    with st.expander("➕ Additional Context & Questions (Optional)", expanded=False):
        # Changed from columns to sequential layout for mobile
        context = st.text_area(
            "Additional Context:",
            placeholder="Add any background information or context...",
            height=100
        )
        specific_questions = st.text_area(
            "Specific Questions:",
            placeholder="Any specific questions you want answered...",
            height=100
        )
    
    # Analysis button
    if st.button("Check the Vibe ✨", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text to analyze.")
            return
            
        if not rate_limiter.check_rate_limit(st.session_state.user_id):
            st.error("Rate limit exceeded. Please wait before making more requests.")
            return
            
        with st.spinner("Analyzing vibes..."):
            try:
                analysis, tokens, cost, stats = analyzer.analyze_vibe(
                    text_input,
                    context=context if context.strip() else None,
                    specific_questions=specific_questions if specific_questions.strip() else None
                )
                
                if "error" in stats:
                    st.error(stats["error"])
                    return

                st.markdown("### Analysis Results")
                st.write(analysis)
                
                # Modified stats display for mobile
                with st.expander("📊 Usage Statistics", expanded=False):
                    st.write(f"Tokens used: {stats['tokens']}")
                    
                    # Cost tracking section - simplified for mobile
                    st.markdown("### 💰 Cost Tracking")
                    st.metric("Requests Today", stats['request_count'])
                    st.metric("Current Total", f"${stats['total_cost']:.6f}")
                    st.metric("Daily Limit", f"${stats['max_cost']:.6f}")
                    
                    st.write(f"Last request cost: ${stats['request_cost']:.6f}")
                    if stats['max_cost'] > 0:
                        st.progress(min(float(stats['total_cost'] / stats['max_cost']), 1.0))
                    
                    if st.button("🔄 Reset Tracking", key="reset_button"):
                        rate_limiter.reset()
                        stats = analyzer.reset_tracking()
                        st.success("All tracking has been reset!")
                        st.rerun()
                    
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()