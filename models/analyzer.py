import os
from typing import Optional, Tuple
from langchain_community.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from utils.validators import sanitize_text
from config.security_config import SecurityConfig
import streamlit as st
from datetime import datetime, date
from decimal import Decimal

class VibeAnalyzer:
    def __init__(self):
        self._validate_api_key()
        self._initialize_cost_tracking()

    def _initialize_cost_tracking(self):
        today = date.today()
        if ('cost_reset_date' not in st.session_state or 
            st.session_state.cost_reset_date < today):
            st.session_state.update({
                'total_cost': Decimal('0.0'),
                'cost_reset_date': today,
                'request_count': 0
            })

    def _validate_api_key(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or not api_key.startswith('sk-'):
            raise ValueError("Invalid API key configuration")
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            openai_api_key=api_key
        )

    def analyze_vibe(self, text: str, context: Optional[str] = None, 
                    specific_questions: Optional[str] = None) -> Tuple[Optional[str], int, float, dict]:
        # Cost limit check
        max_cost = Decimal(str(SecurityConfig.MAX_DAILY_COST))
        current_cost = Decimal(str(st.session_state.total_cost))

        if current_cost >= max_cost:
            return None, 0, 0, {"error": f"Daily cost limit of ${max_cost:.6f} exceeded"}

        # Sanitize inputs
        text = sanitize_text(text)
        context = sanitize_text(context) if context else None
        specific_questions = sanitize_text(specific_questions) if specific_questions else None

        # Build a more detailed prompt
        prompt = """Analyze this text's communication dynamics and emotional subtext:

        1. Overall Tone & Atmosphere:
           - Primary emotional undertone
           - Communication style (formal/casual/etc.)
           - Hidden implications or subtext

        2. Key Dynamics:
           - Power dynamics or relationships
           - Emotional states of participants
           - Unspoken intentions or needs

        3. Notable Patterns:
           - Communication effectiveness
           - Potential misunderstandings
           - Suggestions for clarity (if needed)

        Keep the analysis concise but insightful."""

        if context:
            prompt += f"\n\nContext for this interaction: {context}"
        if specific_questions:
            prompt += f"\n\nSpecific areas to address: {specific_questions}"
        prompt += f"\n\nText to analyze: {text}"

        try:
            with get_openai_callback() as cb:
                response = self.llm.predict(prompt)
                request_cost = Decimal(str(cb.total_cost))
                
                # Update tracking
                st.session_state.total_cost += request_cost
                st.session_state.request_count += 1

                # Return all necessary data
                stats = {
                    "tokens": cb.total_tokens,
                    "request_cost": float(request_cost),
                    "total_cost": float(st.session_state.total_cost),
                    "request_count": st.session_state.request_count,
                    "max_cost": float(max_cost)
                }
                
                return response, cb.total_tokens, float(request_cost), stats

        except Exception as e:
            return None, 0, 0, {"error": str(e)}

    def reset_tracking(self) -> dict:
        """Reset all cost tracking and return new stats"""
        st.session_state.update({
            'total_cost': Decimal('0.0'),
            'cost_reset_date': date.today(),
            'request_count': 0
        })
        return {
            "tokens": 0,
            "request_cost": 0.0,
            "total_cost": 0.0,
            "request_count": 0,
            "max_cost": float(SecurityConfig.MAX_DAILY_COST)
        }