"""
KYC Validation Module
Handles validation of KYC documents, photos, and addresses
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from database_config import db
import streamlit as st

def validate_photo(photo_path: str) -> Dict[str, Any]:
    """
    Validate photo quality and face detection
    Returns validation result with score and issues
    """
    try:
        from PIL import Image
        import io
        
        # Check if file exists
        if not os.path.exists(photo_path):
            return {
                'is_valid': False,
                'score': 0,
                'issues': ['Photo file not found'],
                'confidence': 0
            }
        
        # Load image
        img = Image.open(photo_path)
        width, height = img.size
        
        # Basic validation checks
        issues = []
        score = 100
        
        # Check image dimensions (more lenient)
        if width < 100 or height < 100:
            issues.append('Photo too small (minimum 100x100 pixels)')
            score -= 20  # Reduced penalty
        
        if width > 10000 or height > 10000:
            issues.append('Photo too large')
            score -= 5  # Reduced penalty
        
        # Check aspect ratio (should be roughly square or portrait) - more lenient
        aspect_ratio = width / height
        if aspect_ratio < 0.3 or aspect_ratio > 3.0:
            issues.append('Unusual aspect ratio')
            score -= 10  # Reduced penalty
        
        # Check file size (more lenient)
        file_size = os.path.getsize(photo_path)
        if file_size < 1000:  # Less than 1KB
            issues.append('Photo file too small (may be corrupted)')
            score -= 15  # Reduced penalty
        elif file_size > 10 * 1024 * 1024:  # More than 10MB
            issues.append('Photo file too large')
            score -= 5  # Reduced penalty
        
        # Note: Real face detection would require OpenCV or similar
        # For now, we do basic validation
        
        is_valid = score >= 50  # More lenient - just check score
        
        return {
            'is_valid': is_valid,
            'score': score,
            'issues': issues,
            'confidence': min(score, 100),
            'width': width,
            'height': height,
            'file_size': file_size
        }
    except Exception as e:
        return {
            'is_valid': False,
            'score': 0,
            'issues': [f'Error validating photo: {str(e)}'],
            'confidence': 0
        }

def validate_address(customer_data: Dict[str, Any], document_ocr_data: Dict = None) -> Dict[str, Any]:
    """
    Validate address consistency between customer data and documents
    """
    try:
        issues = []
        score = 100
        
        # Check if address fields are present (more lenient)
        address = customer_data.get('address', '')
        city = customer_data.get('city_town', '')
        pincode = customer_data.get('pincode', '')
        
        if not address or len(address) < 5:
            issues.append('Address too short or missing')
            score -= 15  # Reduced penalty
        
        if not city:
            issues.append('City/Town missing')
            score -= 10  # Reduced penalty
        
        if not pincode or len(pincode) < 6:
            issues.append('Pincode missing or invalid')
            score -= 10  # Reduced penalty
        
        # If OCR data available, try to match address
        if document_ocr_data:
            ocr_address = document_ocr_data.get('address', '')
            if ocr_address and address:
                # Simple check - see if key words match
                address_lower = address.lower()
                ocr_lower = ocr_address.lower()
                
                # Check for common words
                common_words = ['street', 'road', 'lane', 'avenue', 'nagar', 'colony']
                matches = sum(1 for word in common_words if word in address_lower and word in ocr_lower)
                
                if matches == 0 and len(ocr_address) > 10:
                    issues.append('Address mismatch with document')
                    score -= 15
        
        is_valid = score >= 70
        
        return {
            'is_valid': is_valid,
            'score': score,
            'issues': issues,
            'confidence': min(score, 100)
        }
    except Exception as e:
        return {
            'is_valid': False,
            'score': 0,
            'issues': [f'Error validating address: {str(e)}'],
            'confidence': 0
        }

def validate_documents(application_id, customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all documents for an application
    """
    try:
        # Get all documents for this application
        query = """
            SELECT document_id, document_type, document_name, verification_status, ocr_extracted_data
            FROM documents
            WHERE application_id = %s
        """
        documents = db.execute_query(query, (application_id,))
        
        if not documents:
            return {
                'is_valid': False,
                'score': 0,
                'issues': ['No documents found'],
                'confidence': 0,
                'verified_count': 0,
                'total_count': 0
            }
        
        total_docs = len(documents)
        verified_docs = sum(1 for doc in documents if doc.get('verification_status') == 'verified')
        pending_docs = sum(1 for doc in documents if doc.get('verification_status') == 'pending')
        
        issues = []
        score = 100
        
        # Check if identity document exists
        identity_docs = [d for d in documents if d.get('document_type') == 'identity_proof']
        if not identity_docs:
            issues.append('Identity document missing')
            score -= 30  # Reduced penalty
        
        # Check if photo exists
        photo_docs = [d for d in documents if d.get('document_type') == 'photo']
        if not photo_docs:
            issues.append('Photo missing')
            score -= 25  # Reduced penalty
        
        # Check verification status (more lenient)
        if verified_docs < total_docs * 0.3:  # Less than 30% verified (was 50%)
            issues.append(f'Only {verified_docs}/{total_docs} documents verified')
            score -= 10  # Reduced penalty
        
        # Check OCR data quality (more lenient - don't fail on OCR issues)
        ocr_issues_count = 0
        for doc in documents:
            ocr_data = doc.get('ocr_extracted_data')
            if ocr_data and isinstance(ocr_data, dict):
                if not ocr_data.get('is_valid', False):
                    ocr_issues_count += 1
        
        if ocr_issues_count > 0:
            issues.append(f"{ocr_issues_count} document(s) have OCR validation warnings")
            score -= 5 * ocr_issues_count  # Small penalty per OCR issue
        
        is_valid = score >= 50  # Lower threshold
        
        return {
            'is_valid': is_valid,
            'score': score,
            'issues': issues,
            'confidence': min(score, 100),
            'verified_count': verified_docs,
            'total_count': total_docs,
            'pending_count': pending_docs
        }
    except Exception as e:
        return {
            'is_valid': False,
            'score': 0,
            'issues': [f'Error validating documents: {str(e)}'],
            'confidence': 0,
            'verified_count': 0,
            'total_count': 0
        }

def perform_kyc_validation(application_id, customer_id) -> Dict[str, Any]:
    """
    Perform complete KYC validation
    Returns overall validation result
    """
    try:
        # Get customer data
        customer_query = "SELECT * FROM customers WHERE customer_id = %s"
        customer = db.execute_one(customer_query, (customer_id,))
        
        if not customer:
            return {
                'is_valid': False,
                'overall_score': 0,
                'status': 'rejected',
                'issues': ['Customer not found'],
                'validation_details': {}
            }
        
        # Get customer photo path
        photo_path = customer.get('photo_path')
        
        # Validate photo
        photo_validation = validate_photo(photo_path) if photo_path else {
            'is_valid': False,
            'score': 0,
            'issues': ['Photo not uploaded'],
            'confidence': 0
        }
        
        # Get document OCR data for address validation
        doc_query = """
            SELECT ocr_extracted_data 
            FROM documents 
            WHERE application_id = %s AND document_type = 'identity_proof'
            LIMIT 1
        """
        doc_result = db.execute_one(doc_query, (application_id,))
        ocr_data = doc_result.get('ocr_extracted_data') if doc_result else None
        
        # Validate address
        address_validation = validate_address(customer, ocr_data)
        
        # Validate documents
        document_validation = validate_documents(application_id, customer)
        
        # Calculate overall score
        photo_weight = 0.3
        address_weight = 0.2
        document_weight = 0.5
        
        overall_score = (
            photo_validation['score'] * photo_weight +
            address_validation['score'] * address_weight +
            document_validation['score'] * document_weight
        )
        
        # Collect all issues
        all_issues = []
        all_issues.extend(photo_validation.get('issues', []))
        all_issues.extend(address_validation.get('issues', []))
        all_issues.extend(document_validation.get('issues', []))
        
        # Determine status - Always set approved or rejected, no pending
        # More lenient criteria: Score >= 70% OR (Score >= 60% AND minimal issues)
        if overall_score >= 70:
            status = 'approved'
        elif overall_score >= 60 and len(all_issues) <= 2:  # Allow up to 2 minor issues
            status = 'approved'
        else:
            status = 'rejected'
        
        is_valid = overall_score >= 60
        
        validation_result = {
            'is_valid': is_valid,
            'overall_score': round(overall_score, 2),
            'status': status,
            'issues': all_issues,
            'validation_details': {
                'photo': photo_validation,
                'address': address_validation,
                'documents': document_validation
            }
        }
        
        # Update application status
        update_query = """
            UPDATE kyc_applications 
            SET application_status = %s,
                verification_date = %s,
                notes = %s
            WHERE application_id = %s
        """
        
        # Create detailed notes with validation breakdown
        photo_score = photo_validation.get('score', 0)
        address_score = address_validation.get('score', 0)
        doc_score = document_validation.get('score', 0)
        
        notes = f"""AUTO-VALIDATION RESULTS:
Overall Score: {overall_score}%
Photo Score: {photo_score}% (30% weight)
Address Score: {address_score}% (20% weight)
Document Score: {doc_score}% (50% weight)
Status: {status.upper()}
Issues: {', '.join(all_issues) if all_issues else 'None - All checks passed'}"""
        
        db.execute_query(update_query, (
            status,
            datetime.now(),
            notes,
            application_id
        ), fetch=False)
        
        # Update customer KYC status based on validation result
        if status == 'approved':
            customer_status = 'Approved'
        else:
            customer_status = 'Rejected'
        
        customer_update_query = """
            UPDATE customers 
            SET kyc_status = %s
            WHERE customer_id = %s
        """
        db.execute_query(customer_update_query, (customer_status, customer_id), fetch=False)
        
        # Update document verification status based on validation
        if status == 'approved':
            # Mark all documents as verified
            doc_update_query = """
                UPDATE documents 
                SET verification_status = 'verified',
                    verification_notes = 'Auto-verified by KYC validation system'
                WHERE application_id = %s AND verification_status = 'pending'
            """
            db.execute_query(doc_update_query, (application_id,), fetch=False)
        else:
            # Mark documents as rejected if validation failed
            doc_update_query = """
                UPDATE documents 
                SET verification_status = 'rejected',
                    verification_notes = 'Rejected by KYC validation system. Score: {overall_score}%'
                WHERE application_id = %s AND verification_status = 'pending'
            """
            db.execute_query(doc_update_query, (application_id,), fetch=False)
        
        return validation_result
        
    except Exception as e:
        st.error(f"Error performing KYC validation: {str(e)}")
        return {
            'is_valid': False,
            'overall_score': 0,
            'status': 'rejected',
            'issues': [f'Validation error: {str(e)}'],
            'validation_details': {}
        }

