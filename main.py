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

# Load environment variables
load_dotenv()

# Initialize components
rate_limiter = RateLimiter()

def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    
    return st.session_state["password_correct"]

def main():
    st.markdown("<h1 class='main-header'>🎭 Vibe Check</h1>", unsafe_allow_html=True)
    
    if not check_password():
        st.stop()  # Don't run the rest of the app
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()

    analyzer = VibeAnalyzer()

    # File uploader
    uploaded_file = st.file_uploader("Upload screenshot or image", type=['png', 'jpg', 'jpeg'])
    
    # Text input area
    text_input = st.text_area(
        "Or paste text directly:",
        height=200,
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
            st.text_area("Extracted Text (edit if needed):", value=text_input, height=200)
    
    # Additional context and questions
    with st.expander("➕ Additional Context & Questions (Optional)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            context = st.text_area(
                "Additional Context:",
                placeholder="Add any background information or context...",
                height=100
            )
        with col2:
            specific_questions = st.text_area(
                "Specific Questions:",
                placeholder="Any specific questions you want answered...",
                height=100
            )
    
    # # Debug display (optional)
    # if st.session_state.get('request_history'):
    #     with st.expander("Debug: Rate Limit Info"):
    #         user_id = st.session_state.user_id
    #         if user_id in st.session_state.request_history:
    #             recent = len([t for t in st.session_state.request_history[user_id]
    #                         if (datetime.now() - t).seconds < SecurityConfig.RATE_LIMIT_PERIOD])
    #             st.write(f"Recent requests in last minute: {recent}")
    #             st.write(f"Rate limit: {SecurityConfig.MAX_REQUESTS_PER_PERIOD} per {SecurityConfig.RATE_LIMIT_PERIOD}s")

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
                
                with st.expander("📊 Usage Statistics", expanded=True):
                    st.write(f"Tokens used: {stats['tokens']}")
                    
                    # Cost tracking section
                    st.markdown("### 💰 Cost Tracking")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Requests Today", stats['request_count'])
                    col2.metric("Current Total", f"${stats['total_cost']:.6f}")
                    col3.metric("Daily Limit", f"${stats['max_cost']:.6f}")
                    
                    st.write(f"Last request cost: ${stats['request_cost']:.6f}")
                    if stats['max_cost'] > 0:
                        st.progress(min(float(stats['total_cost'] / stats['max_cost']), 1.0))
                    
                    # Reset button with proper handling
                    if st.button("🔄 Reset Tracking", key="reset_button"):
                        # Reset both rate limiter and cost tracking
                        rate_limiter.reset()
                        stats = analyzer.reset_tracking()
                        st.success("All tracking has been reset!")
                        # Force a rerun to update all displays
                        st.rerun()
                    
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()