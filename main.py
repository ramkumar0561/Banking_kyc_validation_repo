
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from PIL import Image
import pytesseract
import time # For simulating OCR delay

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="Horizon Bank | KYC Portal", page_icon="🏦", layout="wide")

# Directory Setup
UPLOAD_DIR = "uploads"
DATA_FILE = "submitted_data/kyc_records.csv"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("submitted_data", exist_ok=True)

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None # 'user' or 'admin'
if "username" not in st.session_state:
    st.session_state.username = ""

# --- UTILITY FUNCTIONS ---

def save_application(data):
    """Saves application data to CSV."""
    df = pd.DataFrame([data])
    if not os.path.isfile(DATA_FILE):
        df.to_csv(DATA_FILE, index=False)
    else:
        df.to_csv(DATA_FILE, mode='a', header=False, index=False)

def load_applications():
    """Loads all applications."""
    if os.path.isfile(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Application ID", "Name", "status", "PAN", "Aadhar", "DOB"])

def update_application_status(app_id, new_status, remarks=""):
    """Updates status of an application."""
    if os.path.isfile(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "Application ID" in df.columns:
            # Locate file and update
            # Note: For CSV simplicity we just overwrite. In prod, use DB.
            df.loc[df["Application ID"] == app_id, "status"] = new_status
            if remarks:
                 df.loc[df["Application ID"] == app_id, "remarks"] = remarks
            df.to_csv(DATA_FILE, index=False)
            return True
    return False

def perform_ocr(image):
    """
    Simulates or performs OCR on an uploaded image.
    Tries to use pytesseract, falls back to mock if not installed/configured.
    """
    try:
        # Check if tesseract cmd is in path or configured. 
        # For Windows, usually needs hard path, but we try default first.
        text = pytesseract.image_to_string(image)
        if not text.strip():
            return "OCR scanned but found no text."
        return text
    except Exception as e:
        # Fallback for demo if Tesseract isn't installed
        return f"[System]: OCR Engine unavailable ({str(e)}). Manual Verification Required."

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold;}
    .success-status { color: green; font-weight: bold; }
    .pending-status { color: orange; font-weight: bold; }
    .rejected-status { color: red; font-weight: bold; }
    .sidebar .sidebar-content { background-color: #003366; color: white; }
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- PAGES ---

def login_page():
    st.markdown("## 🔐 Secure Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "Administrator"
                st.success("Welcome, Administrator!")
                st.rerun()
            elif username == "user" and password == "user123":
                st.session_state.logged_in = True
                st.session_state.user_role = "user"
                st.session_state.username = "Valued Customer"
                st.success("Welcome back!")
                st.rerun()
            else:
                st.error("Invalid credentials. Try 'admin/admin123' or 'user/user123'")

def kyc_form_page():
    st.markdown("## 📝 Digital KYC Application")
    st.info("Complete your verification in 3 easy steps.")
    
    with st.form("kyc_submission"):
        # Personal Details
        st.subheader("1. Personal Information")
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name (as per ID)")
        dob = col2.date_input("Date of Birth", min_value=date(1950, 1, 1))
        email = col1.text_input("Email Address")
        mobile = col2.text_input("Mobile Number")
        
        # ID Details
        st.subheader("2. Identity Proof")
        col3, col4 = st.columns(2)
        pan_num = col3.text_input("PAN Card Number")
        aadhar_num = col4.text_input("Aadhar Number")
        
        # Document Upload
        st.subheader("3. Document Upload")
        uploaded_file = st.file_uploader("Upload PAN or Aadhar Card (Image)", type=['png', 'jpg', 'jpeg'])
        
        consent = st.checkbox("I certify that the information provided is correct and I authorize Horizon Bank to verify these details.")
        
        submit_btn = st.form_submit_button("Submit Application")
        
        if submit_btn:
            if name and mobile and pan_num and uploaded_file and consent:
                # Save file
                file_path = os.path.join(UPLOAD_DIR, f"{mobile}_{uploaded_file.name}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Perform OCR (Simulated/Actual)
                img = Image.open(uploaded_file)
                ocr_result = perform_ocr(img)
                
                # Validation Logic (Simple check)
                status = "Pending Verification"
                if pan_num in ocr_result or aadhar_num in ocr_result:
                    ocr_match = "pass"
                else:
                    ocr_match = "fail"

                # Create Record
                app_id = f"APP-{int(time.time())}"
                record = {
                    "Application ID": app_id,
                    "Name": name,
                    "Mobile": mobile,
                    "Email": email,
                    "PAN": pan_num,
                    "Aadhar": aadhar_num,
                    "DOB": dob,
                    "File Path": file_path,
                    "OCR Text": ocr_result[:100] + "...", # Truncate for CSV
                    "OCR Match": ocr_match,
                    "status": status,
                    "Submission Date": str(date.today()),
                    "remarks": ""
                }
                
                save_application(record)
                
                st.success(f"Application {app_id} Submitted Successfully!")
                if ocr_match == "pass":
                    st.success("✅ OCR Auto-Validation: MATCH FOUND. Your application is fast-tracked.")
                else:
                    st.warning("⚠️ OCR Auto-Validation: Details unmatched. Manual review required.")
                    
            else:
                st.error("Please fill all fields and provide consent.")

def status_check_page():
    st.markdown("## 🔍 Application Status Tracker")
    app_id_input = st.text_input("Enter Application ID (e.g., APP-170...)")
    
    if st.button("Check Status"):
        df = load_applications()
        if not df.empty and app_id_input:
            match = df[df["Application ID"] == app_id_input]
            if not match.empty:
                status = match.iloc[0]["status"]
                st.info(f"Current Status: **{status}**")
                
                if status == "Approved":
                    st.balloons()
                    st.success("Congratulations! Your account is active.")
                elif status == "Rejected":
                    st.error(f"Application Rejected. Remarks: {match.iloc[0].get('remarks', 'Contact Support')}")
                else:
                    st.write("Your application is currently under review by our team.")
            else:
                st.error("Application ID not found.")
        else:
            st.warning("Please enter a valid ID or no records found.")

def admin_dashboard():
    st.markdown("## 👮‍♂️ Admin Verification Console")
    st.write("Review pending KYC applications.")
    
    df = load_applications()
    if df.empty:
        st.info("No applications found.")
        return

    # Filter for pending
    pending_apps = df 
    
    if pending_apps.empty:
        st.success("All caught up! No pending applications.")
        return
        
    for index, row in pending_apps.iterrows():
        with st.expander(f"{row['Name']} ({row['status']}) - ID: {row['Application ID']}"):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write(f"**PAN:** {row['PAN']}")
                st.write(f"**Aadhar:** {row['Aadhar']}")
                st.write(f"**OCR Result:** {row['OCR Match']}")
                st.text_area("OCR Extracted Text", row['OCR Text'], height=100, key=f"ocr_{row['Application ID']}")
            
            with col2:
                # Show Image
                if os.path.exists(row['File Path']):
                    st.image(row['File Path'], caption="Uploaded Document", use_column_width=True)
                else:
                    st.error("Image file missing.")
            
            # Action Buttons
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("✅ Approve", key=f"approve_{row['Application ID']}"):
                    update_application_status(row['Application ID'], "Approved")
                    st.success("Approved!")
                    st.rerun()
            with action_col2:
                if st.button("❌ Reject", key=f"reject_{row['Application ID']}"):
                    update_application_status(row['Application ID'], "Rejected", remarks="Doc mismatch")
                    st.error("Rejected.")
                    st.rerun()

# --- MAIN APP SHELL ---

def main():
    # Sidebar Navigation
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=80)
        st.title("Horizon Bank")
        
        if st.session_state.logged_in:
            st.write(f"User: **{st.session_state.username}**")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.rerun()
            st.divider()
        
        menu_options = ["Home", "Check Status"]
        if not st.session_state.logged_in:
            menu_options = ["Home", "Login", "Register (KYC)", "Check Status"]
        else:
            if st.session_state.user_role == "admin":
                menu_options = ["Home", "Admin Dashboard", "Check Status"]
            else:
                menu_options = ["Home", "My Profile", "Check Status"]
                
        selection = st.radio("Navigation", menu_options)
        
        st.divider()
        st.caption("© 2025 Horizon Global Bank")

    # Routing
    if selection == "Home":
        st.image("https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?q=80&w=2070&auto=format&fit=crop", use_column_width=True)
        st.markdown("# Welcome to Horizon Bank")
        st.markdown("### Banking for the Modern World.")
        st.write("Experience seamless digital banking with our state-of-the-art KYC and account management systems.")
        
    elif selection == "Login":
        login_page()
        
    elif selection == "Register (KYC)":
        kyc_form_page()
        
    elif selection == "Check Status":
        status_check_page()
        
    elif selection == "Admin Dashboard":
        if st.session_state.user_role == "admin":
            admin_dashboard()
        else:
            st.error("Access Denied. Admin only.")

if __name__ == "__main__":
    main()