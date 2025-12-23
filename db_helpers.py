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

def check_username_exists(username: str) -> bool:
    """Check if username already exists"""
    try:
        query = "SELECT user_id FROM users WHERE username = %s"
        result = db.execute_one(query, (username,))
        return result is not None
    except:
        return False

def check_email_exists(email: str) -> bool:
    """Check if email already exists"""
    try:
        query = "SELECT user_id FROM users WHERE email = %s"
        result = db.execute_one(query, (email,))
        return result is not None
    except:
        return False

def check_phone_exists(phone: str) -> bool:
    """Check if phone number already exists"""
    try:
        query = "SELECT customer_id FROM customers WHERE phone_number = %s"
        result = db.execute_one(query, (phone,))
        return result is not None
    except:
        return False

def check_pan_exists(pan: str) -> bool:
    """Check if PAN card already exists"""
    try:
        if not pan or pan.strip() == "":
            return False
        query = "SELECT customer_id FROM customers WHERE pan_card = %s AND pan_card IS NOT NULL AND pan_card != ''"
        result = db.execute_one(query, (pan.strip(),))
        return result is not None
    except:
        return False

def check_aadhar_exists(aadhar: str) -> bool:
    """Check if Aadhar number already exists"""
    try:
        if not aadhar or aadhar.strip() == "":
            return False
        query = "SELECT customer_id FROM customers WHERE aadhar_no = %s AND aadhar_no IS NOT NULL AND aadhar_no != ''"
        result = db.execute_one(query, (aadhar.strip(),))
        return result is not None
    except:
        return False

def create_user(username: str, email: str, password: str, role: str = 'customer') -> Optional[uuid.UUID]:
    """Create a new user"""
    try:
        # Check if username already exists
        if check_username_exists(username):
            st.error(f"❌ Username '{username}' already exists. Please choose a different username.")
            return None
        
        # Check if email already exists
        if check_email_exists(email):
            st.error(f"❌ Email '{email}' is already registered. Please use a different email or login.")
            return None
        
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
        # Check if error is due to unique constraint
        error_msg = str(e).lower()
        if 'unique' in error_msg or 'duplicate' in error_msg:
            if 'username' in error_msg:
                st.error(f"❌ Username '{username}' already exists. Please choose a different username.")
            elif 'email' in error_msg:
                st.error(f"❌ Email '{email}' is already registered. Please use a different email.")
        else:
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

def admin_approve_kyc(application_id: uuid.UUID, customer_id: uuid.UUID, admin_user_id: Optional[uuid.UUID], admin_notes: str = "") -> bool:
    """Admin manually approves KYC application"""
    try:
        # Update KYC application status
        if admin_user_id:
            update_query = """
                UPDATE kyc_applications 
                SET application_status = 'approved',
                    verification_date = CURRENT_TIMESTAMP,
                    verified_by = %s,
                    notes = %s
                WHERE application_id = %s
            """
            notes = f"Manually approved by admin. {admin_notes}".strip()
            db.execute_query(update_query, (admin_user_id, notes, application_id), fetch=False)
        else:
            # If no admin_user_id, don't set verified_by
            update_query = """
                UPDATE kyc_applications 
                SET application_status = 'approved',
                    verification_date = CURRENT_TIMESTAMP,
                    notes = %s
                WHERE application_id = %s
            """
            notes = f"Manually approved by admin. {admin_notes}".strip()
            db.execute_query(update_query, (notes, application_id), fetch=False)
        
        # Update customer KYC status
        customer_update = "UPDATE customers SET kyc_status = 'Approved' WHERE customer_id = %s"
        db.execute_query(customer_update, (customer_id,), fetch=False)
        
        # Update all documents to verified
        doc_update = """
            UPDATE documents 
            SET verification_status = 'verified',
                verified_at = CURRENT_TIMESTAMP,
                verification_notes = 'Approved by admin'
            WHERE application_id = %s
        """
        db.execute_query(doc_update, (application_id,), fetch=False)
        
        # Log audit (admin_user_id can be None)
        log_audit(admin_user_id, 'kyc_approve', 'application', application_id, 
                 f"Admin approved KYC for customer {customer_id}")
        return True
    except Exception as e:
        st.error(f"Error approving KYC: {str(e)}")
        return False

def admin_reject_kyc(application_id: uuid.UUID, customer_id: uuid.UUID, admin_user_id: Optional[uuid.UUID], rejection_reason: str) -> bool:
    """Admin manually rejects KYC application"""
    try:
        # Update KYC application status
        if admin_user_id:
            update_query = """
                UPDATE kyc_applications 
                SET application_status = 'rejected',
                    verification_date = CURRENT_TIMESTAMP,
                    verified_by = %s,
                    rejection_reason = %s,
                    notes = %s
                WHERE application_id = %s
            """
            notes = f"Manually rejected by admin. Reason: {rejection_reason}"
            db.execute_query(update_query, (admin_user_id, rejection_reason, notes, application_id), fetch=False)
        else:
            # If no admin_user_id, don't set verified_by
            update_query = """
                UPDATE kyc_applications 
                SET application_status = 'rejected',
                    verification_date = CURRENT_TIMESTAMP,
                    rejection_reason = %s,
                    notes = %s
                WHERE application_id = %s
            """
            notes = f"Manually rejected by admin. Reason: {rejection_reason}"
            db.execute_query(update_query, (rejection_reason, notes, application_id), fetch=False)
        
        # Update customer KYC status
        customer_update = "UPDATE customers SET kyc_status = 'Rejected' WHERE customer_id = %s"
        db.execute_query(customer_update, (customer_id,), fetch=False)
        
        # Log audit
        log_audit(admin_user_id, 'kyc_rejection', 'kyc_application', application_id, 
                 f"KYC rejected by admin. Reason: {rejection_reason}")
        
        return True
    except Exception as e:
        st.error(f"Error rejecting KYC: {str(e)}")
        return False

def admin_reject_document(document_id: uuid.UUID, application_id: uuid.UUID, customer_id: uuid.UUID, 
                         admin_user_id: Optional[uuid.UUID], rejection_reason: str, document_type: str) -> bool:
    """Admin manually rejects a specific document (photo or identity_proof)"""
    try:
        # Update document verification status to rejected
        doc_update_query = """
            UPDATE documents 
            SET verification_status = 'rejected',
                verification_notes = %s,
                verified_at = CURRENT_TIMESTAMP
            WHERE document_id = %s
        """
        notes = f"Manually rejected by admin. Reason: {rejection_reason}. Document Type: {document_type}"
        db.execute_query(doc_update_query, (notes, document_id), fetch=False)
        
        # Update KYC application to indicate partial rejection
        app_update_query = """
            UPDATE kyc_applications 
            SET application_status = 'pending_resubmission',
                notes = COALESCE(notes || E'\\n', '') || %s
            WHERE application_id = %s
        """
        rejection_note = f"Document rejected: {document_type}. Reason: {rejection_reason}. Customer needs to resubmit this document."
        db.execute_query(app_update_query, (rejection_note, application_id), fetch=False)
        
        # Update customer KYC status to indicate resubmission needed
        customer_update = "UPDATE customers SET kyc_status = 'Pending Resubmission' WHERE customer_id = %s"
        db.execute_query(customer_update, (customer_id,), fetch=False)
        
        # Log audit
        log_audit(admin_user_id, 'document_rejection', 'document', document_id, 
                 f"Document {document_type} rejected by admin. Reason: {rejection_reason}")
        
        return True
    except Exception as e:
        st.error(f"Error rejecting document: {str(e)}")
        return False
        
        # Update all documents to rejected
        doc_update = """
            UPDATE documents 
            SET verification_status = 'rejected',
                verified_at = CURRENT_TIMESTAMP,
                verification_notes = %s
            WHERE application_id = %s
        """
        rejection_note = f"Rejected by admin: {rejection_reason}"
        db.execute_query(doc_update, (rejection_note, application_id), fetch=False)
        
        # Log audit (admin_user_id can be None)
        log_audit(admin_user_id, 'kyc_reject', 'application', application_id, 
                 f"Admin rejected KYC for customer {customer_id}. Reason: {rejection_reason}")
        return True
    except Exception as e:
        st.error(f"Error rejecting KYC: {str(e)}")
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
            SELECT ka.application_id, ka.customer_id, ka.application_status, 
                   ka.submission_date, ka.verification_date, ka.verified_by,
                   ka.rejection_reason, ka.notes, ka.created_at, ka.updated_at,
                   COUNT(DISTINCT d.document_id) as total_documents,
                   COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END) as verified_documents
            FROM kyc_applications ka
            LEFT JOIN documents d ON ka.application_id = d.application_id
            WHERE ka.customer_id = %s
            GROUP BY ka.application_id, ka.customer_id, ka.application_status, 
                     ka.submission_date, ka.verification_date, ka.verified_by,
                     ka.rejection_reason, ka.notes, ka.created_at, ka.updated_at
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
        # Convert UUID to string for database query
        app_id_str = str(application_id) if isinstance(application_id, uuid.UUID) else application_id
        query = """
            SELECT document_id, document_type, document_name, file_path, 
                   verification_status, verification_notes, created_at
            FROM documents
            WHERE application_id = %s
            ORDER BY created_at DESC
        """
        return db.execute_query(query, (app_id_str,))
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
        existing_cols = db.execute_query(check_cols_query, fetch=True)
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
                       u.email, u.username, ka.application_id, ka.application_status,
                       ka.submission_date, ka.notes, ka.rejection_reason,
                       COALESCE(COUNT(DISTINCT d.document_id), 0) as total_documents,
                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END), 0) as verified_documents,
                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END), 0) as rejected_documents,
                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'pending' OR d.verification_status IS NULL THEN d.document_id END), 0) as pending_documents
                FROM customers c
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN kyc_applications ka ON c.customer_id = ka.customer_id
                LEFT JOIN documents d ON ka.application_id = d.application_id
                WHERE u.email = %s
                GROUP BY {select_list}, u.email, u.username, ka.application_id, ka.application_status, ka.submission_date, ka.notes, ka.rejection_reason
                ORDER BY ka.submission_date DESC NULLS LAST
                LIMIT 1
            """
        else:  # phone
            query = f"""
                SELECT {select_list},
                       u.email, u.username, ka.application_id, ka.application_status,
                       ka.submission_date, ka.notes, ka.rejection_reason,
                       COALESCE(COUNT(DISTINCT d.document_id), 0) as total_documents,
                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END), 0) as verified_documents,
                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END), 0) as rejected_documents,
                       COALESCE(COUNT(DISTINCT CASE WHEN d.verification_status = 'pending' OR d.verification_status IS NULL THEN d.document_id END), 0) as pending_documents
                FROM customers c
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN kyc_applications ka ON c.customer_id = ka.customer_id
                LEFT JOIN documents d ON ka.application_id = d.application_id
                WHERE c.phone_number = %s
                GROUP BY {select_list}, u.email, u.username, ka.application_id, ka.application_status, ka.submission_date, ka.notes, ka.rejection_reason
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

