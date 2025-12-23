"""
OCR Engine for Document Verification
Extracts text from uploaded documents and validates completeness
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from PIL import Image
import streamlit as st

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import pdf2image
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class OCREngine:
    """OCR Engine for extracting and validating document information"""
    
    def __init__(self):
        self.tesseract_available = TESSERACT_AVAILABLE
        if TESSERACT_AVAILABLE:
            if os.name == 'nt':
                possible_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from an image file"""
        try:
            if not self.tesseract_available:
                return self._mock_ocr_extraction(image_path)
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            return self._mock_ocr_extraction(image_path)
    
    def extract_text(self, file_path: str, mime_type: str) -> str:
        """Extract text from file based on MIME type"""
        if mime_type.startswith('image/'):
            return self.extract_text_from_image(file_path)
        elif mime_type == 'application/pdf' and PDF_SUPPORT:
            images = pdf2image.convert_from_path(file_path)
            all_text = []
            for image in images:
                if self.tesseract_available:
                    text = pytesseract.image_to_string(image, lang='eng')
                else:
                    text = self._mock_ocr_extraction(file_path)
                all_text.append(text)
            return "\n".join(all_text).strip()
        else:
            return ""
    
    def validate_pan(self, extracted_text: str) -> Dict[str, any]:
        """Validate PAN card document"""
        results = {
            'is_valid': False,
            'pan_number': None,
            'name': None,
            'father_name': None,
            'dob': None,
            'completeness_score': 0,
            'missing_fields': [],
            'confidence': 0
        }
        
        # PAN format: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)
        # Pattern allows for spaces or hyphens: ABCDE 1234 F or ABCDE-1234-F
        pan_pattern = r'\b([A-Z]{5})[\s\-]?(\d{4})[\s\-]?([A-Z]{1})\b'
        pan_match = re.search(pan_pattern, extracted_text.upper())
        if pan_match:
            # Combine parts: ABCDE1234F
            pan_number = pan_match.group(1) + pan_match.group(2) + pan_match.group(3)
            results['pan_number'] = pan_number
            results['completeness_score'] += 35
        
        # Extract name (usually appears after "INCOME TAX DEPARTMENT" or "Name")
        name_patterns = [
            r'(?:Name|NAME)[\s:]+([A-Z][A-Z\s]{5,40})',
            r'(?:Name|NAME)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'INCOME TAX DEPARTMENT\s+([A-Z][A-Z\s]{5,40})',
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, extracted_text)
            if name_match:
                results['name'] = name_match.group(1).strip()
                results['completeness_score'] += 25
                break
        
        # Extract Father's Name (optional)
        father_patterns = [
            r'(?:Father|FATHER|FATHER\'S NAME)[\s:]+([A-Z][A-Z\s]{5,40})',
            r'(?:Father|FATHER|FATHER\'S NAME)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        for pattern in father_patterns:
            father_match = re.search(pattern, extracted_text)
            if father_match:
                results['father_name'] = father_match.group(1).strip()
                results['completeness_score'] += 10
                break
        
        # Extract Date of Birth (optional)
        dob_patterns = [
            r'(?:Date of Birth|DOB|Birth Date)[\s:]+(\d{2}[\s\-\/]\d{2}[\s\-\/]\d{4})',
            r'(\d{2}[\s\-\/]\d{2}[\s\-\/]\d{4})',
        ]
        for pattern in dob_patterns:
            dob_match = re.search(pattern, extracted_text)
            if dob_match:
                results['dob'] = dob_match.group(1).strip()
                results['completeness_score'] += 10
                break
        
        if results['completeness_score'] >= 60:  # PAN number + Name is minimum
            results['is_valid'] = True
            results['confidence'] = min(100, results['completeness_score'])
        else:
            if not results['pan_number']:
                results['missing_fields'].append('PAN Number')
            if not results['name']:
                results['missing_fields'].append('Name')
        
        return results
    
    def validate_aadhar(self, extracted_text: str) -> Dict[str, any]:
        """Validate Aadhar card document"""
        results = {
            'is_valid': False,
            'aadhar_number': None,
            'name': None,
            'dob': None,
            'address': None,
            'completeness_score': 0,
            'missing_fields': [],
            'confidence': 0
        }
        
        # Aadhar format: 12 digits, can be space-separated (e.g., 1234 5678 9012)
        aadhar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
        aadhar_match = re.search(aadhar_pattern, extracted_text)
        if aadhar_match:
            results['aadhar_number'] = re.sub(r'\s', '', aadhar_match.group())
            results['completeness_score'] += 30
        
        name_patterns = [
            r'(?:Name|नाम)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][A-Z\s]{10,30})',
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, extracted_text, re.IGNORECASE)
            if name_match:
                results['name'] = name_match.group(1).strip()
                results['completeness_score'] += 25
                break
        
        if results['completeness_score'] >= 70:
            results['is_valid'] = True
            results['confidence'] = min(100, results['completeness_score'])
        else:
            if not results['aadhar_number']:
                results['missing_fields'].append('Aadhar Number')
            if not results['name']:
                results['missing_fields'].append('Name')
        
        return results
    
    def validate_document(self, file_path: str, mime_type: str, document_type: str) -> Dict[str, any]:
        """Validate a document based on its type"""
        extracted_text = self.extract_text(file_path, mime_type)
        
        validation_result = {
            'extracted_text': extracted_text[:500],
            'document_type': document_type,
            'validation': {}
        }
        
        if document_type == 'identity_proof':
            text_upper = extracted_text.upper()
            # Detect document type and validate accordingly
            if 'AADHAAR' in text_upper or 'AADHAR' in text_upper:
                # Aadhar card detected
                validation_result['validation'] = self.validate_aadhar(extracted_text)
            elif 'INCOME TAX' in text_upper or 'PAN' in text_upper or re.search(r'\b[A-Z]{5}\d{4}[A-Z]{1}\b', text_upper):
                # PAN card detected (by keywords or PAN format pattern)
                validation_result['validation'] = self.validate_pan(extracted_text)
            else:
                # Generic identity document - try to detect PAN or Aadhar by format
                # Check for PAN format first (more specific)
                if re.search(r'\b[A-Z]{5}[\s\-]?\d{4}[\s\-]?[A-Z]{1}\b', text_upper):
                    validation_result['validation'] = self.validate_pan(extracted_text)
                # Check for Aadhar format
                elif re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', extracted_text):
                    validation_result['validation'] = self.validate_aadhar(extracted_text)
                else:
                    # Generic validation - just check if text is readable
                    validation_result['validation'] = {
                        'is_valid': len(extracted_text) > 50,
                        'completeness_score': min(100, len(extracted_text) // 2),
                        'confidence': min(100, len(extracted_text) // 2),
                        'missing_fields': []
                    }
        else:
            validation_result['validation'] = {
                'is_valid': len(extracted_text) > 30,
                'completeness_score': min(100, len(extracted_text)),
                'confidence': min(100, len(extracted_text)),
                'missing_fields': []
            }
        
        return validation_result
    
    def _mock_ocr_extraction(self, file_path: str) -> str:
        """Mock OCR extraction when tesseract is not available"""
        # Try to detect document type from filename
        file_lower = file_path.lower()
        if 'pan' in file_lower:
            # Mock PAN card text
            return """
            INCOME TAX DEPARTMENT
            GOVT. OF INDIA
            
            Name: JOHN DOE
            Father's Name: JAMES DOE
            Date of Birth: 01/01/1990
            PAN: ABCDE1234F
            """
        else:
            # Mock Aadhar card text
            return """
            GOVERNMENT OF INDIA
            AADHAAR
            
            Name: JOHN DOE
            Date of Birth: 01/01/1990
            Address: 123 Main Street, City, State - 123456
            Aadhaar No: 1234 5678 9012
            """

# Global OCR Engine instance
ocr_engine = OCREngine()

