"""
Horizon Bank - Professional Banking Portal
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

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Horizon Bank | Professional Banking", 
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
        st.write(f"**KYC Status:** {kyc_status}")
        st.write(f"**Application Status:** {status}")
        st.write(f"**Submitted:** {result.get('submission_date', 'N/A')}")
        if result.get('verification_date'):
            st.write(f"**Verified:** {result.get('verification_date')}")
        if result.get('rejection_reason'):
            st.error(f"**Rejection Reason:** {result.get('rejection_reason')}")
    
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
            <h1 style='color: #ffffff; font-size: 2rem; font-weight: 800; margin: 0;'>🏦 HORIZON</h1>
            <p style='color: #94a3b8; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>Professional Banking</p>
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
    
    st.markdown("---")
    st.info("🔒 Secure 256-bit Encryption")
    st.caption("📞 1-800-HORIZON")
    st.caption("📧 support@horizonbank.com")

# --- LANDING PAGE ---
if st.session_state.view == "Landing":
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo'>HORIZON BANK</h1>
            <p class='bank-tagline'>Experience Banking Reimagined | Trusted by Millions</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick Actions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔐 Login", use_container_width=True, type="primary"):
            change_view("Login")
    with col2:
        if st.button("✨ Open Account", use_container_width=True):
            change_view("Register")
    with col3:
        if st.button("📊 Check Status", use_container_width=True):
            change_view("StatusCheck")
    with col4:
        if st.button("📱 Mobile App", use_container_width=True):
            st.info("Download our mobile app from App Store or Google Play")
    
    # Services Grid
    st.markdown("### Our Services")
    col1, col2, col3, col4 = st.columns(4)
    
    services = [
        ("🏦", "Personal Banking", "Savings, Current & More"),
        ("💳", "Credit Cards", "Rewards & Cashback"),
        ("📈", "Investments", "Mutual Funds & Stocks"),
        ("🏠", "Loans", "Home, Personal & Business"),
    ]
    
    for i, (icon, title, desc) in enumerate(services):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
                <div class='service-grid-card'>
                    <span class='service-icon-large' style='font-size: 5rem;'>{icon}</span>
                    <div class='service-title'>{title}</div>
                    <div class='service-description'>{desc}</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Stats
    # 1. Spacer for breathing room
    st.markdown("<br><br>", unsafe_allow_html=True)

    # 2. Modern Stats Section with Custom Background
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
            padding: 60px 20px; 
            border-radius: 24px; 
            margin: 40px 0;
            text-align: center;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        ">
            <h2 style="color: #f8fafc; font-size: 2.2rem; margin-bottom: 40px; font-weight: 700;">
                The Horizon Advantage
            </h2>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">
                <div class="stat-item">
                    <div style="font-size: 3rem; font-weight: 800; color: #38bdf8;">5M+</div>
                    <div style="color: #94a3b8; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;">Active Customers</div>
                </div>
                <div class="stat-item">
                    <div style="font-size: 3rem; font-weight: 800; color: #38bdf8;">2,500+</div>
                    <div style="color: #94a3b8; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;">Global Branches</div>
                </div>
                <div class="stat-item">
                    <div style="font-size: 3rem; font-weight: 800; color: #38bdf8;">4.9★</div>
                    <div style="color: #94a3b8; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;">App Rating</div>
                </div>
                <div class="stat-item">
                    <div style="font-size: 3rem; font-weight: 800; color: #38bdf8;">24/7</div>
                    <div style="color: #94a3b8; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;">Expert Support</div>
                </div>
            </div>
        </div>

        <style>
            .stat-item {
                flex: 1;
                min-width: 200px;
                padding: 20px;
                transition: transform 0.3s ease;
            }
            .stat-item:hover {
                transform: translateY(-10px);
            }
        </style>
    """, unsafe_allow_html=True)

    # 3. Another spacer after the stats
    st.markdown("<br><br>", unsafe_allow_html=True)
    


    # Footer
    st.markdown("""
        <div class='bank-footer'>
            <p style='font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;'>Horizon Bank - Banking Made Beautiful</p>
            <div class='footer-links'>
                <a href='#' class='footer-link'>Privacy Policy</a>
                <a href='#' class='footer-link'>Terms & Conditions</a>
                <a href='#' class='footer-link'>About Us</a>
                <a href='#' class='footer-link'>Contact</a>
            </div>
            <p style='margin-top: 1.5rem; color: #64748b;'>© 2025 Horizon Bank. All Rights Reserved</p>
        </div>
    """, unsafe_allow_html=True)

# --- REGISTRATION PAGE (Initial Entry - Progressive KYC Step 1) ---
elif st.session_state.view == "Register":
    st.markdown("""
        <div class='bank-header-main'>
            <h1 class='bank-logo' style='font-size: 2.5rem;'>Open Your Account</h1>
            <p class='bank-tagline'>Step 1: Create Your Account</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        
        st.info("ℹ️ **Registration Process:** After creating your account, you'll complete KYC verification on your first login.")
        
        with st.form("register_form", clear_on_submit=False):
            st.markdown("### 👤 Personal Information")
            st.markdown("<p style='color: #ef4444; font-size: 0.9rem;'>* Indicates mandatory fields</p>", unsafe_allow_html=True)
            
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
                # Validation
                missing_fields = []
                if not first_name: missing_fields.append("First Name")
                if not last_name: missing_fields.append("Last Name")
                if not email: missing_fields.append("Email")
                if not phone: missing_fields.append("Phone Number")
                if not gender or gender == "": missing_fields.append("Gender")
                if not marital_status or marital_status == "": missing_fields.append("Marital Status")
                if not occupation: missing_fields.append("Occupation")
                if not salary or salary == 0: missing_fields.append("Monthly Salary")
                if not annual_income or annual_income == 0: missing_fields.append("Annual Income")
                if not username: missing_fields.append("Username")
                if not password: missing_fields.append("Password")
                if not address: missing_fields.append("Address")
                if not city: missing_fields.append("City")
                if not pincode: missing_fields.append("Pincode")
                if not consent: missing_fields.append("Terms & Conditions consent")
                
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
    
    with st.container():
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        
        st.info("ℹ️ **KYC Verification:** Complete identity verification and photo upload to activate your account.")
        
        with st.form("kyc_portal_form", clear_on_submit=False):
            st.markdown("### 📄 Identity Verification (Mandatory)")
            st.markdown("<p style='color: #ef4444; font-size: 0.9rem;'>* Indicates mandatory fields</p>", unsafe_allow_html=True)
            
            doc_type = st.selectbox("Document Type*", ["", "Aadhar Card", "PAN Card", "Passport", "Voter ID"])
            identity_doc = st.file_uploader(f"Upload {doc_type if doc_type else 'Identity Document'}*", 
                                          type=["pdf", "jpg", "png", "jpeg"],
                                          help="Upload a clear scan of your identity document")
            
            if identity_doc:
                st.success(f"✅ File uploaded: {identity_doc.name} ({identity_doc.size / 1024:.1f} KB)")
            
            st.markdown("### 📸 Photo Identification (Mandatory)")
            photo_mode = st.radio("Choose Photo Method*", ["Upload from Local", "Use Web Cam"], horizontal=True, key="photo_method")
            user_photo = None
            
            if photo_mode == "Upload from Local":
                user_photo = st.file_uploader("Upload your photo* (JPG/PNG, Max 2MB)", 
                                             type=["jpg", "jpeg", "png"],
                                             help="Upload a recent passport-size photograph")
                if user_photo:
                    st.success(f"✅ Photo uploaded: {user_photo.name}")
            elif photo_mode == "Use Web Cam":
                st.info("📷 **Webcam Instructions:**\n1. Click 'Take Photo' button below\n2. Position your face in the frame\n3. If camera doesn't work, switch to 'Upload from Local'")
                user_photo = handle_webcam_capture()
                if user_photo:
                    st.success("✅ Photo captured successfully")
            
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
                if not user_photo: missing_fields.append("Photo")
                
                if missing_fields:
                    st.error(f"❌ **Please complete all mandatory fields:**\n\n" + "\n".join([f"• {field}" for field in missing_fields]))
                    if not user_photo:
                        st.warning("⚠️ **Photo not uploaded!** Please upload your photo or use webcam to take a photo.")
                elif not db_connected:
                    st.error("❌ Database not connected.")
                else:
                    try:
                        # Save photo
                        photo_path = None
                        if user_photo:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            photo_filename = f"photo_{timestamp}_{customer_id}.{user_photo.name.split('.')[-1] if '.' in user_photo.name else 'jpg'}"
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
                            
                            # Save photo as document
                            if photo_path:
                                save_document(application_id, 'photo', f"photo_{customer_id}.jpg",
                                            photo_path, user_photo.size if user_photo else 0, 
                                            user_photo.type if user_photo else 'image/jpeg')
                            
                            # Update customer KYC data
                            kyc_data = {
                                'nominee_name': nominee_name if nominee_name else None,
                                'nominee_relation': nominee_relation if nominee_relation else None,
                                'otp_verified': otp_verified,
                                'kyc_status': 'Submitted'
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
                            
                            # Refresh customer data
                            st.session_state.customer = get_customer_by_user_id(st.session_state.user['user_id'])
                            
                            create_notification(customer_id, 'kyc_submitted', 
                                              'KYC Submitted', 
                                              f'Your KYC application has been submitted. Application ID: {application_id}')
                            
                            notifications.toast_success("KYC application submitted successfully!")
                            st.success(f"✅ **KYC Application Submitted Successfully!**\n\n**Application ID:** `{application_id}`\n\nYour application is now under review.")
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
                            existing_cols = db.execute_all(check_cols_query)
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

# --- ADMIN DASHBOARD (Integrated) ---
elif st.session_state.view == "Admin":
    if not st.session_state.authenticated:
        change_view("Login")
        st.stop()
    
    if st.session_state.user.get('role') != 'admin':
        st.error("❌ Access Denied. Admin privileges required.")
        change_view("Dashboard")
        st.stop()
    
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

