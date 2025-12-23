"""
Ti Tans Bank - Professional Banking Portal
Refactored with Progressive KYC Flow, Enhanced Status Tracking, and Integrated Admin/Audit
"""

import streamlit as st
import os
import shutil
from datetime import date, datetime
from pathlib import Path
import uuid
import json

# Import database modules
from database_config import db
from db_helpers import (
    create_user, authenticate_user, create_customer, create_kyc_application,
    save_document, get_customer_kyc_status, get_customer_documents,
    get_customer_by_user_id, create_notification, log_audit,
    update_customer_kyc, get_customer_by_email_or_phone, check_application_status
)

# Import custom modules
from styling import get_banking_css
from ocr_engine import ocr_engine
from notifications import notifications
from admin_dashboard import AdminDashboard
from audit_reports import AuditReports
from kyc_validator import perform_kyc_validation
from ai_kyc_validator import perform_advanced_kyc_validation
import pandas as pd
from io import BytesIO
from ai_kyc_validator import perform_advanced_kyc_validation
import pandas as pd
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Ti Tans Bank | Professional Banking", 
    page_icon="🏦", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATA STORAGE SETUP ---
DOCUMENTS_DIR = Path("submitted_data/documents")
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# --- SESSION STATE INITIALIZATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.customer = None
    st.session_state.view = "Landing"
    st.session_state.first_login = False
    st.session_state.admin_mode = False

# --- APPLY PROFESSIONAL BANKING STYLES ---
st.markdown(f"<style>{get_banking_css()}</style>", unsafe_allow_html=True)

# Set page-specific background based on current view
def set_page_background(view_name):
    """Set page-specific background styling"""
    page_map = {
        "Landing": "landing",
        "Login": "login",
        "Register": "register",
        "Admin": "admin",
        "AdminLogin": "admin",
        "CustomerManagement": "admin",
        "StatusCheck": "status",
        "Dashboard": "dashboard",
        "KYC Portal": "kyc"
    }
    page_class = page_map.get(view_name, "landing")
    st.markdown(f"""
        <script>
            document.querySelector('.stApp').setAttribute('data-page', '{page_class}');
        </script>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION CHECK ---
@st.cache_resource
def init_database():
    """Initialize database connection"""
    try:
        db.create_connection_pool()
        return db.test_connection()
    except Exception as e:
        return False

db_connected = init_database()

# --- NAVIGATION HELPER ---
def change_view(v):
    st.session_state.view = v
    st.rerun()

# --- WEBCAM HELPER WITH FALLBACK ---
def handle_webcam_capture():
    """Handle webcam capture with fallback"""
    try:
        # Try camera input
        camera_photo = st.camera_input(
            "Take a live photo*",
            help="Position your face in the frame. If camera doesn't work, use 'Upload Photo' option.",
            key="camera_capture"
        )
        return camera_photo
    except Exception as e:
        st.warning(f"⚠️ Camera not available: {str(e)}")
        st.info("💡 Please use the 'Upload Photo' option instead.")
        return None

# --- HELPER FUNCTION FOR STATUS DISPLAY ---
def _display_application_details(result):
    """Helper function to display application details"""
    st.markdown("---")
    
    # Application Details
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📋 Application Details")
        st.write(f"**Application ID:** `{result.get('application_id', 'N/A')}`")
        st.write(f"**Customer Name:** {result.get('full_name', 'N/A')}")
        st.write(f"**Email:** {result.get('email', 'N/A')}")
        st.write(f"**Phone:** {result.get('phone_number', 'N/A')}")
        st.write(f"**PAN:** {result.get('pan_card', 'N/A')}")
        st.write(f"**Aadhar:** {result.get('aadhar_no', 'N/A')}")
    with col2:
        st.markdown("### 📊 Status Information")
        status = result.get('application_status', 'N/A').replace('_', ' ').title()
        kyc_status = result.get('kyc_status', 'N/A')
        
        # Extract KYC score from notes if available
        kyc_score = "N/A"
        notes = result.get('notes', '')
        if notes and 'Overall Score:' in notes:
            try:
                score_line = [line for line in notes.split('\n') if 'Overall Score:' in line]
                if score_line:
                    kyc_score = score_line[0].split('Overall Score:')[1].split('%')[0].strip() + '%'
            except:
                pass
        
        st.write(f"**KYC Status:** {kyc_status}")
        st.write(f"**KYC Validation Score:** {kyc_score}")
        st.write(f"**Application Status:** {status}")
        st.write(f"**Submitted:** {result.get('submission_date', 'N/A')}")
        if result.get('verification_date'):
            st.write(f"**Verified:** {result.get('verification_date')}")
        if result.get('rejection_reason'):
            st.error(f"**Rejection Reason:** {result.get('rejection_reason')}")
        
        # Show validation details if available
        if notes and 'AUTO-VALIDATION RESULTS' in notes:
            with st.expander("📊 View Validation Details"):
                st.code(notes)
    
    # Document Verification Status
    if result.get('application_id'):
        st.markdown("---")
        st.markdown("### 📄 Document Verification Status")
        
        # Get all documents - prioritize showing rejected ones first, then by most recent update
        doc_query = """
            SELECT document_type, document_name, verification_status, 
                   verification_notes, created_at, verified_at, document_id
            FROM documents
            WHERE application_id = %s
            ORDER BY 
                CASE LOWER(COALESCE(verification_status, 'pending'))
                    WHEN 'rejected' THEN 1
                    WHEN 'pending' THEN 2
                    WHEN 'verified' THEN 3
                    ELSE 4
                END,
                COALESCE(verified_at, created_at) DESC,
                created_at DESC
        """
        documents = db.execute_query(doc_query, (result['application_id'],))
        
        if documents:
            # Group by document type and show the most relevant status
            # Strategy: Collect all rejected docs per type, then pick latest rejected OR latest non-rejected
            doc_by_type = {}
            rejected_docs_by_type = {}
            
            # First pass: collect all documents, prioritizing rejected ones
            for doc in documents:
                doc_type_key = doc['document_type']
                doc_status = str(doc.get('verification_status', 'pending')).lower().strip()
                
                # Track rejected documents separately
                if doc_status == 'rejected':
                    if doc_type_key not in rejected_docs_by_type:
                        rejected_docs_by_type[doc_type_key] = []
                    rejected_docs_by_type[doc_type_key].append(doc)
                
                # For non-rejected, track the latest
                if doc_type_key not in doc_by_type:
                    if doc_status != 'rejected':
                        doc_by_type[doc_type_key] = doc
                else:
                    if doc_status != 'rejected':
                        existing = doc_by_type[doc_type_key]
                        existing_date = existing.get('verified_at') or existing.get('created_at')
                        current_date = doc.get('verified_at') or doc.get('created_at')
                        if current_date and existing_date and current_date > existing_date:
                            doc_by_type[doc_type_key] = doc
                        elif current_date and not existing_date:
                            doc_by_type[doc_type_key] = doc
            
            # Second pass: For each type, use latest rejected if available, otherwise use latest non-rejected
            final_docs = {}
            for doc_type_key in set(list(doc_by_type.keys()) + list(rejected_docs_by_type.keys())):
                if doc_type_key in rejected_docs_by_type:
                    # Get the most recent rejected document
                    rejected_list = rejected_docs_by_type[doc_type_key]
                    latest_rejected = rejected_list[0]  # Already sorted by ORDER BY, first is most recent
                    for rejected_doc in rejected_list[1:]:
                        existing_date = latest_rejected.get('verified_at') or latest_rejected.get('created_at')
                        current_date = rejected_doc.get('verified_at') or rejected_doc.get('created_at')
                        if current_date and existing_date and current_date > existing_date:
                            latest_rejected = rejected_doc
                        elif current_date and not existing_date:
                            latest_rejected = rejected_doc
                    final_docs[doc_type_key] = latest_rejected
                elif doc_type_key in doc_by_type:
                    final_docs[doc_type_key] = doc_by_type[doc_type_key]
            
            doc_by_type = final_docs
            
            # Display documents
            for doc_type_key, doc in doc_by_type.items():
                doc_type = doc['document_type'].replace('_', ' ').title()
                doc_status_raw = doc.get('verification_status', 'pending')
                
                # Normalize status (handle case sensitivity and null values)
                if doc_status_raw:
                    doc_status_lower = str(doc_status_raw).lower().strip()
                    if doc_status_lower == 'verified':
                        doc_status_display = 'Verified'
                    elif doc_status_lower == 'rejected':
                        doc_status_display = 'Rejected'
                    elif doc_status_lower == 'pending':
                        doc_status_display = 'Pending'
                    else:
                        doc_status_display = str(doc_status_raw).title()
                else:
                    doc_status_display = 'Pending'
                
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{doc_type}**")
                    st.caption(doc['document_name'])
                with col2:
                    if doc_status_display == 'Verified':
                        st.success(f"✅ {doc_status_display}")
                    elif doc_status_display == 'Rejected':
                        st.error(f"❌ {doc_status_display}")
                    else:
                        st.warning(f"⏳ {doc_status_display}")
                    
                    # Show verification notes
                    if doc.get('verification_notes'):
                        notes = str(doc['verification_notes'])
                        # Check if this is a rejection note
                        if doc_status_display == 'Rejected' or 'rejected' in notes.lower() or 'reject' in notes.lower():
                            # Extract rejection reason if available
                            if 'Reason:' in notes:
                                try:
                                    reason = notes.split('Reason:')[1].split('.')[0].strip()
                                    if reason:
                                        st.error(f"**Rejection Reason:** {reason}")
                                    else:
                                        st.caption(f"Note: {notes}")
                                except:
                                    st.caption(f"Note: {notes}")
                            else:
                                st.caption(f"Note: {notes}")
                        else:
                            st.caption(f"Note: {notes}")
                with col3:
                    upload_date = doc['created_at'].strftime('%Y-%m-%d') if doc.get('created_at') else 'N/A'
                    verify_date = doc['verified_at'].strftime('%Y-%m-%d') if doc.get('verified_at') else None
                    if verify_date:
                        st.caption(f"Uploaded: {upload_date}")
                        st.caption(f"Verified: {verify_date}")
                    else:
                        st.caption(f"Uploaded: {upload_date}")
                
                st.markdown("---")
            
            # Summary - Calculate from displayed documents (grouped by type, case-insensitive)
            total_docs = len(doc_by_type)
            verified_docs = 0
            rejected_docs = 0
            pending_docs = 0
            
            for d in doc_by_type.values():
                status = str(d.get('verification_status', 'pending')).lower().strip()
                if status == 'verified':
                    verified_docs += 1
                elif status == 'rejected':
                    rejected_docs += 1
                else:
                    pending_docs += 1
            
            st.markdown("### 📈 Document Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Documents", total_docs)
            with col2:
                st.metric("Approved", verified_docs, delta=f"{verified_docs}/{total_docs}" if total_docs > 0 else None)
            with col3:
                st.metric("Pending", pending_docs)
            with col4:
                st.metric("Rejected", rejected_docs)
        else:
            st.info("No documents uploaded for this application yet.")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <div style='display: flex; align-items: center; justify-content: center; gap: 1rem;'>
                <div class='ti-tans-logo' style='width: 60px; height: 60px; background: rgba(15, 23, 42, 0.8); border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4), 0 0 1px rgba(6, 182, 212, 0.6); border: 1px solid rgba(6, 182, 212, 0.3); position: relative;'>
                    <svg width="45" height="45" viewBox="0 0 45 45" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <filter id="shadow-filter-small">
                                <feGaussianBlur in="SourceAlpha" stdDeviation="1.5"/>
                                <feOffset dx="2" dy="2" result="offsetblur"/>
                                <feComponentTransfer>
                                    <feFuncA type="linear" slope="0.5"/>
                                </feComponentTransfer>
                                <feMerge>
                                    <feMergeNode/>
                                    <feMergeNode in="SourceGraphic"/>
                                </feMerge>
                            </filter>
                        </defs>
                        <!-- Shadow T (behind main T) -->
                        <g opacity="0.4">
                            <rect x="19.5" y="10" width="10" height="32" rx="2" fill="#06b6d4"/>
                            <path d="M 7 10 Q 22.5 5 38 10 L 38 20 Q 22.5 15 7 20 Z" fill="#06b6d4"/>
                        </g>
                        <!-- Main T (on top) -->
                        <g filter="url(#shadow-filter-small)">
                            <rect x="17.5" y="8" width="10" height="32" rx="2" fill="#06b6d4"/>
                            <path d="M 5 8 Q 22.5 3 40 8 L 40 18 Q 22.5 13 5 18 Z" fill="#06b6d4"/>
                        </g>
                    </svg>
                </div>
                <div>
                    <h1 style='color: #ffffff; font-size: 2rem; font-weight: 800; margin: 0; text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);'>TI TANS</h1>
                    <p style='color: #06b6d4; font-size: 0.9rem; margin: 0.5rem 0 0 0; text-shadow: 0 0 5px rgba(6, 182, 212, 0.3);'>Professional Banking</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Database status
    if db_connected:
        st.success("✅ Database Connected")
    else:
        st.error("❌ Database Offline")
    
    st.markdown("---")
    
    # Navigation
    if st.button("🏠 Home", use_container_width=True):
        change_view("Landing")
    
    if not st.session_state.authenticated:
        if st.button("🔐 Login", use_container_width=True):
            change_view("Login")
        if st.button("✨ Open Account", use_container_width=True):
            change_view("Register")
    else:
        st.success(f"👤 {st.session_state.user['username']}")
        
        if st.button("📋 My Dashboard", use_container_width=True):
            change_view("Dashboard")
        
        if st.button("📄 Complete KYC", use_container_width=True):
            change_view("KYC Portal")
        
        if st.button("📁 My Documents", use_container_width=True):
            change_view("Documents")
        
        # Admin Mode Toggle
        if st.session_state.user.get('role') == 'admin':
            st.markdown("---")
            admin_mode = st.checkbox("🔐 Admin Mode", value=st.session_state.admin_mode)
            st.session_state.admin_mode = admin_mode
            
            if admin_mode:
                if st.button("📊 Admin Dashboard", use_container_width=True):
                    change_view("Admin")
                if st.button("📈 Audit Reports", use_container_width=True):
                    change_view("AuditReports")
        
        if st.button("🚪 Logout", use_container_width=True):
            log_audit(st.session_state.user['user_id'], 'logout', 'user', 
                     st.session_state.user['user_id'], "User logged out")
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.customer = None
            st.session_state.admin_mode = False
            change_view("Landing")
    
    st.markdown("---")
    if st.button("📊 Check Status", use_container_width=True):
        change_view("StatusCheck")
    
    # Admin Access (Always visible, requires credentials)
    st.markdown("---")
    if st.button("🔐 Admin", use_container_width=True):
        # If user is logged in, logout first
        if st.session_state.get('authenticated') and st.session_state.get('user'):
            # Logout user
            user_id = st.session_state.user.get('user_id')
            if user_id:
                try:
                    log_audit(user_id, 'logout', 'user', user_id, "User logged out before admin access")
                except:
                    pass
            
            # Clear user session
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.customer = None
            st.session_state.admin_mode = False
            
            # Show popup about opening in new tab
            st.warning("""
            ⚠️ **Admin Access Notice**
            
            **You have been logged out from your user account.**
            
            For better security and to keep your user session active, we recommend opening the Admin page in a new tab:
            
            **Option 1:** Right-click on "Admin" button → Select "Open in new tab"  
            **Option 2:** Use Ctrl+Click (Windows) or Cmd+Click (Mac) on the "Admin" button  
            **Option 3:** Copy the URL and open it in a new tab manually
            
            This ensures your user session remains active in the original tab while you access the admin panel.
            """)
            
            # Add informational note
            st.info("💡 **Tip:** If you want to keep your user session, open the Admin page in a new tab before clicking the Admin button.")
        
        # Navigate to admin login
        change_view("AdminLogin")
        st.rerun()
    
    st.markdown("---")
    st.info("🔒 Secure 256-bit Encryption")
    st.caption("📞 1-800-TITANS")
    st.caption("📧 support@titansbank.com")

# --- LANDING PAGE ---
if st.session_state.view == "Landing":
    set_page_background("Landing")
    st.markdown("""
        <div class='bank-header-main'>
            <div style='display: flex; align-items: center; justify-content: center; gap: 1.5rem; margin-bottom: 1rem;'>
                <div class='ti-tans-logo-main' style='width: 120px; height: 120px; background: rgba(15, 23, 42, 0.8); border-radius: 24px; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), 0 0 1px rgba(6, 182, 212, 0.6); position: relative; overflow: hidden; border: 1px solid rgba(6, 182, 212, 0.3);'>
                    <div style='position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(6, 182, 212, 0.2) 0%, transparent 70%); animation: shimmer 3s infinite;'></div>
                    <svg width="90" height="90" viewBox="0 0 90 90" xmlns="http://www.w3.org/2000/svg" style='position: relative; z-index: 1;'>
                        <defs>
                            <filter id="shadow-filter-large">
                                <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
                                <feOffset dx="3" dy="3" result="offsetblur"/>
                                <feComponentTransfer>
                                    <feFuncA type="linear" slope="0.6"/>
                                </feComponentTransfer>
                                <feMerge>
                                    <feMergeNode/>
                                    <feMergeNode in="SourceGraphic"/>
                                </feMerge>
                            </filter>
                        </defs>
                        <!-- Shadow T (behind main T, visible) -->
                        <g opacity="0.5">
                            <rect x="37" y="14" width="20" height="70" rx="3" fill="#06b6d4"/>
                            <path d="M 12 14 Q 45 7 78 14 L 78 30 Q 45 23 12 30 Z" fill="#06b6d4"/>
                        </g>
                        <!-- Main T (on top with glow) -->
                        <g filter="url(#shadow-filter-large)" style='filter: drop-shadow(0 0 15px rgba(6, 182, 212, 0.8));'>
                            <rect x="35" y="12" width="20" height="70" rx="3" fill="#06b6d4"/>
                            <path d="M 10 12 Q 45 5 80 12 L 80 28 Q 45 21 10 28 Z" fill="#06b6d4"/>
                        </g>
                    </svg>
                </div>
            </div>
            <h1 class='bank-logo'>TI TANS BANK</h1>
            <p class='bank-tagline'>Experience Banking Reimagined | Trusted by Millions</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Hero Banner with CTA
    st.markdown("---")
    hero_col1, hero_col2 = st.columns([2, 1])
    with hero_col1:
        st.markdown("""
            <div style='padding: 2rem 0;'>
                <h2 style='color: #ffffff; font-size: 2.5rem; font-weight: 900; margin-bottom: 1rem; text-shadow: 0 0 20px rgba(6, 182, 212, 0.3);'>
                    Your Trusted Banking Partner
                </h2>
                <p style='color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem; line-height: 1.6;'>
                    Experience seamless banking with cutting-edge technology, personalized service, and unmatched security.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("✨ Open Account Now", use_container_width=True, type="primary"):
            change_view("Register")
    with hero_col2:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <div style='font-size: 4rem; filter: drop-shadow(0 0 15px rgba(6, 182, 212, 0.5));'>🏦</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Services Section with Glassmorphism
    st.markdown("### 🎯 Our Services")
    st.markdown("<p style='color: #94a3b8; margin-bottom: 2rem;'>Comprehensive banking solutions tailored for you</p>", unsafe_allow_html=True)
    
    services = [
        ("🏦", "Personal Banking", "Savings, Current & More", "#06b6d4"),
        ("💳", "Credit Cards", "Rewards & Cashback", "#06b6d4"),
        ("📈", "Investments", "Mutual Funds & Stocks", "#06b6d4"),
        ("🏠", "Loans", "Home, Personal & Business", "#06b6d4"),
    ]
    
    service_cols = st.columns(4)
    for i, (icon, title, desc, color) in enumerate(services):
        with service_cols[i]:
            st.markdown(f"""
                <div class='service-card'>
                    <div class='service-icon' style='font-size: 3.5rem; margin-bottom: 1rem;'>{icon}</div>
                    <h3 style='color: #ffffff; font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem;'>{title}</h3>
                    <p style='color: #94a3b8; font-size: 0.95rem;'>{desc}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Statistics Section with Dark Background and Glowing Numbers
    st.markdown("""
        <div class='stats-section'>
            <h2 style='color: #ffffff; font-size: 2.5rem; font-weight: 900; text-align: center; margin-bottom: 3rem; text-shadow: 0 0 20px rgba(6, 182, 212, 0.3);'>
                The Ti Tans Advantage
            </h2>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; text-align: center;'>
                <div>
                    <div class='stat-number'>5M+</div>
                    <div class='stat-label'>Active Customers</div>
                </div>
                <div>
                    <div class='stat-number'>2,500+</div>
                    <div class='stat-label'>Global Branches</div>
                </div>
                <div>
                    <div class='stat-number'>4.9★</div>
                    <div class='stat-label'>App Rating</div>
                </div>
                <div>
                    <div class='stat-number'>24/7</div>
                    <div class='stat-label'>Expert Support</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 3. Another spacer after the stats
    st.markdown("<br><br>", unsafe_allow_html=True)
    


    # Footer
    st.markdown("""
        <div class='bank-footer'>
            <p style='font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;'>Ti Tans Bank - Banking Made Beautiful</p>
            <div class='footer-links'>
                <a href='#' class='footer-link'>Privacy Policy</a>
                <a href='#' class='footer-link'>Terms & Conditions</a>
                <a href='#' class='footer-link'>About Us</a>
                <a href='#' class='footer-link'>Contact</a>
            </div>
            <p style='margin-top: 1.5rem; color: #64748b;'>© 2025 Ti Tans Bank. All Rights Reserved</p>
        </div>
    """, unsafe_allow_html=True)

# --- REGISTRATION PAGE (Initial Entry - Progressive KYC Step 1) ---
elif st.session_state.view == "Register":
    set_page_background("Register")
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2.5rem;'>Open Your Account</h1>
            <p class='bank-tagline'>Step 1: Create Your Account</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Two column layout: Form on left, Customer image on right
    reg_col1, reg_col2 = st.columns([2, 1])
    
    with reg_col1:
        with st.container():
            st.markdown("<div class='form-container'>", unsafe_allow_html=True)
            
            st.info("ℹ️ **Registration Process:** After creating your account, you'll complete KYC verification on your first login.")
            
            with st.form("register_form", clear_on_submit=False):
                st.markdown("### 👤 Personal Information")
                st.markdown("<p style='color: #06b6d4; font-size: 0.9rem;'>* Indicates mandatory fields</p>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("First Name*", placeholder="Enter your first name")
                    last_name = st.text_input("Last Name*", placeholder="Enter your last name")
                    email = st.text_input("Email Address*", placeholder="example@email.com")
                    
                    # Phone number with country code
                    phone_col1, phone_col2 = st.columns([1, 3])
                    with phone_col1:
                        country_code = st.selectbox("Country Code*", ["+91", "+1", "+44", "+61", "+971", "+86", "+65"], index=0, help="Select your country code")
                    with phone_col2:
                        phone = st.text_input("Phone Number*", placeholder="9876543210", max_chars=10, help="Enter 10-digit phone number")
                with col2:
                    dob = st.date_input("Date of Birth*", min_value=date(1920, 1, 1), max_value=date.today())
                    gender = st.selectbox("Gender*", ["", "Male", "Female", "Other", "Prefer not to say"])
                    marital_status = st.selectbox("Marital Status*", ["", "Single", "Married", "Divorced", "Widowed"])
                    age = st.number_input("Age*", min_value=18, max_value=120, value=25)
                
                st.markdown("### 💼 Employment & Income Details")
                col1, col2, col3 = st.columns(3)
                with col1:
                    occupation = st.text_input("Occupation*", placeholder="e.g., Software Engineer")
                with col2:
                    salary = st.number_input("Monthly Salary (₹)*", min_value=0, value=50000, step=1000)
                with col3:
                    annual_income = st.number_input("Annual Income (₹)*", min_value=0, value=600000, step=10000)
                
                st.markdown("### 🔐 Account Credentials")
                col1, col2 = st.columns(2)
                with col1:
                    username = st.text_input("Choose Username*", placeholder="Choose a unique username")
                    password = st.text_input("Create Password*", type="password", help="Minimum 8 characters")
                with col2:
                    confirm_password = st.text_input("Confirm Password*", type="password")
                
                st.markdown("### 📍 Address Details")
                address = st.text_area("Residential Address*", placeholder="House No, Street, Landmark, City, State")
                col1, col2 = st.columns(2)
                with col1:
                    city = st.text_input("City/Town*", placeholder="Enter your city")
                with col2:
                    pincode = st.text_input("Pincode*", placeholder="123456", max_chars=6)
                
                consent = st.checkbox("I hereby declare that the information provided is true and correct. I agree to the Terms & Conditions and Privacy Policy.*")
                
                submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if submitted:
                    # Validation - Initialize missing_fields list
                    missing_fields = []
                    if not first_name: 
                        missing_fields.append("First Name")
                    if not last_name: 
                        missing_fields.append("Last Name")
                    if not email: 
                        missing_fields.append("Email")
                    if not phone: 
                        missing_fields.append("Phone Number")
                    if not gender or gender == "": 
                        missing_fields.append("Gender")
                    if not marital_status or marital_status == "": 
                        missing_fields.append("Marital Status")
                    if not occupation: 
                        missing_fields.append("Occupation")
                    if not salary or salary == 0: 
                        missing_fields.append("Monthly Salary")
                    if not annual_income or annual_income == 0: 
                        missing_fields.append("Annual Income")
                    if not username: 
                        missing_fields.append("Username")
                    if not password: 
                        missing_fields.append("Password")
                    if not address: 
                        missing_fields.append("Address")
                    if not city: 
                        missing_fields.append("City")
                    if not pincode: 
                        missing_fields.append("Pincode")
                    if not consent: 
                        missing_fields.append("Terms & Conditions consent")
                    
                    # Validate phone number format (10 digits)
                    phone_valid = True
                    phone_clean = ""
                    if phone:
                        # Remove spaces and non-digits
                        phone_clean = ''.join(filter(str.isdigit, phone))
                        if len(phone_clean) != 10:
                            phone_valid = False
                            st.error("❌ Phone number must be exactly 10 digits.")
                        elif len(phone_clean) == 10:
                            phone_valid = True
                    
                    # Validate password length
                    password_valid = True
                    if password and len(password) < 8:
                        password_valid = False
                        st.error("❌ Password must be at least 8 characters long.")
                    
                    if missing_fields:
                        st.error(f"❌ **Please fill all mandatory fields:**\n\n" + "\n".join([f"• {field}" for field in missing_fields]))
                    elif not phone_valid:
                        pass  # Error already shown above
                    elif not password_valid:
                        pass  # Error already shown above
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match. Please re-enter your password.")
                    elif not db_connected:
                        st.error("❌ Database not connected. Please check your database connection.")
                    else:
                        try:
                            # Check for duplicate accounts BEFORE creating
                            from db_helpers import check_username_exists, check_email_exists, check_phone_exists
                            
                            duplicate_found = False
                            
                            # Check username
                            if check_username_exists(username):
                                st.error(f"❌ **Username already exists!**\n\nThe username '{username}' is already taken. Please choose a different username.")
                                duplicate_found = True
                            
                            # Check email
                            if check_email_exists(email):
                                st.error(f"❌ **Email already registered!**\n\nThe email '{email}' is already associated with an existing account. Please use a different email or login to your existing account.")
                                duplicate_found = True
                            
                            # Check phone number (with country code)
                            full_phone = f"{country_code} {phone_clean}" if phone_valid else phone
                            if check_phone_exists(full_phone):
                                st.error(f"❌ **Phone number already registered!**\n\nThe phone number '{full_phone}' is already associated with an existing account. Please use a different phone number or login to your existing account.")
                                duplicate_found = True
                            
                            if duplicate_found:
                                st.stop()
                            
                            # Create full name
                            full_name = f"{first_name} {last_name}".strip()
                            
                            # Create user account
                            user_id = create_user(username, email, password)
                            if user_id:
                                # Prepare customer data (KYC Status = 'Not Submitted')
                                # Use full phone with country code
                                full_phone_number = f"{country_code} {phone_clean}" if phone_valid else phone
                                
                                customer_data = {
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'full_name': full_name,
                                    'date_of_birth': dob,
                                    'gender': gender,
                                    'marital_status': marital_status,
                                    'age': int(age),
                                    'phone_number': full_phone_number,
                                    'address': address,
                                    'city_town': city,
                                    'pincode': pincode,
                                    'occupation': occupation,
                                    'salary': float(salary),
                                    'annual_income': float(annual_income),
                                    'kyc_status': 'Not Submitted'  # Initial status
                                }
                                
                                # Create customer profile
                                customer_id = create_customer(user_id, customer_data)
                                
                                if customer_id:
                                    notifications.toast_success(f"Account created successfully! Welcome {full_name}")
                                    st.balloons()
                                    st.success(f"✅ **Account Created Successfully!**\n\n**Next Steps:**\n1. Login with your credentials\n2. Complete KYC verification (Identity & Photo)\n3. Submit your application")
                                    st.info("💡 **Note:** KYC verification will be required on your first login.")
                                    change_view("Login")
                                else:
                                    st.error("❌ Failed to create customer profile. Please try again.")
                            else:
                                # Check if user exists
                                query = "SELECT username, email FROM users WHERE username = %s OR email = %s"
                                existing = db.execute_one(query, (username, email))
                                if existing:
                                    st.error(f"❌ **User already exists!** Username or email is already registered.")
                                else:
                                    st.error("❌ Registration failed. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            import traceback
                            with st.expander("View Error Details"):
                                st.code(traceback.format_exc())
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("⬅ Back to Home"):
            change_view("Landing")

# --- LOGIN PAGE ---
elif st.session_state.view == "Login":
    set_page_background("Login")
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2.5rem;'>Secure Login</h1>
            <p class='bank-tagline'>Access your banking portal</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 🔐 Login to Your Account")
            st.markdown("<p style='color: #ef4444; font-size: 0.9rem;'>* Indicates mandatory fields</p>", unsafe_allow_html=True)
            
            username = st.text_input("Username or Email*", placeholder="Enter your username or email")
            password = st.text_input("Password*", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            with col2:
                if st.form_submit_button("Forgot Password?", use_container_width=True):
                    st.info("📧 Password reset link will be sent to your registered email")
            
            if login_submit:
                if not username or not password:
                    st.error("❌ **Please enter both username/email and password**")
                elif not db_connected:
                    st.error("❌ **Database not connected.** Please check your database connection.")
                else:
                    try:
                        # Check if user exists first
                        check_query = "SELECT user_id, username, email FROM users WHERE username = %s OR email = %s"
                        user_exists = db.execute_one(check_query, (username, username))
                        
                        if not user_exists:
                            st.error(f"❌ **User does not exist!**\n\nNo account found with username/email: `{username}`\n\nPlease register first or check your credentials.")
                        else:
                            # Try authentication
                            user = authenticate_user(username, password)
                            if user:
                                # Get customer data
                                customer = get_customer_by_user_id(user['user_id'])
                                
                                st.session_state.authenticated = True
                                st.session_state.user = user
                                st.session_state.customer = customer
                                
                                # Check if first login and KYC not submitted
                                if customer and customer.get('kyc_status') == 'Not Submitted':
                                    st.session_state.first_login = True
                                
                                # Show success with user data
                                st.success("✅ **Login Successful!**")
                                notifications.toast_success(f"Welcome back, {user['username']}!")
                                
                                # Scroll to top using JavaScript (multiple methods for reliability)
                                st.markdown("""
                                    <script>
                                        // Scroll to top immediately
                                        window.scrollTo({top: 0, behavior: 'instant'});
                                        // Also try scrolling the main content area
                                        setTimeout(function() {
                                            window.scrollTo({top: 0, behavior: 'smooth'});
                                            document.querySelector('.main').scrollTop = 0;
                                        }, 100);
                                    </script>
                                """, unsafe_allow_html=True)
                                
                                # Display user information
                                if customer:
                                    st.markdown("---")
                                    st.markdown("### 👤 Your Profile")
                                    col1, col2 = st.columns([1, 2])
                                    with col1:
                                        if customer.get('photo_path') and os.path.exists(customer['photo_path']):
                                            st.image(customer['photo_path'], width=150)
                                        else:
                                            st.info("📷 No photo uploaded")
                                    with col2:
                                        st.write(f"**Name:** {customer.get('full_name', 'N/A')}")
                                        st.write(f"**Email:** {user.get('email', 'N/A')}")
                                        st.write(f"**Age:** {customer.get('age', 'N/A')}")
                                        st.write(f"**Occupation:** {customer.get('occupation', 'N/A')}")
                                    
                                    # Check KYC status
                                    if customer.get('kyc_status') == 'Not Submitted':
                                        st.warning("⚠️ **KYC Verification Required**\n\nPlease complete your KYC verification to activate your account.")
                                
                                st.balloons()
                                
                                # Redirect based on KYC status
                                if customer and customer.get('kyc_status') == 'Not Submitted':
                                    change_view("KYC Portal")
                                else:
                                    change_view("Dashboard")
                                
                                # Rerun to show new page (scroll to top already done above)
                                st.rerun()
                            else:
                                st.error(f"❌ **Incorrect credentials!**\n\nWrong password for user: `{username}`\n\nPlease check your password and try again.")
                    except Exception as e:
                        st.error(f"❌ **Login Error:** {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**Don't have an account?** [Register here](#)")
        if st.button("⬅ Back to Home"):
            change_view("Landing")

# --- POST-LOGIN KYC PORTAL (Progressive KYC Step 2) ---
elif st.session_state.view == "KYC Portal":
    if not st.session_state.authenticated:
        change_view("Login")
        st.stop()
    
    # Scroll to top when KYC Portal loads - improved script
    st.markdown("""
        <script>
            (function() {
                // Immediate scroll
                window.scrollTo(0, 0);
                document.documentElement.scrollTop = 0;
                document.body.scrollTop = 0;
                
                // Force scroll after a short delay
                setTimeout(function() {
                    window.scrollTo({top: 0, left: 0, behavior: 'instant'});
                    document.documentElement.scrollTop = 0;
                    document.body.scrollTop = 0;
                }, 50);
                
                // Additional scroll after page fully loads
                window.addEventListener('load', function() {
                    window.scrollTo({top: 0, left: 0, behavior: 'instant'});
                    document.documentElement.scrollTop = 0;
                    document.body.scrollTop = 0;
                });
            })();
        </script>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2rem;'>Complete KYC Verification</h1>
            <p class='bank-tagline'>Step 2: Identity & Document Verification</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.customer:
        st.error("❌ Customer profile not found. Please contact support.")
        change_view("Dashboard")
        st.stop()
    
    customer = st.session_state.customer
    customer_id = customer['customer_id']
    
    # Check if KYC is already submitted/approved/pending
    kyc_status = customer.get('kyc_status', 'Not Submitted')
    kyc_app_status = get_customer_kyc_status(customer_id)
    
    # If KYC is already submitted, approved, or under review, show status instead of form
    if kyc_status in ['Submitted', 'Approved', 'Under Review'] or (kyc_app_status and kyc_app_status.get('application_status') in ['submitted', 'approved', 'under_review']):
        st.markdown("---")
        
        # Get application details
        app_status = kyc_app_status.get('application_status', 'N/A') if kyc_app_status else 'N/A'
        app_id = kyc_app_status.get('application_id', 'N/A') if kyc_app_status else 'N/A'
        
        # Display status based on KYC status
        if kyc_status == 'Approved' or app_status == 'approved':
            st.success(f"""
            ## ✅ **KYC Verification Successful!**
            
            Your KYC has been **approved** and your account is fully active.
            
            **Application ID:** `{app_id}`
            **Status:** Approved
            **KYC Status:** {kyc_status}
            """)
            
            # Show validation score if available
            if kyc_app_status and kyc_app_status.get('notes'):
                notes = kyc_app_status.get('notes', '')
                if 'Overall Score:' in notes:
                    try:
                        score_line = [line for line in notes.split('\n') if 'Overall Score:' in line]
                        if score_line:
                            score = score_line[0].split('Overall Score:')[1].split('%')[0].strip()
                            st.info(f"**Validation Score:** {score}%")
                    except:
                        pass
            
            st.balloons()
            
        elif kyc_status == 'Submitted' or app_status in ['submitted', 'under_review']:
            st.warning(f"""
            ## 📄 **KYC Application Submitted**
            
            Your KYC application has been submitted and is currently **under review**.
            
            **Application ID:** `{app_id}`
            **Status:** {app_status.replace('_', ' ').title()}
            **KYC Status:** {kyc_status}
            
            You will be notified once the review is complete. Please check back later.
            """)
            
        elif kyc_status == 'Rejected' or app_status == 'rejected':
            # Get rejection reason from application
            rejection_reason = "Please review your documents and resubmit."
            if kyc_app_status and kyc_app_status.get('rejection_reason'):
                rejection_reason = kyc_app_status.get('rejection_reason')
            elif kyc_app_status and kyc_app_status.get('notes'):
                notes = kyc_app_status.get('notes', '')
                if 'Manually rejected by admin' in notes:
                    # Extract admin rejection reason
                    if 'Reason:' in notes:
                        rejection_reason = notes.split('Reason:')[1].split('\n')[0].strip()
            
            st.error(f"""
            ## ❌ **KYC Application Rejected**
            
            Your KYC application has been **rejected**. Please review the issues below and resubmit your documents.
            
            **Application ID:** `{app_id}`
            **Status:** Rejected
            **KYC Status:** {kyc_status}
            
            **Rejection Reason:**
            {rejection_reason}
            
            **Next Steps:**
            1. Review the rejection reason above
            2. Ensure all documents are clear and valid
            3. Make sure your photo matches the photo in your ID document
            4. Verify that you uploaded the correct document type (PAN or Aadhar)
            5. Click "Resubmit KYC" below to upload new documents
            """)
            
            if st.button("🔄 Resubmit KYC Documents", use_container_width=True, type="primary"):
                # Reset KYC status to allow resubmission
                try:
                    reset_query = "UPDATE customers SET kyc_status = 'Not Submitted' WHERE customer_id = %s"
                    db.execute_query(reset_query, (customer_id,), fetch=False)
                    # Clear old documents from session state to force new uploads
                    if 'identity_doc_kyc' in st.session_state:
                        st.session_state.identity_doc_kyc = None
                    if 'camera_photo_kyc' in st.session_state:
                        st.session_state.camera_photo_kyc = None
                    if 'uploaded_photo_kyc' in st.session_state:
                        st.session_state.uploaded_photo_kyc = None
                    if 'doc_type_kyc' in st.session_state:
                        st.session_state.doc_type_kyc = None
                    
                    # Scroll to top and navigate to KYC Portal
                    st.markdown("""
                        <script>
                            window.scrollTo({top: 0, behavior: 'instant'});
                        </script>
                    """, unsafe_allow_html=True)
                    change_view("KYC Portal")
                    st.rerun()
                except:
                    change_view("KYC Portal")
                    st.rerun()
        else:
            st.info(f"""
            ## ℹ️ **KYC Status: {kyc_status}**
            
            Your current KYC status is: **{kyc_status}**
            """)
        
        st.markdown("---")
        if st.button("⬅ Back to Dashboard", use_container_width=True):
            change_view("Dashboard")
        
        st.stop()  # Don't show the form if KYC is already submitted
    
    # If KYC is not submitted, show the form
    with st.container():
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        
        # Check for existing documents to see which ones need re-upload
        existing_documents = {}
        photo_rejected = False
        identity_rejected = False
        photo_verified = False
        identity_verified = False
        
        if kyc_app_status and kyc_app_status.get('application_id'):
            from db_helpers import get_customer_documents
            import uuid
            app_id = kyc_app_status.get('application_id')
            if app_id:
                try:
                    # Handle UUID conversion - app_id might already be UUID or string
                    if isinstance(app_id, uuid.UUID):
                        app_id_uuid = app_id
                    else:
                        app_id_uuid = uuid.UUID(str(app_id))
                    
                    docs = get_customer_documents(app_id_uuid)
                    for doc in docs:
                        doc_type = doc.get('document_type', '')
                        status = doc.get('verification_status', 'pending')
                        
                        if doc_type in ['photo', 'photo_optional']:
                            if status == 'rejected':
                                photo_rejected = True
                            elif status == 'verified':
                                photo_verified = True
                        elif doc_type == 'identity_proof':
                            if status == 'rejected':
                                identity_rejected = True
                            elif status == 'verified':
                                identity_verified = True
                        
                        existing_documents[doc_type] = {
                            'status': status,
                            'name': doc.get('document_name', ''),
                            'notes': doc.get('verification_notes', '')
                        }
                except Exception as e:
                    # Silently handle - treat as no existing documents
                    # Error is already logged in get_customer_documents function
                    pass
        
        st.info("ℹ️ **KYC Verification:** Complete identity verification and photo upload to activate your account.")
        
        # Photo selection - Always show upload options
        st.markdown("### 📸 Photo Identification (Mandatory)")
        st.info("📷 **Please provide a photo using either webcam OR file upload (one is required)**")
        
        # Initialize session state
        if 'camera_photo_kyc' not in st.session_state:
            st.session_state.camera_photo_kyc = None
        if 'uploaded_photo_kyc' not in st.session_state:
            st.session_state.uploaded_photo_kyc = None
        
        # Radio button to choose photo source
        photo_source = st.radio(
            "Choose photo source*",
            ["Webcam", "Upload from Device"],
            horizontal=True,
            key="photo_source_kyc"
        )
        
        # Track previous selection to clear other option when switching
        prev_photo_source = st.session_state.get('prev_photo_source_kyc', photo_source)
        if prev_photo_source != photo_source:
            # Selection changed - clear the other option
            if photo_source == "Webcam":
                st.session_state.uploaded_photo_kyc = None
            else:
                st.session_state.camera_photo_kyc = None
            st.session_state.prev_photo_source_kyc = photo_source
        else:
            st.session_state.prev_photo_source_kyc = photo_source
        
        user_photo = None
        
        # Conditionally show camera or file uploader based on radio selection
        if photo_source == "Webcam":
            # Webcam photo option
            camera_photo = st.camera_input(
                "Take a live photo*",
                help="Position your face in the frame. This is required for KYC verification.",
                key="camera_mandatory_kyc"
            )
            
            if camera_photo:
                st.session_state.camera_photo_kyc = camera_photo
                st.session_state.uploaded_photo_kyc = None  # Clear uploaded photo if webcam is used
                st.success("✅ Photo captured successfully")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.image(camera_photo, width=200, caption="Webcam Photo Preview")
                with col2:
                    if st.button("🗑️ Remove", key="remove_camera_kyc_outside"):
                        st.session_state.camera_photo_kyc = None
                        st.rerun()
            
            user_photo = st.session_state.camera_photo_kyc
        else:
            # File upload option
            uploaded_photo = st.file_uploader(
                "Upload photo from your device*",
                type=["jpg", "png", "jpeg"],
                help="Upload a clear photo of yourself (Max 5MB, JPG/PNG only). This is required for KYC verification.",
                key="mandatory_photo_upload_kyc"
            )
            
            if uploaded_photo:
                # Validate file size (5MB max)
                max_size = 5 * 1024 * 1024  # 5MB in bytes
                if uploaded_photo.size > max_size:
                    st.error(f"❌ File too large! Maximum size is 5MB. Your file is {uploaded_photo.size / (1024*1024):.2f}MB. Please upload a smaller file.")
                    st.session_state.uploaded_photo_kyc = None
                # Validate file type
                elif uploaded_photo.type not in ['image/jpeg', 'image/jpg', 'image/png']:
                    st.error(f"❌ Invalid file type! Only JPG and PNG images are allowed. Your file type: {uploaded_photo.type}")
                    st.session_state.uploaded_photo_kyc = None
                else:
                    st.session_state.uploaded_photo_kyc = uploaded_photo
                    st.session_state.camera_photo_kyc = None  # Clear webcam photo if upload is used
                    st.success(f"✅ File uploaded: {uploaded_photo.name} ({uploaded_photo.size / 1024:.1f} KB)")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.image(uploaded_photo, width=200, caption="Uploaded Photo Preview")
                    with col2:
                        if st.button("🗑️ Remove", key="remove_uploaded_photo_kyc"):
                            st.session_state.uploaded_photo_kyc = None
                            st.rerun()
            
            user_photo = st.session_state.uploaded_photo_kyc
        
        st.markdown("---")
        
        # Identity document upload - Always show upload option
        st.markdown("### 📄 Identity Verification (Mandatory)")
        st.markdown("<p style='color: #ef4444; font-size: 0.9rem;'>* Indicates mandatory fields</p>", unsafe_allow_html=True)

        # Initialize session state for identity document
        if 'identity_doc_kyc' not in st.session_state:
            st.session_state.identity_doc_kyc = None
        if 'doc_type_kyc' not in st.session_state:
            st.session_state.doc_type_kyc = ""

        doc_type = st.selectbox("Document Type*", ["", "Aadhar Card", "PAN Card", "Passport", "Voter ID"],
                               key="doc_type_select_kyc")
        if doc_type:
            st.session_state.doc_type_kyc = doc_type

        identity_doc = st.file_uploader(f"Upload {doc_type if doc_type else 'Identity Document'}*",
                                      type=["pdf", "jpg", "png", "jpeg"],
                                      help="Upload a clear scan of your identity document (Max 10MB, PDF/JPG/PNG only)",
                                      key="identity_doc_upload_kyc")

        if identity_doc:
            # Validate file size (10MB max for documents)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if identity_doc.size > max_size:
                st.error(f"❌ File too large! Maximum size is 10MB. Your file is {identity_doc.size / (1024*1024):.2f}MB. Please upload a smaller file.")
                st.session_state.identity_doc_kyc = None
            # Validate file type
            elif identity_doc.type not in ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']:
                st.error(f"❌ Invalid file type! Only PDF, JPG and PNG files are allowed. Your file type: {identity_doc.type}")
                st.session_state.identity_doc_kyc = None
            else:
                st.session_state.identity_doc_kyc = identity_doc
                st.success(f"✅ File uploaded: {identity_doc.name} ({identity_doc.size / 1024:.1f} KB)")
                col1, col2 = st.columns([3, 1])
                with col1:
                    if identity_doc.type.startswith('image/'):
                        st.image(identity_doc, width=300, caption="Document Preview")
                    else:
                        st.info(f"📄 PDF Document: {identity_doc.name}")
                with col2:
                    if st.button("🗑️ Remove", key="remove_identity_doc_kyc"):
                        st.session_state.identity_doc_kyc = None
                        st.rerun()

        # Use session state value (with safe access)
        identity_doc = st.session_state.get('identity_doc_kyc', None)
        doc_type = st.session_state.get('doc_type_kyc', '')

        st.markdown("---")
        
        with st.form("kyc_portal_form", clear_on_submit=False):
            
            st.markdown("### 📋 Additional Information (Optional)")
            col1, col2 = st.columns(2)
            with col1:
                pan_card = st.text_input("PAN Card Number", 
                                        value=customer.get('pan_card', '') if customer.get('pan_card') else '',
                                        placeholder="ABCDE1234F", 
                                        help="Optional but recommended")
                aadhar_no = st.text_input("Aadhar Number", 
                                         value=customer.get('aadhar_no', '') if customer.get('aadhar_no') else '',
                                         placeholder="1234 5678 9012", 
                                         help="Optional but recommended")
            with col2:
                nominee_name = st.text_input("Nominee Name", 
                                           value=customer.get('nominee_name', '') if customer.get('nominee_name') else '',
                                           placeholder="Enter nominee name",
                                           help="Optional")
                nominee_relation = st.selectbox("Nominee Relation", 
                                               ["", "Spouse", "Father", "Mother", "Son", "Daughter", "Brother", "Sister", "Other"],
                                               help="Optional")
            
            st.markdown("### 🔐 OTP Verification (Optional)")
            otp_verified = st.checkbox("I have verified my phone number with OTP", 
                                      value=customer.get('otp_verified', False) if customer.get('otp_verified') else False,
                                      help="Optional - Can be completed later")
            
            submitted = st.form_submit_button("Submit KYC Application", use_container_width=True, type="primary")
            
            if submitted:
                # Get current values from session state
                identity_doc = st.session_state.get('identity_doc_kyc')
                doc_type = st.session_state.get('doc_type_kyc', '')
                user_photo = st.session_state.get('camera_photo_kyc') or st.session_state.get('uploaded_photo_kyc')
                
                # Validation - always require both documents
                missing_fields = []
                if not doc_type or doc_type == "":
                    missing_fields.append("Document Type")
                if not identity_doc:
                    missing_fields.append("Identity Document")
                if not user_photo:
                    missing_fields.append("Photo (Webcam or Upload - Mandatory)")
                
                if missing_fields:
                    st.error(f"❌ **Please complete all mandatory fields:**\n\n" + "\n".join([f"• {field}" for field in missing_fields]))
                    if not user_photo:
                        st.warning("⚠️ **Photo required!** Please use either webcam or file upload above to provide a photo.")
                    if not identity_doc:
                        st.warning("⚠️ **Identity document required!** Please select document type and upload your identity document.")
                elif not db_connected:
                    st.error("❌ Database not connected.")
                else:
                    try:
                        # Check for duplicate PAN/Aadhar if provided
                        from db_helpers import check_pan_exists, check_aadhar_exists
                        
                        duplicate_found = False
                        
                        # Check PAN if provided
                        if pan_card and pan_card.strip():
                            pan_clean = pan_card.strip().upper()
                            if check_pan_exists(pan_clean):
                                st.error(f"❌ **PAN Card already registered!**\n\nThe PAN number '{pan_clean}' is already associated with an existing account. Please use a different PAN or contact support if this is your PAN.")
                                duplicate_found = True
                        
                        # Check Aadhar if provided
                        if aadhar_no and aadhar_no.strip():
                            aadhar_clean = ''.join(filter(str.isdigit, aadhar_no.strip()))
                            if len(aadhar_clean) == 12:
                                if check_aadhar_exists(aadhar_clean):
                                    st.error(f"❌ **Aadhar Number already registered!**\n\nThe Aadhar number '{aadhar_clean}' is already associated with an existing account. Please use a different Aadhar or contact support if this is your Aadhar.")
                                    duplicate_found = True
                            elif aadhar_clean:
                                st.warning(f"⚠️ Aadhar number should be 12 digits. You entered {len(aadhar_clean)} digits.")
                        
                        if duplicate_found:
                            st.stop()
                        
                        # Save photo
                        photo_path = None
                        if user_photo:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            # Handle both file upload and camera photo
                            if hasattr(user_photo, 'name') and user_photo.name:
                                file_ext = user_photo.name.split('.')[-1] if '.' in user_photo.name else 'jpg'
                            else:
                                file_ext = 'jpg'  # Camera photos default to jpg
                            photo_filename = f"photo_{timestamp}_{customer_id}.{file_ext}"
                            photo_path_full = DOCUMENTS_DIR / photo_filename
                            with open(photo_path_full, "wb") as f:
                                f.write(user_photo.getbuffer())
                            photo_path = str(photo_path_full)
                            
                            # Update customer with photo path
                            update_query = "UPDATE customers SET photo_path = %s WHERE customer_id = %s"
                            db.execute_query(update_query, (photo_path, customer_id), fetch=False)
                        
                        # OCR Verification on identity document
                        ocr_result_data = None
                        if identity_doc:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            temp_path = DOCUMENTS_DIR / f"temp_{timestamp}_{identity_doc.name}"
                            with open(temp_path, "wb") as f:
                                f.write(identity_doc.getbuffer())
                            
                            # Run OCR
                            with st.spinner("🔍 Verifying document with OCR..."):
                                ocr_result = ocr_engine.validate_document(
                                    str(temp_path), identity_doc.type, "identity_proof"
                                )
                                ocr_result_data = ocr_result.get('validation', {})
                            
                            validation = ocr_result.get('validation', {})
                            
                            if validation.get('is_valid', False):
                                st.success(f"✅ Document verified! Confidence: {validation.get('confidence', 0)}%")
                                notifications.toast_success("Document verified successfully!")
                            else:
                                missing = ", ".join(validation.get('missing_fields', []))
                                st.warning(f"⚠️ Document verification score: {validation.get('completeness_score', 0)}%")
                                if missing:
                                    st.info(f"Missing fields: {missing}")
                            
                            # Clean up temp file
                            if temp_path.exists():
                                temp_path.unlink()
                        
                        # Get previous application ID BEFORE creating new one (for copying verified documents)
                        prev_application_id = None
                        if kyc_app_status and kyc_app_status.get('application_id'):
                            prev_application_id = kyc_app_status.get('application_id')
                        
                        # Create KYC application
                        application_id = create_kyc_application(customer_id)
                        
                        if application_id:
                            # Save identity document
                            if identity_doc:
                                doc_ext = os.path.splitext(identity_doc.name)[1] or ".pdf"
                                doc_filename = f"identity_proof_{timestamp}{doc_ext}"
                                doc_folder = DOCUMENTS_DIR / f"{timestamp}_{customer.get('first_name', 'user')}_{customer.get('last_name', '')}"
                                doc_folder.mkdir(parents=True, exist_ok=True)
                                doc_path = doc_folder / doc_filename
                                with open(doc_path, "wb") as f:
                                    f.write(identity_doc.getbuffer())
                                save_document(application_id, 'identity_proof', identity_doc.name, 
                                            str(doc_path), identity_doc.size, identity_doc.type, ocr_result_data)
                            else:
                                # If no new identity document uploaded, check if there's a verified one from previous applications
                                if prev_application_id:
                                    try:
                                        # Get verified identity document from previous application (check all previous applications)
                                        prev_doc_query = """
                                            SELECT d.file_path, d.document_name, d.file_size, d.file_type, d.ocr_data
                                            FROM documents d
                                            INNER JOIN kyc_applications ka ON d.application_id = ka.application_id
                                            WHERE ka.customer_id = %s 
                                            AND d.document_type = 'identity_proof' 
                                            AND d.verification_status = 'verified'
                                            AND d.application_id != %s
                                            ORDER BY d.created_at DESC
                                            LIMIT 1
                                        """
                                        prev_doc = db.execute_one(prev_doc_query, (customer_id, application_id))
                                        
                                        if prev_doc and prev_doc.get('file_path') and os.path.exists(prev_doc.get('file_path')):
                                            # Copy the verified document to the new application
                                            prev_file_path = prev_doc.get('file_path')
                                            prev_doc_name = prev_doc.get('document_name', 'identity_proof')
                                            
                                            # Create a copy of the file for the new application
                                            doc_ext = os.path.splitext(prev_file_path)[1] or ".pdf"
                                            doc_filename = f"identity_proof_{timestamp}{doc_ext}"
                                            doc_folder = DOCUMENTS_DIR / f"{timestamp}_{customer.get('first_name', 'user')}_{customer.get('last_name', '')}"
                                            doc_folder.mkdir(parents=True, exist_ok=True)
                                            new_doc_path = doc_folder / doc_filename
                                            
                                            # Copy file
                                            shutil.copy2(prev_file_path, new_doc_path)
                                            
                                            # Get OCR data if available
                                            ocr_data_copy = prev_doc.get('ocr_data')
                                            if ocr_data_copy and isinstance(ocr_data_copy, str):
                                                try:
                                                    ocr_data_copy = json.loads(ocr_data_copy)
                                                except:
                                                    ocr_data_copy = None
                                            
                                            # Save document reference in new application
                                            save_document(
                                                application_id, 
                                                'identity_proof', 
                                                prev_doc_name, 
                                                str(new_doc_path), 
                                                prev_doc.get('file_size', 0),
                                                prev_doc.get('file_type', 'application/pdf'),
                                                ocr_data_copy
                                            )
                                            
                                            # Mark as verified in the new application
                                            verify_query = """
                                                UPDATE documents 
                                                SET verification_status = 'verified',
                                                    verified_at = CURRENT_TIMESTAMP
                                                WHERE application_id = %s AND document_type = 'identity_proof'
                                            """
                                            db.execute_query(verify_query, (application_id,), fetch=False)
                                    except Exception as e:
                                        # If copying fails, silently continue (don't block submission)
                                        pass
                            
                            # Save photo as document (either webcam or uploaded)
                            if photo_path and user_photo:
                                photo_size = user_photo.size if hasattr(user_photo, 'size') else 0
                                photo_type = user_photo.type if hasattr(user_photo, 'type') else 'image/jpeg'
                                photo_source_name = "webcam" if st.session_state.get('camera_photo_kyc') else "upload"
                                save_document(application_id, 'photo', f"photo_{photo_source_name}_{customer_id}.jpg",
                                            photo_path, photo_size, photo_type)
                            else:
                                # If no new photo uploaded, check if there's a verified one from previous applications
                                if prev_application_id:
                                    try:
                                        # Get verified photo from previous application (check all previous applications, check both 'photo' and 'photo_optional' types)
                                        prev_photo_query = """
                                            SELECT d.file_path, d.document_name, d.file_size, d.file_type
                                            FROM documents d
                                            INNER JOIN kyc_applications ka ON d.application_id = ka.application_id
                                            WHERE ka.customer_id = %s 
                                            AND (d.document_type = 'photo' OR d.document_type = 'photo_optional') 
                                            AND d.verification_status = 'verified'
                                            AND d.application_id != %s
                                            ORDER BY d.created_at DESC
                                            LIMIT 1
                                        """
                                        prev_photo = db.execute_one(prev_photo_query, (customer_id, application_id))
                                        
                                        if prev_photo and prev_photo.get('file_path') and os.path.exists(prev_photo.get('file_path')):
                                            # Copy the verified photo to the new application
                                            prev_file_path = prev_photo.get('file_path')
                                            prev_photo_name = prev_photo.get('document_name', 'photo')
                                            
                                            # Create a copy of the file for the new application
                                            photo_ext = os.path.splitext(prev_file_path)[1] or ".jpg"
                                            photo_filename = f"photo_{timestamp}_{customer_id}{photo_ext}"
                                            photo_folder = DOCUMENTS_DIR / f"{timestamp}_{customer.get('first_name', 'user')}_{customer.get('last_name', '')}"
                                            photo_folder.mkdir(parents=True, exist_ok=True)
                                            new_photo_path = photo_folder / photo_filename
                                            
                                            # Copy file
                                            shutil.copy2(prev_file_path, new_photo_path)
                                            
                                            # Save photo document reference in new application
                                            save_document(
                                                application_id, 
                                                'photo', 
                                                prev_photo_name, 
                                                str(new_photo_path), 
                                                prev_photo.get('file_size', 0),
                                                prev_photo.get('file_type', 'image/jpeg')
                                            )
                                            
                                            # Mark as verified in the new application
                                            verify_photo_query = """
                                                UPDATE documents 
                                                SET verification_status = 'verified',
                                                    verified_at = CURRENT_TIMESTAMP
                                                WHERE application_id = %s AND (document_type = 'photo' OR document_type = 'photo_optional')
                                            """
                                            db.execute_query(verify_photo_query, (application_id,), fetch=False)
                                            
                                            # Also update customer photo_path if it exists
                                            if os.path.exists(new_photo_path):
                                                update_photo_query = "UPDATE customers SET photo_path = %s WHERE customer_id = %s"
                                                db.execute_query(update_photo_query, (str(new_photo_path), customer_id), fetch=False)
                                    except Exception as e:
                                        # If copying fails, silently continue (don't block submission)
                                        pass
                            
                            # Update customer KYC data (status will be updated by validation)
                            kyc_data = {
                                'nominee_name': nominee_name if nominee_name else None,
                                'nominee_relation': nominee_relation if nominee_relation else None,
                                'otp_verified': otp_verified,
                                'kyc_status': 'Submitted'  # Will be updated by validation
                            }
                            update_customer_kyc(customer_id, kyc_data)
                            
                            # Update PAN and Aadhar if provided
                            if pan_card or aadhar_no:
                                update_query = "UPDATE customers SET pan_card = %s, aadhar_no = %s WHERE customer_id = %s"
                                db.execute_query(update_query, (
                                    pan_card if pan_card else customer.get('pan_card'),
                                    aadhar_no if aadhar_no else customer.get('aadhar_no'),
                                    customer_id
                                ), fetch=False)
                            
                            # Perform Advanced AI KYC Validation
                            with st.spinner("🤖 Performing advanced AI KYC validation... This may take a few moments."):
                                validation_result = perform_advanced_kyc_validation(application_id, customer_id)
                                
                                validation_status = validation_result.get('status', 'under_review')
                                overall_score = validation_result.get('overall_score', 0)
                                issues = validation_result.get('issues', [])
                                
                                # Show validation results with AI features
                                if validation_status == 'approved':
                                    st.success(f"✅ **KYC Validation Passed!**\n\n**Validation Score:** {overall_score}%\n\nYour KYC has been approved and your account is now active!")
                                    
                                    # Show AI features used
                                    validation_details = validation_result.get('validation_details', {})
                                    photo_details = validation_details.get('photo', {})
                                    ai_features = photo_details.get('ai_features', {})
                                    
                                    if ai_features:
                                        st.info("🤖 **AI Features Used:** Face Detection ✅ | Liveness Check ✅ | Quality Analysis ✅")
                                    
                                    notifications.toast_success("KYC approved! Account activated.")
                                else:  # rejected
                                    st.error(f"❌ **KYC Validation Failed**\n\n**Validation Score:** {overall_score}%\n\nPlease address the following issues and resubmit:")
                                    if issues:
                                        st.markdown("**Issues Found:**")
                                        for issue in issues[:10]:  # Show first 10 issues
                                            st.write(f"• {issue}")
                                    
                                    # Show AI features even if rejected
                                    validation_details = validation_result.get('validation_details', {})
                                    photo_details = validation_details.get('photo', {})
                                    ai_features = photo_details.get('ai_features', {})
                                    
                                    if ai_features:
                                        face_det = ai_features.get('face_detection', {})
                                        liveness = ai_features.get('liveness_detection', {})
                                        quality = ai_features.get('quality_analysis', {})
                                        
                                        st.warning(f"🤖 **AI Analysis:** Face: {'✅' if face_det.get('face_detected') else '❌'} | "
                                                 f"Live: {'✅' if liveness.get('is_live') else '⚠️'} | "
                                                 f"Quality: {quality.get('overall_rating', 'Unknown')}")
                                    
                                    notifications.toast_error("KYC validation failed. Please check issues and resubmit.")
                                
                                # Show timestamps
                                timestamps = validation_result.get('timestamps', {})
                                if timestamps:
                                    with st.expander("⏰ View Timestamps"):
                                        st.write(f"**Document Upload:** {timestamps.get('document_upload_time', 'N/A')}")
                                        st.write(f"**Photo Upload:** {timestamps.get('photo_upload_time', 'N/A')}")
                                        st.write(f"**Validation Started:** {timestamps.get('validation_start', 'N/A')}")
                                        st.write(f"**Validation Completed:** {timestamps.get('validation_end', 'N/A')}")
                                        st.write(f"**Duration:** {timestamps.get('validation_duration_seconds', 'N/A')} seconds")
                            
                            # Refresh customer data
                            st.session_state.customer = get_customer_by_user_id(st.session_state.user['user_id'])
                            
                            # Create notification based on validation status
                            if validation_status == 'approved':
                                create_notification(customer_id, 'kyc_approved', 
                                                  'KYC Approved', 
                                                  f'Your KYC application has been approved. Score: {overall_score}%. Application ID: {application_id}')
                            else:  # rejected
                                create_notification(customer_id, 'kyc_rejected', 
                                                  'KYC Rejected', 
                                                  f'Your KYC application was rejected. Score: {overall_score}%. Please review issues and resubmit. Application ID: {application_id}')
                            
                            if validation_status == 'approved':
                                st.balloons()
                            
                            change_view("Dashboard")
                        else:
                            st.error("❌ Failed to create KYC application. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        with st.expander("View Error Details"):
                            st.code(traceback.format_exc())
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("⬅ Back to Dashboard"):
            change_view("Dashboard")

# --- ENHANCED STATUS CHECK PAGE (5 States) ---
elif st.session_state.view == "StatusCheck":
    set_page_background("StatusCheck")
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2.5rem;'>Check Application Status</h1>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        
        search_type = st.radio("Search by", ["Email", "Phone Number", "Application ID"], horizontal=True)
        
        search_value = st.text_input(f"Enter {search_type}", placeholder=f"Enter your {search_type.lower()}")
        
        if st.button("🔍 Check Status", use_container_width=True, type="primary"):
            if search_value and db_connected:
                try:
                    if search_type == "Application ID":
                        # Direct application lookup
                        # Check which columns exist and build query dynamically
                        try:
                            check_cols_query = """
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = 'customers'
                            """
                            existing_cols = db.execute_query(check_cols_query, fetch=True)
                            col_names = {row['column_name'] for row in existing_cols} if existing_cols else set()
                            
                            # Build customer columns list
                            customer_cols = ['c.full_name', 'u.email']
                            group_by_cols = ['c.full_name', 'u.email']
                            
                            if 'first_name' in col_names:
                                customer_cols.append('c.first_name')
                                group_by_cols.append('c.first_name')
                            if 'last_name' in col_names:
                                customer_cols.append('c.last_name')
                                group_by_cols.append('c.last_name')
                            if 'phone_number' in col_names:
                                customer_cols.append('c.phone_number')
                                group_by_cols.append('c.phone_number')
                            if 'pan_card' in col_names:
                                customer_cols.append('c.pan_card')
                                group_by_cols.append('c.pan_card')
                            if 'aadhar_no' in col_names:
                                customer_cols.append('c.aadhar_no')
                                group_by_cols.append('c.aadhar_no')
                            
                            if 'kyc_status' in col_names:
                                customer_cols.append('c.kyc_status')
                                group_by_cols.append('c.kyc_status')
                            else:
                                customer_cols.append("'Not Submitted' as kyc_status")
                            
                            customer_cols_str = ", ".join(customer_cols)
                            group_by_str = ", ".join(group_by_cols)
                            
                            query = f"""
                                SELECT ka.*, {customer_cols_str},
                                       COALESCE(COUNT(DISTINCT d.document_id), 0) as total_documents,
                                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END), 0) as verified_documents,
                                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END), 0) as rejected_documents,
                                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'pending' OR d.verification_status IS NULL THEN d.document_id END), 0) as pending_documents
                                FROM kyc_applications ka
                                LEFT JOIN customers c ON ka.customer_id = c.customer_id
                                LEFT JOIN users u ON c.user_id = u.user_id
                                LEFT JOIN documents d ON ka.application_id = d.application_id
                                WHERE ka.application_id = %s
                                GROUP BY ka.application_id, {group_by_str}
                            """
                            
                            result = db.execute_one(query, (search_value,))
                            
                            if not any(col in col_names for col in ['kyc_status', 'nominee_name', 'nominee_relation', 'otp_verified']):
                                st.warning("⚠️ **Database Migration Recommended:** Some columns are missing. Please run `migrate_all_missing_columns.sql` for full functionality. See COMPLETE_MIGRATION_GUIDE.md")
                        except Exception as col_check_error:
                            # Fallback query with minimal columns
                            query = """
                                SELECT ka.*, c.full_name, u.email,
                                       COALESCE(COUNT(DISTINCT d.document_id), 0) as total_documents,
                                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END), 0) as verified_documents,
                                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END), 0) as rejected_documents,
                                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'pending' OR d.verification_status IS NULL THEN d.document_id END), 0) as pending_documents,
                                       'Not Submitted' as kyc_status
                                FROM kyc_applications ka
                                LEFT JOIN customers c ON ka.customer_id = c.customer_id
                                LEFT JOIN users u ON c.user_id = u.user_id
                                LEFT JOIN documents d ON ka.application_id = d.application_id
                                WHERE ka.application_id = %s
                                GROUP BY ka.application_id, c.full_name, u.email
                            """
                            result = db.execute_one(query, (search_value,))
                            st.warning("⚠️ **Database Migration Required:** Please run `migrate_all_missing_columns.sql` in DBeaver. See COMPLETE_MIGRATION_GUIDE.md")
                        
                        if result:
                            # State D or E
                            app_status = result.get('application_status', '')
                            if app_status == 'approved':
                                status_msg = "✅ KYC Verified & Account Fully Active."
                                status_code = 'E'
                            else:
                                status_msg = "📄 KYC submitted, verification in progress."
                                status_code = 'D'
                            
                            st.success(f"✅ **Application Found!**")
                            st.info(f"**Status:** {status_msg}")
                            _display_application_details(result)
                        else:
                            # State A
                            st.error("❌ **No account found with these details.**\n\nPlease check:\n- Application ID is correct\n- You have submitted a KYC application")
                    else:
                        # Use enhanced status checking function
                        status_result = check_application_status(search_value, 'email' if search_type == "Email" else 'phone')
                        
                        status_code = status_result.get('status')
                        status_msg = status_result.get('message')
                        result = status_result.get('data')
                        
                        if status_code == 'A':
                            # State A: No Account
                            st.error(f"❌ **{status_msg}**")
                        elif status_code == 'C':
                            # State C: KYC Not Started
                            st.warning(f"⚠️ **{status_msg}**")
                            if result:
                                st.info(f"**Account Details:**\n- Name: {result.get('full_name', 'N/A')}\n- Email: {result.get('email', 'N/A')}\n- Phone: {result.get('phone_number', 'N/A')}")
                                st.info("💡 **Next Steps:** Login to your account and complete KYC verification.")
                        elif status_code == 'D':
                            # State D: KYC In Progress
                            app_status = result.get('application_status', '') if result else ''
                            kyc_status = result.get('kyc_status', '') if result else ''
                            
                            # Check if rejected
                            if app_status == 'rejected' or kyc_status == 'Rejected':
                                rejection_reason = result.get('rejection_reason', '') if result else ''
                                if not rejection_reason and result and result.get('notes'):
                                    notes = result.get('notes', '')
                                    if 'Manually rejected by admin' in notes:
                                        if 'Reason:' in notes:
                                            rejection_reason = notes.split('Reason:')[1].split('\n')[0].strip()
                                
                                st.error(f"""
                                ## ❌ **KYC Application Rejected**
                                
                                Your KYC application has been **rejected**. Please review the issues and resubmit.
                                
                                **Rejection Reason:**
                                {rejection_reason if rejection_reason else 'Please review your documents and resubmit.'}
                                
                                **Next Steps:**
                                1. Review the rejection reason above
                                2. Ensure all documents are clear and valid
                                3. Make sure your photo matches the photo in your ID document
                                4. Verify that you uploaded the correct document type (PAN or Aadhar)
                                5. Login to your account to resubmit KYC documents
                                """)
                                if result:
                                    _display_application_details(result)
                            else:
                                st.info(f"ℹ️ **{status_msg}**")
                                if result:
                                    _display_application_details(result)
                        elif status_code == 'E':
                            # State E: Success
                            st.success(f"✅ **{status_msg}**")
                            if result:
                                _display_application_details(result)
                        else:
                            st.error(f"❌ {status_msg}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("View Error Details"):
                        st.code(traceback.format_exc())
            else:
                st.warning("⚠️ Please enter a search value")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("⬅ Back to Home"):
            change_view("Landing")

# --- DASHBOARD ---
elif st.session_state.view == "Dashboard":
    set_page_background("Dashboard")
    if not st.session_state.authenticated:
        change_view("Login")
        st.stop()
    
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2rem;'>My Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.customer:
        customer = st.session_state.customer
        customer_id = customer['customer_id']
        
        # Show Customer Profile
        st.markdown("### 👤 Your Profile")
        col1, col2 = st.columns([1, 2])
        with col1:
            if customer.get('photo_path') and os.path.exists(customer['photo_path']):
                st.image(customer['photo_path'], width=200)
            else:
                st.info("📷 No photo uploaded")
        with col2:
            st.write(f"**Full Name:** {customer.get('full_name', 'N/A')}")
            st.write(f"**Email:** {st.session_state.user.get('email', 'N/A')}")
            st.write(f"**Phone:** {customer.get('phone_number', 'N/A')}")
            st.write(f"**Date of Birth:** {customer.get('date_of_birth', 'N/A')}")
            st.write(f"**Age:** {customer.get('age', 'N/A')}")
            st.write(f"**Gender:** {customer.get('gender', 'N/A')}")
            st.write(f"**Occupation:** {customer.get('occupation', 'N/A')}")
            if customer.get('annual_income'):
                st.write(f"**Annual Income:** ₹{customer.get('annual_income', 0):,.0f}")
        
        st.markdown("---")
        
        # KYC Status
        kyc_status = customer.get('kyc_status', 'Not Submitted')
        st.markdown("### 📊 KYC Status")
        
        if kyc_status == 'Not Submitted':
            st.warning("⚠️ **KYC Verification Required**\n\nPlease complete your KYC verification to activate your account.")
            if st.button("📄 Complete KYC Verification", use_container_width=True, type="primary"):
                change_view("KYC Portal")
        else:
            kyc_app_status = get_customer_kyc_status(customer_id)
            
            if kyc_app_status:
                col1, col2, col3 = st.columns(3)
                with col1:
                    status = kyc_app_status['application_status'].replace('_', ' ').title()
                    status_colors = {
                        'Submitted': '🟠',
                        'Under Review': '🔵',
                        'Document Verification': '🟡',
                        'Approved': '🟢',
                        'Rejected': '🔴',
                        'Pending Resubmission': '🟠'
                    }
                    st.metric("Application Status", f"{status_colors.get(status, '⚪')} {status}")
                with col2:
                    st.metric("Total Documents", kyc_app_status.get('total_documents', 0))
                with col3:
                    st.metric("Verified Documents", kyc_app_status.get('verified_documents', 0))
                
                st.markdown("---")
                st.write(f"**Application ID:** `{kyc_app_status['application_id']}`")
                st.write(f"**Submission Date:** {kyc_app_status['submission_date']}")
                
                if kyc_app_status.get('verification_date'):
                    st.write(f"**Verification Date:** {kyc_app_status['verification_date']}")
                
                if kyc_app_status.get('rejection_reason'):
                    st.error(f"""
                    ## ❌ **KYC Application Rejected**
                    
                    **Rejection Reason:** {kyc_app_status['rejection_reason']}
                    
                    **Next Steps:**
                    1. Review the rejection reason above
                    2. Ensure all documents are clear and valid
                    3. Make sure your photo matches the photo in your ID document
                    4. Verify that you uploaded the correct document type (PAN or Aadhar)
                    5. Click "Resubmit KYC" below to upload new documents
                    """)
                    if st.button("🔄 Resubmit KYC Documents", use_container_width=True, type="primary"):
                        # Reset KYC status to allow resubmission
                        try:
                            reset_query = "UPDATE customers SET kyc_status = 'Not Submitted' WHERE customer_id = %s"
                            db.execute_query(reset_query, (customer_id,), fetch=False)
                            # Clear old documents from session state to force new uploads
                            if 'identity_doc_kyc' in st.session_state:
                                st.session_state.identity_doc_kyc = None
                            if 'camera_photo_kyc' in st.session_state:
                                st.session_state.camera_photo_kyc = None
                            if 'uploaded_photo_kyc' in st.session_state:
                                st.session_state.uploaded_photo_kyc = None
                            if 'doc_type_kyc' in st.session_state:
                                st.session_state.doc_type_kyc = None
                            
                            # Scroll to top and navigate to KYC Portal
                            st.markdown("""
                                <script>
                                    window.scrollTo({top: 0, behavior: 'instant'});
                                </script>
                            """, unsafe_allow_html=True)
                            change_view("KYC Portal")
                            st.rerun()
                        except:
                            # Scroll to top and navigate to KYC Portal
                            st.markdown("""
                                <script>
                                    window.scrollTo({top: 0, behavior: 'instant'});
                                </script>
                            """, unsafe_allow_html=True)
                            change_view("KYC Portal")
                            st.rerun()
            else:
                st.info("📋 KYC application in progress.")

# --- DOCUMENTS PAGE ---
elif st.session_state.view == "Documents":
    if not st.session_state.authenticated:
        change_view("Login")
        st.stop()
    
    st.markdown("### 📁 My Documents")
    
    if st.session_state.customer:
        customer_id = st.session_state.customer['customer_id']
        kyc_status = get_customer_kyc_status(customer_id)
        
        if kyc_status:
            documents = get_customer_documents(kyc_status['application_id'])
            if documents:
                for doc in documents:
                    with st.expander(f"📄 {doc['document_name']} - {doc['verification_status'].title()}"):
                        st.write(f"**Type:** {doc['document_type']}")
                        st.write(f"**Status:** {doc['verification_status']}")
                        if doc.get('verification_notes'):
                            st.info(f"**Notes:** {doc['verification_notes']}")
            else:
                st.info("No documents uploaded yet.")
        else:
            st.info("No application found.")

# --- ADMIN LOGIN PAGE ---
elif st.session_state.view == "AdminLogin":
    set_page_background("AdminLogin")
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2.5rem;'>🔐 Admin Access</h1>
            <p class='bank-tagline'>Enter admin credentials to access customer management</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        
        with st.form("admin_login_form"):
            admin_username = st.text_input("Admin Username", placeholder="Enter admin username")
            admin_password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
            
            submitted = st.form_submit_button("🔐 Login as Admin", use_container_width=True, type="primary")
            
            if submitted:
                # Default admin credentials: admin / admin
                if admin_username == "admin" and admin_password == "admin":
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_username = admin_username
                    st.success("✅ Admin login successful!")
                    change_view("CustomerManagement")
                    st.rerun()
                else:
                    st.error("❌ Invalid admin credentials. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("⬅ Back to Home"):
            change_view("Landing")

# --- CUSTOMER MANAGEMENT PAGE (Admin Only) ---
elif st.session_state.view == "CustomerManagement":
    if not st.session_state.get('admin_authenticated', False):
        st.error("❌ Admin access required. Please login first.")
        change_view("AdminLogin")
        st.stop()
    
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2rem;'>👥 Customer Management</h1>
            <p class='bank-tagline'>View and manage all customer accounts</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get all customers
    try:
        # Get unique customers (one row per customer, latest application)
        # Use subquery to get latest application per customer
        query = """
            SELECT 
                c.customer_id,
                c.full_name,
                c.first_name,
                c.last_name,
                u.email,
                c.phone_number,
                c.kyc_status,
                c.date_of_birth,
                c.gender,
                c.address,
                c.city_town,
                c.pincode,
                c.pan_card,
                c.aadhar_no,
                c.occupation,
                c.annual_income,
                c.marital_status,
                c.created_at,
                ka.application_status,
                ka.application_id,
                ka.notes as application_notes
            FROM customers c
            LEFT JOIN users u ON c.user_id = u.user_id
            LEFT JOIN (
                SELECT DISTINCT ON (customer_id)
                    customer_id,
                    application_status,
                    application_id,
                    notes
                FROM kyc_applications
                ORDER BY customer_id, created_at DESC
            ) ka ON ka.customer_id = c.customer_id
            ORDER BY c.created_at DESC
        """
        customers = db.execute_query(query)
        
        if customers:
            st.subheader(f"📊 Total Customers: {len(customers)}")
            
            # Search and filter
            col1, col2 = st.columns([2, 1])
            with col1:
                search_term = st.text_input("🔍 Search by name, email, or phone", placeholder="Type to search...")
            with col2:
                kyc_filter = st.selectbox("Filter by KYC Status", ["All", "Not Submitted", "Submitted", "Under Review", "Approved", "Rejected"])
            
            # Filter customers
            filtered_customers = customers
            if search_term:
                search_lower = search_term.lower()
                filtered_customers = [
                    c for c in filtered_customers
                    if (c.get('full_name', '').lower().find(search_lower) >= 0 or
                        c.get('email', '').lower().find(search_lower) >= 0 or
                        str(c.get('phone_number', '')).find(search_term) >= 0)
                ]
            
            if kyc_filter != "All":
                filtered_customers = [c for c in filtered_customers if c.get('kyc_status') == kyc_filter]
            
            if filtered_customers:
                st.markdown(f"**Showing {len(filtered_customers)} customers**")
                
                # Bulk actions section
                st.markdown("---")
                st.markdown("### 🔧 Bulk Actions")
                col_action1, col_action2, col_action3 = st.columns(3)
                
                with col_action1:
                    if st.button("🔄 Re-validate Selected", use_container_width=True, type="primary"):
                        customers_to_validate = [c for c in filtered_customers if c.get('application_id')]
                        if customers_to_validate:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            for idx, customer in enumerate(customers_to_validate):
                                status_text.text(f"Validating {customer.get('full_name', 'N/A')}... ({idx+1}/{len(customers_to_validate)})")
                                try:
                                    perform_advanced_kyc_validation(customer.get('application_id'), customer.get('customer_id'))
                                except:
                                    pass
                                progress_bar.progress((idx + 1) / len(customers_to_validate))
                            status_text.text("✅ Complete!")
                            st.success(f"✅ Re-validated {len(customers_to_validate)} customers")
                            st.rerun()
                        else:
                            st.warning("⚠️ No customers with KYC applications found.")
                
                with col_action2:
                    if st.button("📊 Export to Excel", use_container_width=True):
                        try:
                            export_data = []
                            for customer in filtered_customers:
                                app_notes = customer.get('application_notes', '')
                                kyc_score = "N/A"
                                validation_time = "N/A"
                                doc_upload_time = "N/A"
                                photo_upload_time = "N/A"
                                
                                if app_notes and 'Overall Score:' in app_notes:
                                    try:
                                        score_line = [line for line in app_notes.split('\n') if 'Overall Score:' in line]
                                        if score_line:
                                            kyc_score = score_line[0].split('Overall Score:')[1].split('%')[0].strip() + '%'
                                    except:
                                        pass
                                
                                if app_notes and 'Validation Time:' in app_notes:
                                    try:
                                        time_line = [line for line in app_notes.split('\n') if 'Validation Time:' in line]
                                        if time_line:
                                            validation_time = time_line[0].split('Validation Time:')[1].strip()
                                    except:
                                        pass
                                
                                if customer.get('application_id'):
                                    try:
                                        doc_query = "SELECT created_at, document_type FROM documents WHERE application_id = %s ORDER BY created_at"
                                        docs = db.execute_query(doc_query, (customer.get('application_id'),))
                                        for doc in docs:
                                            upload_time = str(doc.get('created_at', ''))[:19] if doc.get('created_at') else "N/A"
                                            if doc.get('document_type') == 'identity_proof':
                                                doc_upload_time = upload_time
                                            elif doc.get('document_type') == 'photo':
                                                photo_upload_time = upload_time
                                    except:
                                        pass
                                
                                export_data.append({
                                    'Customer ID': str(customer.get('customer_id', '')),
                                    'Full Name': customer.get('full_name', ''),
                                    'Email': customer.get('email', ''),
                                    'Phone': customer.get('phone_number', ''),
                                    'KYC Status': customer.get('kyc_status', ''),
                                    'Application Status': customer.get('application_status', ''),
                                    'KYC Score': kyc_score,
                                    'Application ID': str(customer.get('application_id', '')) if customer.get('application_id') else '',
                                    'Document Upload': doc_upload_time,
                                    'Photo Upload': photo_upload_time,
                                    'Validation Time': validation_time
                                })
                            
                            df = pd.DataFrame(export_data)
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False, sheet_name='Customer KYC Data')
                            output.seek(0)
                            
                            st.download_button(
                                label="⬇️ Download Excel",
                                data=output,
                                file_name=f"customer_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            st.success(f"✅ Excel file ready with {len(export_data)} records")
                        except Exception as e:
                            st.error(f"❌ Export error: {str(e)}")
                
                with col_action3:
                    if st.button("🔄 Refresh", use_container_width=True):
                        st.rerun()
                
                st.markdown("---")
                st.markdown("### 👥 Customer Details")
                
                # Display customers in expandable cards
                for idx, customer in enumerate(filtered_customers):
                    kyc_status = customer.get('kyc_status', 'N/A')
                    status_color = {
                        'Approved': '🟢',
                        'Submitted': '🟠',
                        'Under Review': '🔵',
                        'Rejected': '🔴',
                        'Not Submitted': '⚪'
                    }.get(kyc_status, '⚪')
                    
                    # Create unique key using index and customer_id (for button only, expander doesn't support key)
                    customer_id_str = str(customer.get('customer_id', ''))
                    app_id_str = str(customer.get('application_id', '')) if customer.get('application_id') else 'noapp'
                    unique_key = f"{idx}_{customer_id_str}_{app_id_str}"
                    
                    with st.expander(f"{status_color} {customer.get('full_name', 'N/A')} - {kyc_status}", expanded=False):
                        # Get document upload times and other data first
                        uploaded_documents = []
                        validation_time = "N/A"
                        doc_upload_time = "N/A"
                        photo_upload_time = "N/A"
                        kyc_score = "N/A"
                        app_notes = customer.get('application_notes', '')
                        
                        if app_notes and 'Overall Score:' in app_notes:
                            try:
                                score_line = [line for line in app_notes.split('\n') if 'Overall Score:' in line]
                                if score_line:
                                    kyc_score = score_line[0].split('Overall Score:')[1].split('%')[0].strip() + '%'
                            except:
                                pass
                        
                        if app_notes and 'Validation Time:' in app_notes:
                            try:
                                time_line = [line for line in app_notes.split('\n') if 'Validation Time:' in line]
                                if time_line:
                                    validation_time = time_line[0].split('Validation Time:')[1].strip()
                            except:
                                pass
                        
                        if customer.get('application_id'):
                            try:
                                doc_query = """
                                    SELECT created_at, document_type, document_name, verification_status, verified_at
                                    FROM documents
                                    WHERE application_id = %s
                                    ORDER BY created_at
                                """
                                docs = db.execute_query(doc_query, (customer.get('application_id'),))
                                for doc in docs:
                                    upload_time = str(doc.get('created_at', ''))[:19] if doc.get('created_at') else "N/A"
                                    doc_type = doc.get('document_type', 'unknown')
                                    doc_name = doc.get('document_name', 'N/A')
                                    
                                    uploaded_documents.append({
                                        'type': doc_type,
                                        'name': doc_name,
                                        'upload_time': upload_time
                                    })
                                    
                                    if doc_type == 'identity_proof':
                                        doc_upload_time = f"{upload_time} ({doc_name})"
                                    elif doc_type == 'photo':
                                        photo_upload_time = f"{upload_time} ({doc_name})"
                            except:
                                pass
                            
                        # NEW LAYOUT: Two main columns - Personal Info (left), Address/Contact/Employment (right)
                        col_personal, col_contact_emp = st.columns(2)
                        
                        with col_personal:
                            st.markdown("### 👤 Personal Information")
                            st.write(f"**Full Name:** {customer.get('full_name', 'N/A')}")
                            st.write(f"**First Name:** {customer.get('first_name', 'N/A')}")
                            st.write(f"**Last Name:** {customer.get('last_name', 'N/A')}")
                            st.write(f"**Email:** {customer.get('email', 'N/A')}")
                            st.write(f"**Phone:** {customer.get('phone_number', 'N/A')}")
                            st.write(f"**Date of Birth:** {customer.get('date_of_birth', 'N/A')}")
                            st.write(f"**Gender:** {customer.get('gender', 'N/A')}")
                            st.write(f"**Marital Status:** {customer.get('marital_status', 'N/A')}")
                        
                        with col_contact_emp:
                            st.markdown("### 📍 Address & Contact")
                            st.write(f"**Address:** {customer.get('address', 'N/A')}")
                            st.write(f"**City/Town:** {customer.get('city_town', 'N/A')}")
                            st.write(f"**Pincode:** {customer.get('pincode', 'N/A')}")
                            st.write(f"**PAN Card:** {customer.get('pan_card', 'N/A')}")
                            st.write(f"**Aadhar No:** {customer.get('aadhar_no', 'N/A')}")
                            
                            st.markdown("### 💼 Employment")
                            st.write(f"**Occupation:** {customer.get('occupation', 'N/A')}")
                            income = customer.get('annual_income')
                            st.write(f"**Annual Income:** ₹{income:,.0f}" if income else "**Annual Income:** N/A")
                        
                        # Second row: Timestamps (left), Validation Details (right)
                        col_timestamps, col_validation = st.columns(2)
                        
                        with col_timestamps:
                            # Timestamps section
                            st.markdown("### ⏰ Timestamps")
                            st.write(f"**Document Upload:** {doc_upload_time}")
                            st.write(f"**Photo Upload:** {photo_upload_time}")
                            st.write(f"**Validation Time:** {validation_time}")
                        
                        with col_validation:
                            st.markdown("### 📊 Validation Details")
                            
                            # KYC Information
                            st.markdown("#### KYC Information")
                            st.write(f"**KYC Status:** {kyc_status}")
                            app_status = customer.get('application_status', 'No Application') if customer.get('application_status') else 'No Application'
                            st.write(f"**Application Status:** {app_status}")
                            st.write(f"**KYC Validation Score:** {kyc_score}")
                            
                            # Show validation details dropdown
                            if app_notes and ('AUTO-VALIDATION RESULTS' in app_notes or 'ADVANCED AI-VALIDATION RESULTS' in app_notes):
                                with st.expander("📋 View Full Validation Details & Scores"):
                                    st.code(app_notes)
                                    
                                    # Show AI features breakdown if available
                                    if 'AI Features:' in app_notes:
                                        st.markdown("### 🤖 AI Validation Features")
                                        ai_section = []
                                        in_ai_section = False
                                        for line in app_notes.split('\n'):
                                            if 'AI Features:' in line:
                                                in_ai_section = True
                                            if in_ai_section:
                                                ai_section.append(line)
                                                if line.strip() == '' and len(ai_section) > 1:
                                                    break
                                        
                                        if ai_section:
                                            st.markdown('\n'.join(ai_section))
                            else:
                                st.info("No validation details available yet.")
                        
                        # Third row: Uploaded Documents (full width, single row)
                        if uploaded_documents:
                                st.markdown("#### 📄 Uploaded Documents")
                                
                                # Display documents list with view buttons
                                for idx, doc_info in enumerate(uploaded_documents):
                                    doc_type_display = doc_info['type'].replace('_', ' ').title()
                                    doc_name_safe = doc_info['name'].replace(' ', '_').replace('.', '_')[:30]
                                    
                                    # Create unique keys for each document
                                    view_key = f"view_doc_{unique_key}_{idx}_{doc_name_safe}"
                                    viewing_state_key = f"viewing_doc_{unique_key}_{idx}"
                                    close_key = f"close_doc_{unique_key}_{idx}"
                                    
                                    # Document row layout: Info on left, actions on right
                                    col_doc1, col_doc2, col_doc3 = st.columns([4, 1, 1])
                                    with col_doc1:
                                        # Show verification status
                                        doc_status_query = """
                                            SELECT verification_status, verification_notes
                                            FROM documents
                                            WHERE application_id = %s AND document_type = %s AND document_name = %s
                                            LIMIT 1
                                        """
                                        doc_status = db.execute_one(doc_status_query, (
                                            customer.get('application_id'),
                                            doc_info['type'],
                                            doc_info['name']
                                        )) if customer.get('application_id') else None
                                        
                                        status_icon = "✅" if doc_status and doc_status.get('verification_status') == 'verified' else "❌" if doc_status and doc_status.get('verification_status') == 'rejected' else "⏳"
                                        status_text = doc_status.get('verification_status', 'pending').title() if doc_status else 'Pending'
                                        st.write(f"- **{doc_type_display}:** {doc_info['name']} (Uploaded: {doc_info['upload_time']}) {status_icon} {status_text}")
                                    
                                    with col_doc2:
                                        # Get document file path to view
                                        if customer.get('application_id'):
                                            try:
                                                doc_path_query = """
                                                    SELECT file_path, document_id, document_type, document_name
                                                    FROM documents
                                                    WHERE application_id = %s AND document_type = %s AND document_name = %s
                                                    LIMIT 1
                                                """
                                                doc_file = db.execute_one(doc_path_query, (
                                                    customer.get('application_id'),
                                                    doc_info['type'],
                                                    doc_info['name']
                                                ))
                                                if doc_file and doc_file.get('file_path'):
                                                    file_path = doc_file.get('file_path')
                                                    doc_id = doc_file.get('document_id')
                                                    if os.path.exists(file_path):
                                                        is_viewing = st.session_state.get(viewing_state_key, False)
                                                        if is_viewing:
                                                            if st.button(f"❌ Close", key=close_key, use_container_width=True):
                                                                st.session_state[viewing_state_key] = False
                                                                st.session_state[f"viewing_doc_path_{unique_key}_{idx}"] = None
                                                                st.rerun()
                                                        else:
                                                            if st.button(f"👁️ View", key=view_key, use_container_width=True):
                                                                for other_idx in range(len(uploaded_documents)):
                                                                    if other_idx != idx:
                                                                        other_state_key = f"viewing_doc_{unique_key}_{other_idx}"
                                                                        other_path_key = f"viewing_doc_path_{unique_key}_{other_idx}"
                                                                        st.session_state[other_state_key] = False
                                                                        st.session_state[other_path_key] = None
                                                                st.session_state[viewing_state_key] = True
                                                                st.session_state[f"viewing_doc_path_{unique_key}_{idx}"] = file_path
                                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error loading document: {str(e)}")
                                    
                                    with col_doc3:
                                        # Individual document rejection button
                                        # Get doc_file and doc_id for this document (may be different from col_doc2)
                                        doc_file_reject = None
                                        doc_id_reject = None
                                        if customer.get('application_id'):
                                            try:
                                                doc_query_reject = """
                                                    SELECT file_path, document_id, document_type, document_name
                                                    FROM documents
                                                    WHERE application_id = %s AND document_type = %s AND document_name = %s
                                                    LIMIT 1
                                                """
                                                doc_file_reject = db.execute_one(doc_query_reject, (
                                                    customer.get('application_id'),
                                                    doc_info['type'],
                                                    doc_info['name']
                                                ))
                                                if doc_file_reject:
                                                    doc_id_reject = doc_file_reject.get('document_id')
                                            except:
                                                pass
                                        
                                        if customer.get('application_id') and doc_file_reject and doc_id_reject:
                                            doc_id = doc_id_reject
                                            # Include document_id in key to ensure absolute uniqueness
                                            doc_id_str = str(doc_id).replace('-', '')[:16]  # Use first 16 chars of UUID without dashes
                                            # Also include document name hash for extra uniqueness
                                            doc_name_hash = abs(hash(doc_info.get('name', ''))) % 10000
                                            reject_doc_key = f"reject_{unique_key}_{idx}_{doc_id_str}_{doc_name_hash}"
                                            reject_reason_key = f"reason_{unique_key}_{idx}_{doc_id_str}_{doc_name_hash}"
                                            
                                            # Check if document is already rejected
                                            is_already_rejected = doc_status and doc_status.get('verification_status') == 'rejected'
                                            
                                            if is_already_rejected:
                                                st.info("❌ Already Rejected")
                                                if doc_status.get('verification_notes'):
                                                    rejection_note = doc_status.get('verification_notes', '')
                                                    if 'Reason:' in rejection_note:
                                                        reason = rejection_note.split('Reason:')[1].split('.')[0].strip() if 'Reason:' in rejection_note else ''
                                                        if reason:
                                                            st.caption(f"Reason: {reason[:50]}...")
                                            else:
                                                # Get admin user_id
                                                doc_admin_user_id = None
                                                try:
                                                    if st.session_state.get('user') and st.session_state.user.get('user_id'):
                                                        doc_admin_user_id = st.session_state.user.get('user_id')
                                                    else:
                                                        admin_username = st.session_state.get('admin_username', 'admin')
                                                        admin_query = "SELECT user_id FROM users WHERE username = %s AND role = 'admin'"
                                                        admin_user = db.execute_one(admin_query, (admin_username,))
                                                        if admin_user:
                                                            doc_admin_user_id = admin_user.get('user_id')
                                                except:
                                                    pass
                                                
                                                # Check if rejection reason input is shown
                                                if st.session_state.get(f"show_reject_{reject_doc_key}", False):
                                                    reject_reason = st.text_input(
                                                        "Rejection Reason",
                                                        key=reject_reason_key,
                                                        placeholder="Enter reason..."
                                                    )
                                                    # Horizontal buttons using container
                                                    btn_row = st.container()
                                                    with btn_row:
                                                        btn1, btn2 = st.columns(2)
                                                        with btn1:
                                                            if st.button("✅ Confirm", key=f"confirm_reject_{reject_doc_key}", use_container_width=True):
                                                                if reject_reason:
                                                                    from db_helpers import admin_reject_document
                                                                    if admin_reject_document(
                                                                        doc_id,
                                                                        customer.get('application_id'),
                                                                        customer.get('customer_id'),
                                                                        doc_admin_user_id,
                                                                        reject_reason,
                                                                        doc_info['type']
                                                                    ):
                                                                        st.success(f"✅ {doc_type_display} rejected!")
                                                                        st.session_state[f"show_reject_{reject_doc_key}"] = False
                                                                        st.rerun()
                                                                    else:
                                                                        st.error("❌ Failed to reject document")
                                                                else:
                                                                    st.warning("⚠️ Please enter rejection reason")
                                                        with btn2:
                                                            if st.button("❌ Cancel", key=f"cancel_reject_{reject_doc_key}", use_container_width=True):
                                                                st.session_state[f"show_reject_{reject_doc_key}"] = False
                                                                st.rerun()
                                                else:
                                                    if st.button(f"❌ Reject", key=reject_doc_key, type="secondary", use_container_width=True):
                                                        st.session_state[f"show_reject_{reject_doc_key}"] = True
                                                        st.rerun()
                                
                                # Display document if viewing
                                for idx, doc_info in enumerate(uploaded_documents):
                                    viewing_state_key = f"viewing_doc_{unique_key}_{idx}"
                                    viewing_path_key = f"viewing_doc_path_{unique_key}_{idx}"
                                    
                                    if st.session_state.get(viewing_state_key, False):
                                        doc_path = st.session_state.get(viewing_path_key)
                                        if doc_path and os.path.exists(doc_path):
                                            st.markdown("---")
                                            st.markdown(f"#### 📄 Viewing: {doc_info['name']}")
                                            
                                            if doc_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                                                st.image(doc_path, caption=doc_info['name'], width=500)
                                            elif doc_path.lower().endswith('.pdf'):
                                                st.info(f"📄 **PDF Document:** {doc_info['name']}\n\n**File Path:** `{doc_path}`\n\n*Please download the PDF file from the path above to view it.*")
                                            else:
                                                st.info(f"📄 **Document:** {doc_info['name']}\n\n**File Path:** `{doc_path}`\n\n*Please download the file from the path above to view it.*")
                                            
                                            close_key = f"close_doc_view_{unique_key}_{idx}"
                                            if st.button(f"❌ Close View", key=close_key):
                                                st.session_state[viewing_state_key] = False
                                                st.session_state[viewing_path_key] = None
                                                st.rerun()
                        
                        # Admin Actions at bottom left
                        st.markdown("---")
                        st.markdown("### 🔧 Admin Actions")
                        
                        if customer.get('application_id'):
                            st.write(f"**Application ID:** `{customer.get('application_id')}`")
                        
                        col_approve, col_reject, col_revalidate = st.columns(3)
                        
                        with col_approve:
                            if st.button(f"✅ Approve KYC", key=f"approve_kyc_{unique_key}", use_container_width=True, type="primary"):
                                if customer.get('application_id') and customer.get('customer_id'):
                                    admin_user_id = None
                                    try:
                                        if st.session_state.get('user') and st.session_state.user.get('user_id'):
                                            admin_user_id = st.session_state.user.get('user_id')
                                        else:
                                            admin_username = st.session_state.get('admin_username', 'admin')
                                            admin_query = "SELECT user_id FROM users WHERE username = %s AND role = 'admin'"
                                            admin_user = db.execute_one(admin_query, (admin_username,))
                                            if admin_user:
                                                admin_user_id = admin_user.get('user_id')
                                    except Exception as e:
                                        st.error(f"❌ Error getting admin user: {str(e)}")
                                    
                                    if admin_user_id:
                                        from db_helpers import admin_approve_kyc
                                        if admin_approve_kyc(customer.get('application_id'), customer.get('customer_id'), admin_user_id, "Approved by admin"):
                                            st.success("✅ KYC Approved Successfully!")
                                            st.rerun()
                                        else:
                                            st.error("❌ Failed to approve KYC")
                                    else:
                                        from db_helpers import admin_approve_kyc
                                        try:
                                            if admin_approve_kyc(customer.get('application_id'), customer.get('customer_id'), None, "Approved by admin"):
                                                st.success("✅ KYC Approved Successfully!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Failed to approve KYC")
                                        except Exception as e:
                                            st.error(f"❌ Error: {str(e)}")
                                else:
                                    st.warning("⚠️ No KYC application found")
                        
                        with col_reject:
                            rejection_reason = st.text_input(
                                "Rejection Reason",
                                key=f"reject_reason_{unique_key}",
                                placeholder="Enter reason for rejection..."
                            )
                            if st.button(f"❌ Reject KYC", key=f"reject_kyc_{unique_key}", use_container_width=True, type="secondary"):
                                if customer.get('application_id') and customer.get('customer_id'):
                                    if not rejection_reason:
                                        st.warning("⚠️ Please enter a rejection reason")
                                    else:
                                        admin_user_id = None
                                        try:
                                            if st.session_state.get('user') and st.session_state.user.get('user_id'):
                                                admin_user_id = st.session_state.user.get('user_id')
                                            else:
                                                admin_username = st.session_state.get('admin_username', 'admin')
                                                admin_query = "SELECT user_id FROM users WHERE username = %s AND role = 'admin'"
                                                admin_user = db.execute_one(admin_query, (admin_username,))
                                                if admin_user:
                                                    admin_user_id = admin_user.get('user_id')
                                        except Exception as e:
                                            st.error(f"❌ Error getting admin user: {str(e)}")
                                        
                                        if admin_user_id:
                                            from db_helpers import admin_reject_kyc
                                            if admin_reject_kyc(customer.get('application_id'), customer.get('customer_id'), admin_user_id, rejection_reason):
                                                st.success("❌ KYC Rejected Successfully!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Failed to reject KYC")
                                        else:
                                            from db_helpers import admin_reject_kyc
                                            try:
                                                if admin_reject_kyc(customer.get('application_id'), customer.get('customer_id'), None, rejection_reason):
                                                    st.success("❌ KYC Rejected Successfully!")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Failed to reject KYC")
                                            except Exception as e:
                                                st.error(f"❌ Error: {str(e)}")
                                else:
                                    st.warning("⚠️ No KYC application found")
                        
                        with col_revalidate:
                            if st.button(f"🔄 Re-validate KYC", key=f"revalidate_kyc_{unique_key}", use_container_width=True):
                                if customer.get('application_id'):
                                    with st.spinner("🔄 Running advanced AI validation..."):
                                        try:
                                            app_id = customer.get('application_id')
                                            cust_id = customer.get('customer_id')
                                            
                                            validation_result = perform_advanced_kyc_validation(
                                                app_id,
                                                cust_id
                                            )
                                            
                                            status = validation_result.get('status', 'error')
                                            score = validation_result.get('overall_score', 0)
                                            
                                            if status == 'approved':
                                                st.success(f"✅ **KYC Approved!** Score: {score}%")
                                            else:
                                                st.error(f"❌ **KYC Rejected** Score: {score}%")
                                            
                                            issues = validation_result.get('issues', [])
                                            if issues:
                                                safe_issues = []
                                                for issue in issues[:5]:
                                                    try:
                                                        safe_issue = issue.encode('ascii', 'ignore').decode('ascii')
                                                        safe_issues.append(safe_issue)
                                                    except:
                                                        safe_issues.append(str(issue)[:50])
                                                if safe_issues:
                                                    st.warning(f"**Issues Found:** {', '.join(safe_issues)}")
                                            
                                            if validation_result.get('validation_details', {}).get('photo', {}).get('ai_features'):
                                                st.info("🤖 **AI Features Used:** Face Detection, Liveness Check, Quality Analysis")
                                            
                                            st.rerun()
                                        except Exception as e:
                                            error_msg = str(e)
                                            try:
                                                error_msg = error_msg.encode('ascii', 'ignore').decode('ascii')
                                            except:
                                                error_msg = "Validation error occurred. Please check logs."
                                            st.error(f"❌ Error: {error_msg}")
                                else:
                                    st.warning("⚠️ No KYC application found for this customer.")
                        
                        created = customer.get('created_at')
                        st.write(f"**Account Created:** {str(created)[:19] if created else 'N/A'}")
            else:
                st.info("No customers found matching your search criteria.")
        else:
            st.info("No customers found in the database.")
    
    except Exception as e:
        st.error(f"❌ Error loading customers: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
    
    st.markdown("---")
    if st.button("⬅ Back to Admin Login"):
        st.session_state.admin_authenticated = False
        change_view("AdminLogin")
    if st.button("🏠 Back to Home"):
        st.session_state.admin_authenticated = False
        change_view("Landing")

# --- ADMIN DASHBOARD (Integrated) ---
elif st.session_state.view == "Admin":
    set_page_background("Admin")
    if not st.session_state.authenticated:
        change_view("Login")
        st.stop()
    
    if st.session_state.user.get('role') != 'admin':
        st.error("❌ Access Denied. Admin privileges required.")
        change_view("Dashboard")
        st.stop()
    
    # Hero Section with Bank Officer Image
    st.markdown("""
        <div class='bank-header-main' style='margin-bottom: 2rem;'>
            <div style='display: flex; align-items: center; justify-content: space-between; padding: 2rem;'>
                <div style='flex: 1;'>
                    <h1 class='bank-logo' style='font-size: 2.5rem; text-align: left; margin-bottom: 1rem;'>Admin Dashboard</h1>
                    <p class='bank-tagline' style='text-align: left; font-size: 1.1rem;'>Manage customer applications and KYC verifications</p>
                </div>
                <div class='hero-image-wrapper' style='flex: 0 0 300px; margin-left: 2rem;'>
                    <div style='background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(15, 23, 42, 0.8) 100%); 
                                padding: 2rem; border-radius: 24px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;'>
                        <div style='font-size: 8rem; margin-bottom: 1rem; filter: drop-shadow(0 0 20px rgba(6, 182, 212, 0.5));'>👔</div>
                        <h3 style='color: #ffffff; font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem;'>Professional Support</h3>
                        <p style='color: #94a3b8; font-size: 0.95rem; line-height: 1.5;'>
                            Expert banking professionals ready to assist with customer management and verification processes.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    AdminDashboard.render_dashboard()
    
    if st.button("⬅ Back to Dashboard"):
        change_view("Dashboard")

# --- AUDIT REPORTS (Integrated) ---
elif st.session_state.view == "AuditReports":
    if not st.session_state.authenticated:
        change_view("Login")
        st.stop()
    
    if st.session_state.user.get('role') != 'admin':
        st.error("❌ Access Denied. Admin privileges required.")
        change_view("Dashboard")
        st.stop()
    
    AuditReports.render_reports_page()
    
    if st.button("⬅ Back to Admin Dashboard"):
        change_view("Admin")

