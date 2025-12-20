"""
Database Helper Functions
Functions for common database operations
"""

import hashlib
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from database_config import db
import streamlit as st

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def create_user(username: str, email: str, password: str, role: str = 'customer') -> Optional[uuid.UUID]:
    """Create a new user"""
    try:
        password_hash = hash_password(password)
        query = """
            INSERT INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id
        """
        result = db.execute_one(query, (username, email, password_hash, role))
        if result:
            # Log audit
            log_audit(result['user_id'], 'login', 'user', result['user_id'], 
                     f"New user registered: {username}")
            return result['user_id']
        return None
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user and return user data"""
    try:
        query = """
            SELECT user_id, username, email, password_hash, role, is_active
            FROM users
            WHERE username = %s OR email = %s
        """
        user = db.execute_one(query, (username, username))
        
        if user and verify_password(password, user['password_hash']):
            if not user['is_active']:
                return None
            
            # Update last login
            update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s"
            db.execute_query(update_query, (user['user_id'],), fetch=False)
            
            # Log audit
            log_audit(user['user_id'], 'login', 'user', user['user_id'], 
                     f"User logged in: {username}")
            
            return {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def create_customer(user_id: uuid.UUID, customer_data: Dict[str, Any]) -> Optional[uuid.UUID]:
    """Create customer profile"""
    try:
        query = """
            INSERT INTO customers (user_id, first_name, last_name, full_name, date_of_birth, gender, 
                                 marital_status, age, address, city_town, pincode, pan_card, aadhar_no,
                                 phone_number, salary, annual_income, occupation, photo_path, kyc_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING customer_id
        """
        result = db.execute_one(query, (
            user_id,
            customer_data.get('first_name'),
            customer_data.get('last_name'),
            customer_data.get('full_name'),
            customer_data.get('date_of_birth'),
            customer_data.get('gender'),
            customer_data.get('marital_status'),
            customer_data.get('age'),
            customer_data.get('address'),
            customer_data.get('city_town'),
            customer_data.get('pincode'),
            customer_data.get('pan_card'),
            customer_data.get('aadhar_no'),
            customer_data.get('phone_number'),
            customer_data.get('salary'),
            customer_data.get('annual_income'),
            customer_data.get('occupation'),
            customer_data.get('photo_path'),
            customer_data.get('kyc_status', 'Not Submitted')
        ))
        return result['customer_id'] if result else None
    except Exception as e:
        st.error(f"Error creating customer: {str(e)}")
        return None

def update_customer_kyc(customer_id: uuid.UUID, kyc_data: Dict[str, Any]) -> bool:
    """Update customer KYC information"""
    try:
        query = """
            UPDATE customers
            SET nominee_name = %s,
                nominee_relation = %s,
                otp_verified = %s,
                kyc_status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = %s
        """
        db.execute_query(query, (
            kyc_data.get('nominee_name'),
            kyc_data.get('nominee_relation'),
            kyc_data.get('otp_verified', False),
            kyc_data.get('kyc_status', 'In Progress'),
            customer_id
        ), fetch=False)
        return True
    except Exception as e:
        st.error(f"Error updating customer KYC: {str(e)}")
        return False

def create_kyc_application(customer_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Create a new KYC application"""
    try:
        query = """
            INSERT INTO kyc_applications (customer_id, application_status)
            VALUES (%s, 'submitted')
            RETURNING application_id
        """
        result = db.execute_one(query, (customer_id,))
        if result:
            # Update customer KYC status
            update_query = "UPDATE customers SET kyc_status = 'Submitted' WHERE customer_id = %s"
            db.execute_query(update_query, (customer_id,), fetch=False)
            
            # Log audit
            log_audit(None, 'application_submit', 'application', result['application_id'],
                     f"New KYC application submitted")
            return result['application_id']
        return None
    except Exception as e:
        st.error(f"Error creating KYC application: {str(e)}")
        return None

def save_document(application_id: uuid.UUID, document_type: str, 
                 document_name: str, file_path: str, file_size: int, 
                 mime_type: str, ocr_data: Dict = None) -> Optional[uuid.UUID]:
    """Save document information to database"""
    try:
        import json
        ocr_json = json.dumps(ocr_data) if ocr_data else None
        
        query = """
            INSERT INTO documents (application_id, document_type, document_name, 
                                 file_path, file_size, mime_type, ocr_extracted_data, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING document_id
        """
        result = db.execute_one(query, (
            application_id, document_type, document_name, 
            file_path, file_size, mime_type, ocr_json
        ))
        if result:
            # Log audit
            log_audit(None, 'document_upload', 'document', result['document_id'],
                     f"Document uploaded: {document_name}")
            return result['document_id']
        return None
    except Exception as e:
        st.error(f"Error saving document: {str(e)}")
        return None

def get_customer_kyc_status(customer_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get KYC application status for a customer"""
    try:
        query = """
            SELECT ka.*, 
                   COUNT(DISTINCT d.document_id) as total_documents,
                   COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END) as verified_documents
            FROM kyc_applications ka
            LEFT JOIN documents d ON ka.application_id = d.application_id
            WHERE ka.customer_id = %s
            ORDER BY ka.submission_date DESC
            LIMIT 1
        """
        return db.execute_one(query, (customer_id,))
    except Exception as e:
        st.error(f"Error fetching KYC status: {str(e)}")
        return None

def get_customer_documents(application_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get all documents for an application"""
    try:
        query = """
            SELECT document_id, document_type, document_name, file_path, 
                   verification_status, verification_notes, created_at
            FROM documents
            WHERE application_id = %s
            ORDER BY created_at DESC
        """
        return db.execute_query(query, (application_id,))
    except Exception as e:
        st.error(f"Error fetching documents: {str(e)}")
        return []

def get_customer_by_email_or_phone(identifier: str) -> Optional[Dict[str, Any]]:
    """Get customer by email or phone number"""
    try:
        query = """
            SELECT c.*, u.email, u.username, u.role
            FROM customers c
            LEFT JOIN users u ON c.user_id = u.user_id
            WHERE u.email = %s OR c.phone_number = %s
        """
        return db.execute_one(query, (identifier, identifier))
    except Exception as e:
        return None

def log_audit(user_id: Optional[uuid.UUID], action_type: str, entity_type: str,
             entity_id: Optional[uuid.UUID], description: str, 
             ip_address: str = None, user_agent: str = None):
    """Log audit trail"""
    try:
        query = """
            INSERT INTO audit_logs (user_id, action_type, entity_type, entity_id, 
                                  description, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        db.execute_query(query, (user_id, action_type, entity_type, entity_id, 
                                description, ip_address, user_agent), fetch=False)
    except Exception as e:
        # Don't show error for audit logging failures
        pass

def create_notification(customer_id: uuid.UUID, notification_type: str, 
                        title: str, message: str):
    """Create a notification for customer"""
    try:
        query = """
            INSERT INTO notifications (customer_id, notification_type, title, message)
            VALUES (%s, %s, %s, %s)
        """
        db.execute_query(query, (customer_id, notification_type, title, message), fetch=False)
    except Exception as e:
        st.error(f"Error creating notification: {str(e)}")

def get_customer_by_user_id(user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get customer by user_id"""
    try:
        query = "SELECT * FROM customers WHERE user_id = %s"
        return db.execute_one(query, (user_id,))
    except Exception as e:
        st.error(f"Error fetching customer: {str(e)}")
        return None

def check_application_status(identifier: str, identifier_type: str = 'email') -> Dict[str, Any]:
    """Check application status - returns status code and message"""
    try:
        # Check which columns exist in customers table
        check_cols_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'customers'
        """
        existing_cols = db.execute_all(check_cols_query)
        col_names = {row['column_name'] for row in existing_cols} if existing_cols else set()
        
        # Build column list dynamically based on what exists
        base_cols = ['customer_id', 'user_id', 'full_name', 'date_of_birth', 'gender', 
                     'age', 'address', 'city_town', 'pincode', 'pan_card', 'aadhar_no', 
                     'phone_number', 'created_at', 'updated_at']
        
        optional_cols = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'marital_status': 'marital_status',
            'salary': 'salary',
            'annual_income': 'annual_income',
            'occupation': 'occupation',
            'photo_path': 'photo_path',
            'nominee_name': 'nominee_name',
            'nominee_relation': 'nominee_relation',
            'otp_verified': 'otp_verified',
            'kyc_status': 'kyc_status'
        }
        
        # Select only columns that exist
        select_cols = [f"c.{col}" for col in base_cols if col in col_names]
        for col_key, col_name in optional_cols.items():
            if col_name in col_names:
                select_cols.append(f"c.{col_name}")
            elif col_key == 'kyc_status':
                select_cols.append("'Not Submitted' as kyc_status")
        
        select_list = ", ".join(select_cols)
        
        if identifier_type == 'email':
            query = f"""
                SELECT {select_list},
                       u.email, u.username, ka.application_id, ka.application_status
                FROM customers c
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN kyc_applications ka ON c.customer_id = ka.customer_id
                WHERE u.email = %s
                ORDER BY ka.submission_date DESC NULLS LAST
                LIMIT 1
            """
        else:  # phone
            query = f"""
                SELECT {select_list},
                       u.email, u.username, ka.application_id, ka.application_status
                FROM customers c
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN kyc_applications ka ON c.customer_id = ka.customer_id
                WHERE c.phone_number = %s
                ORDER BY ka.submission_date DESC NULLS LAST
                LIMIT 1
            """
        
        result = db.execute_one(query, (identifier,))
        
        if not result:
            return {
                'status': 'A',
                'message': 'No account found with these details.',
                'data': None
            }
        
        # Check KYC status
        kyc_status = result.get('kyc_status', 'Not Submitted')
        application_status = result.get('application_status')
        
        if kyc_status == 'Not Submitted' or not application_status:
            return {
                'status': 'C',
                'message': 'Application Details Found. Status: 📄 KYC not submitted, action required.',
                'data': result
            }
        elif application_status in ['submitted', 'under_review', 'document_verification', 'pending_resubmission']:
            return {
                'status': 'D',
                'message': 'Application Details Found. Status: 📄 KYC submitted, verification in progress.',
                'data': result
            }
        elif application_status == 'approved':
            return {
                'status': 'E',
                'message': 'Application Details Found. Status: ✅ KYC Verified & Account Fully Active.',
                'data': result
            }
        else:
            return {
                'status': 'D',
                'message': f'Application Details Found. Status: 📄 {application_status.replace("_", " ").title()}.',
                'data': result
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error checking status: {str(e)}',
            'data': None
        }

