"""
Notification System for Toast Notifications
"""

import streamlit as st
import time

class NotificationSystem:
    """Toast notification system"""
    
    @staticmethod
    def toast_success(message: str):
        st.toast(f"✅ {message}", icon="✅")
    
    @staticmethod
    def toast_error(message: str):
        st.toast(f"❌ {message}", icon="❌")
    
    @staticmethod
    def toast_warning(message: str):
        st.toast(f"⚠️ {message}", icon="⚠️")
    
    @staticmethod
    def toast_info(message: str):
        st.toast(f"ℹ️ {message}", icon="ℹ️")

# Global notification instance
notifications = NotificationSystem()

