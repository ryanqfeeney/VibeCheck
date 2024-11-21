from datetime import datetime
import streamlit as st
from config.security_config import SecurityConfig

class RateLimiter:
    def __init__(self):
        if 'request_history' not in st.session_state:
            self.reset()

    def reset(self):
        """Reset the rate limit tracking"""
        st.session_state.request_history = {}

    def check_rate_limit(self, user_id: str) -> bool:
        now = datetime.now()
        
        # Get or initialize user's request history
        if user_id not in st.session_state.request_history:
            st.session_state.request_history[user_id] = []
        
        # Get recent requests within time window
        recent_requests = [
            t for t in st.session_state.request_history[user_id]
            if (now - t).seconds < SecurityConfig.RATE_LIMIT_PERIOD
        ]
        
        # Update history with only recent requests
        st.session_state.request_history[user_id] = recent_requests
        
        # Check if user has exceeded limit
        if len(recent_requests) >= SecurityConfig.MAX_REQUESTS_PER_PERIOD:
            wait_time = SecurityConfig.RATE_LIMIT_PERIOD - (now - recent_requests[0]).seconds
            st.warning(f"Please wait {wait_time} seconds before making another request.")
            return False
        
        # Add current request timestamp
        st.session_state.request_history[user_id].append(now)
        return True