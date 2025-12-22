"""
Ti Tans Bank - Professional Banking Portal
Refactored with Progressive KYC Flow, Enhanced Status Tracking, and Integrated Admin/Audit
"""

import streamlit as st
import os
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
        
        doc_query = """
            SELECT document_type, document_name, verification_status, 
                   verification_notes, created_at
            FROM documents
            WHERE application_id = %s
            ORDER BY created_at DESC
        """
        documents = db.execute_query(doc_query, (result['application_id'],))
        
        if documents:
            for doc in documents:
                doc_type = doc['document_type'].replace('_', ' ').title()
                doc_status = doc['verification_status'].title()
                
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{doc_type}**")
                    st.caption(doc['document_name'])
                with col2:
                    if doc_status == 'Verified':
                        st.success(f"✅ {doc_status}")
                    elif doc_status == 'Rejected':
                        st.error(f"❌ {doc_status}")
                    else:
                        st.warning(f"⏳ {doc_status}")
                    if doc.get('verification_notes'):
                        st.caption(f"Note: {doc['verification_notes']}")
                with col3:
                    st.caption(f"Uploaded: {doc['created_at'].strftime('%Y-%m-%d') if doc['created_at'] else 'N/A'}")
                
                st.markdown("---")
            
            # Summary
            total_docs = result.get('total_documents', 0)
            verified_docs = result.get('verified_documents', 0)
            rejected_docs = result.get('rejected_documents', 0)
            
            st.markdown("### 📈 Document Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Documents", total_docs)
            with col2:
                st.metric("Verified", verified_docs, delta=f"{verified_docs}/{total_docs}")
            with col3:
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
        change_view("AdminLogin")
    
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
                    phone = st.text_input("Phone Number*", placeholder="+91 9876543210")
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
                    
                    if missing_fields:
                        st.error(f"❌ **Please fill all mandatory fields:**\n\n" + "\n".join([f"• {field}" for field in missing_fields]))
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match. Please re-enter your password.")
                    elif not db_connected:
                        st.error("❌ Database not connected. Please check your database connection.")
                    else:
                        try:
                            # Create full name
                            full_name = f"{first_name} {last_name}".strip()
                            
                            # Create user account
                            user_id = create_user(username, email, password)
                            if user_id:
                                # Prepare customer data (KYC Status = 'Not Submitted')
                                customer_data = {
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'full_name': full_name,
                                    'date_of_birth': dob,
                                    'gender': gender,
                                    'marital_status': marital_status,
                                    'age': int(age),
                                    'phone_number': phone,
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
            st.error(f"""
            ## ❌ **KYC Application Rejected**
            
            Your KYC application was rejected. Please review the issues and resubmit.
            
            **Application ID:** `{app_id}`
            **Status:** Rejected
            **KYC Status:** {kyc_status}
            """)
            
            if st.button("🔄 Resubmit KYC", use_container_width=True, type="primary"):
                # Allow resubmission by changing status
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
        
        st.info("ℹ️ **KYC Verification:** Complete identity verification and photo upload to activate your account.")
        
        # Photo selection OUTSIDE form (mandatory webcam + optional upload)
        st.markdown("### 📸 Photo Identification 1 (Mandatory - Webcam)")
        
        # Initialize session state
        if 'camera_photo_kyc' not in st.session_state:
            st.session_state.camera_photo_kyc = None
        
        # Mandatory webcam photo
        st.info("📷 **Webcam Instructions:** Click 'Take Photo' below and allow camera access when prompted.")
        camera_photo = st.camera_input(
            "Take a live photo* (Mandatory)",
            help="Position your face in the frame. This is required for KYC verification.",
            key="camera_mandatory_kyc"
        )
        
        if camera_photo:
            st.session_state.camera_photo_kyc = camera_photo
            st.success("✅ Photo captured successfully")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.image(camera_photo, width=200, caption="Webcam Photo Preview")
            with col2:
                if st.button("🗑️ Remove", key="remove_camera_kyc_outside"):
                    st.session_state.camera_photo_kyc = None
                    st.rerun()
        
        user_photo = st.session_state.camera_photo_kyc
        
        st.markdown("---")
        
        # Optional second photo upload
        st.markdown("### 📷 Photo Identification 2 (Optional - Upload from Local)")
        
        if 'uploaded_photo_kyc_optional' not in st.session_state:
            st.session_state.uploaded_photo_kyc_optional = None
        
        optional_uploaded = st.file_uploader(
            "Upload additional photo (Optional) - JPG/PNG, Max 2MB",
            type=["jpg", "jpeg", "png"],
            help="Optional: Upload an additional photo from your device",
            key="file_upload_optional_kyc"
        )
        
        if optional_uploaded:
            st.session_state.uploaded_photo_kyc_optional = optional_uploaded
            st.success(f"✅ Additional photo uploaded: {optional_uploaded.name}")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.image(optional_uploaded, width=200, caption="Additional Photo Preview")
            with col2:
                if st.button("🗑️ Remove", key="remove_optional_upload_kyc"):
                    st.session_state.uploaded_photo_kyc_optional = None
                    st.rerun()
        
        optional_photo = st.session_state.uploaded_photo_kyc_optional
        
        st.markdown("---")
        
        with st.form("kyc_portal_form", clear_on_submit=False):
            st.markdown("### 📄 Identity Verification (Mandatory)")
            st.markdown("<p style='color: #ef4444; font-size: 0.9rem;'>* Indicates mandatory fields</p>", unsafe_allow_html=True)
            
            doc_type = st.selectbox("Document Type*", ["", "Aadhar Card", "PAN Card", "Passport", "Voter ID"])
            identity_doc = st.file_uploader(f"Upload {doc_type if doc_type else 'Identity Document'}*", 
                                          type=["pdf", "jpg", "png", "jpeg"],
                                          help="Upload a clear scan of your identity document")
            
            if identity_doc:
                st.success(f"✅ File uploaded: {identity_doc.name} ({identity_doc.size / 1024:.1f} KB)")
            
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
                # Validation
                missing_fields = []
                if not doc_type or doc_type == "": missing_fields.append("Document Type")
                if not identity_doc: missing_fields.append("Identity Document")
                if not user_photo: missing_fields.append("Photo (Webcam - Mandatory)")
                
                if missing_fields:
                    st.error(f"❌ **Please complete all mandatory fields:**\n\n" + "\n".join([f"• {field}" for field in missing_fields]))
                    if not user_photo:
                        st.warning("⚠️ **Webcam photo required!** Please use the webcam above to take a mandatory photo.")
                elif not db_connected:
                    st.error("❌ Database not connected.")
                else:
                    try:
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
                            
                            # Save mandatory webcam photo as document
                            if photo_path:
                                photo_size = user_photo.size if hasattr(user_photo, 'size') else 0
                                photo_type = user_photo.type if hasattr(user_photo, 'type') else 'image/jpeg'
                                save_document(application_id, 'photo', f"photo_webcam_{customer_id}.jpg",
                                            photo_path, photo_size, photo_type)
                            
                            # Save optional uploaded photo if provided
                            if optional_photo:
                                timestamp_opt = datetime.now().strftime("%Y%m%d_%H%M%S")
                                if hasattr(optional_photo, 'name') and optional_photo.name:
                                    file_ext_opt = optional_photo.name.split('.')[-1] if '.' in optional_photo.name else 'jpg'
                                else:
                                    file_ext_opt = 'jpg'
                                photo_filename_opt = f"photo_optional_{timestamp_opt}_{customer_id}.{file_ext_opt}"
                                photo_path_opt_full = DOCUMENTS_DIR / photo_filename_opt
                                with open(photo_path_opt_full, "wb") as f:
                                    f.write(optional_photo.getbuffer())
                                photo_path_opt = str(photo_path_opt_full)
                                
                                photo_size_opt = optional_photo.size if hasattr(optional_photo, 'size') else 0
                                photo_type_opt = optional_photo.type if hasattr(optional_photo, 'type') else 'image/jpeg'
                                save_document(application_id, 'photo_optional', f"photo_optional_{customer_id}.jpg",
                                            photo_path_opt, photo_size_opt, photo_type_opt)
                            
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
                                       COUNT(DISTINCT d.document_id) as total_documents,
                                       COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END) as verified_documents,
                                       COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END) as rejected_documents
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
                                       COUNT(DISTINCT d.document_id) as total_documents,
                                       COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END) as verified_documents,
                                       COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END) as rejected_documents,
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
                    st.error(f"**Rejection Reason:** {kyc_app_status['rejection_reason']}")
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
            LEFT JOIN kyc_applications ka ON c.customer_id = ka.customer_id
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
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### Personal Information")
                            st.write(f"**Full Name:** {customer.get('full_name', 'N/A')}")
                            st.write(f"**First Name:** {customer.get('first_name', 'N/A')}")
                            st.write(f"**Last Name:** {customer.get('last_name', 'N/A')}")
                            st.write(f"**Email:** {customer.get('email', 'N/A')}")
                            st.write(f"**Phone:** {customer.get('phone_number', 'N/A')}")
                            st.write(f"**Date of Birth:** {customer.get('date_of_birth', 'N/A')}")
                            st.write(f"**Gender:** {customer.get('gender', 'N/A')}")
                            st.write(f"**Marital Status:** {customer.get('marital_status', 'N/A')}")
                        
                        with col2:
                            st.markdown("### Address & Contact")
                            st.write(f"**Address:** {customer.get('address', 'N/A')}")
                            st.write(f"**City/Town:** {customer.get('city_town', 'N/A')}")
                            st.write(f"**Pincode:** {customer.get('pincode', 'N/A')}")
                            st.write(f"**PAN Card:** {customer.get('pan_card', 'N/A')}")
                            st.write(f"**Aadhar No:** {customer.get('aadhar_no', 'N/A')}")
                        
                        col3, col4 = st.columns(2)
                        with col3:
                            st.markdown("### Employment")
                            st.write(f"**Occupation:** {customer.get('occupation', 'N/A')}")
                            income = customer.get('annual_income')
                            st.write(f"**Annual Income:** ₹{income:,.0f}" if income else "**Annual Income:** N/A")
                        
                        with col4:
                            st.markdown("### KYC Information")
                            st.write(f"**KYC Status:** {kyc_status}")
                            app_status = customer.get('application_status', 'No Application') if customer.get('application_status') else 'No Application'
                            st.write(f"**Application Status:** {app_status}")
                            
                            # Extract KYC validation score from application notes
                            kyc_score = "N/A"
                            app_notes = customer.get('application_notes', '')
                            if app_notes and 'Overall Score:' in app_notes:
                                try:
                                    score_line = [line for line in app_notes.split('\n') if 'Overall Score:' in line]
                                    if score_line:
                                        kyc_score = score_line[0].split('Overall Score:')[1].split('%')[0].strip() + '%'
                                except:
                                    pass
                            
                            st.write(f"**KYC Validation Score:** {kyc_score}")
                            
                            # Extract and display timestamps
                            validation_time = "N/A"
                            doc_upload_time = "N/A"
                            photo_upload_time = "N/A"
                            
                            if app_notes:
                                # Extract validation time
                                if 'Validation Time:' in app_notes:
                                    try:
                                        time_line = [line for line in app_notes.split('\n') if 'Validation Time:' in line]
                                        if time_line:
                                            validation_time = time_line[0].split('Validation Time:')[1].strip()
                                    except:
                                        pass
                            
                            # Get document upload times from database
                            if customer.get('application_id'):
                                try:
                                    doc_query = """
                                        SELECT created_at, document_type, verification_status, verified_at
                                        FROM documents
                                        WHERE application_id = %s
                                        ORDER BY created_at
                                    """
                                    docs = db.execute_query(doc_query, (customer.get('application_id'),))
                                    for doc in docs:
                                        upload_time = str(doc.get('created_at', ''))[:19] if doc.get('created_at') else "N/A"
                                        
                                        if doc.get('document_type') == 'identity_proof':
                                            doc_upload_time = upload_time
                                        elif doc.get('document_type') == 'photo':
                                            photo_upload_time = upload_time
                                except:
                                    pass
                            
                            st.markdown("---")
                            st.markdown("#### ⏰ Timestamps")
                            st.write(f"**Document Upload Time:** {doc_upload_time}")
                            st.write(f"**Photo Upload Time:** {photo_upload_time}")
                            st.write(f"**Validation Time:** {validation_time}")
                            
                            if customer.get('application_id'):
                                st.write(f"**Application ID:** `{customer.get('application_id')}`")
                            
                            # Re-validate button for individual customer (using unique key)
                            if st.button(f"🔄 Re-validate KYC", key=f"revalidate_{unique_key}"):
                                if customer.get('application_id'):
                                    with st.spinner("🔄 Running advanced AI validation..."):
                                        try:
                                            # Get application_id and customer_id as UUID strings
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
                                            
                                            # Show issues if any (limit to avoid encoding issues)
                                            issues = validation_result.get('issues', [])
                                            if issues:
                                                # Filter out any non-ASCII characters from issues
                                                safe_issues = []
                                                for issue in issues[:5]:
                                                    try:
                                                        safe_issue = issue.encode('ascii', 'ignore').decode('ascii')
                                                        safe_issues.append(safe_issue)
                                                    except:
                                                        safe_issues.append(str(issue)[:50])  # Truncate if encoding fails
                                                if safe_issues:
                                                    st.warning(f"**Issues Found:** {', '.join(safe_issues)}")
                                            
                                            # Show AI features if available
                                            if validation_result.get('validation_details', {}).get('photo', {}).get('ai_features'):
                                                st.info("🤖 **AI Features Used:** Face Detection, Liveness Check, Quality Analysis")
                                            
                                            st.rerun()
                                        except Exception as e:
                                            error_msg = str(e)
                                            # Handle encoding errors gracefully
                                            try:
                                                error_msg = error_msg.encode('ascii', 'ignore').decode('ascii')
                                            except:
                                                error_msg = "Validation error occurred. Please check logs."
                                            st.error(f"❌ Error: {error_msg}")
                                            import traceback
                                            with st.expander("Error Details"):
                                                st.code(traceback.format_exc())
                                else:
                                    st.warning("⚠️ No KYC application found for this customer.")
                            
                            created = customer.get('created_at')
                            st.write(f"**Account Created:** {str(created)[:19] if created else 'N/A'}")
                            
                            # Show validation details if available
                            if app_notes and ('AUTO-VALIDATION RESULTS' in app_notes or 'ADVANCED AI-VALIDATION RESULTS' in app_notes):
                                with st.expander("📊 View Full Validation Details"):
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

