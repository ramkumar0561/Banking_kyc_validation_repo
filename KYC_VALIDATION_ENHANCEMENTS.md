# KYC Validation Enhancements - Document Status Fix & AI Improvements

## Problem Identified
1. **Document verification status showing "Pending"** even when KYC is approved
   - Root cause: Column name mismatch (`verification_date` vs `verified_at`)
   - Root cause: Documents were not being individually validated and updated

2. **Lack of realistic rejection cases**
   - System was too lenient, approving everything
   - No proper AI-based validation with rejection scenarios

## Changes Made

### 1. Fixed Column Name Issue
**File:** `ai_kyc_validator.py`
- Changed `verification_date` to `verified_at` (correct column name from database schema)
- Updated all document update queries to use the correct column

### 2. Enhanced Document Validation (`validate_document_advanced`)

#### New Validation Checks:

**A. File Validation:**
- File size checks (too small = corrupted, too large = rejected)
- File existence and accessibility

**B. Image Quality Validation (for image documents):**
- **Resolution Check:** Rejects if < 50K pixels (critical), warns if < 100K pixels
- **Blur Detection:** Uses Laplacian variance to detect blur
  - Critical rejection if blur score < 50 (unreadable)
  - Warning if blur score < 100
- **Brightness Check:** 
  - Critical rejection if < 30 (too dark)
  - Warning if < 50 or > 220 (overexposed)
- **Contrast Check:** Warns if contrast < 15

**C. Photo-Specific Validation:**
- **Face Detection:** 
  - Critical rejection if no face detected
  - Checks face confidence (rejects if < 60%)
  - Checks face size/position (too small or too large = issues)
- **Liveness Detection:**
  - Detects printed photos or screen captures
  - Penalizes if liveness check fails

**D. OCR Validation:**
- Checks OCR confidence levels
  - Critical rejection if < 50%
  - Warning if < 70%
- Validates document completeness
- Checks for missing critical fields (Aadhar number, PAN number, Name)
- Document-specific format validation (PAN = 10 chars, Aadhar = 12 digits)

**E. Document-Specific Validation:**
- **Identity Proof:** Validates PAN/Aadhar format
- **Photo:** Face detection and liveness checks

### 3. Individual Document Status Updates

**File:** `ai_kyc_validator.py` - `perform_advanced_kyc_validation` function

**Before:** All documents were updated together based on overall KYC status
**After:** Each document is validated individually and gets its own status

**New Logic:**
- Each document is validated separately using `validate_document_advanced`
- Document status is determined by its own validation score:
  - `verified` if score >= 60% AND no critical issues
  - `rejected` if score < 60% OR has critical issues
- Each document gets its own `verification_notes` explaining why it was approved/rejected

### 4. Realistic Rejection Scenarios

The system now rejects documents for:

1. **Critical Issues (Automatic Rejection):**
   - File too small (< 2KB) - possibly corrupted
   - Image resolution too low (< 50K pixels)
   - Image too blurry (Laplacian variance < 50)
   - Image too dark (brightness < 30)
   - No face detected in photo
   - OCR validation failed
   - Very low OCR confidence (< 50%)
   - Missing critical identity numbers (Aadhar/PAN)

2. **Warning Issues (Score Penalties):**
   - Low file size (2-5KB)
   - Low resolution (50K-100K pixels)
   - Blurry image (Laplacian variance 50-100)
   - Dark image (brightness 30-50)
   - Overexposed image (brightness > 220)
   - Low contrast
   - Low face detection confidence (60-80%)
   - Face too small or too large
   - Possible printed/screen photo
   - Low OCR confidence (50-70%)
   - Missing non-critical fields
   - Invalid document format

### 5. Validation Thresholds

**Document Approval Threshold:** 60% (realistic for production)
- Documents scoring < 60% are rejected
- Documents with critical issues are automatically rejected regardless of score

**Overall KYC Approval Threshold:** 50% (kept lower for test data)
- Can be adjusted in `perform_advanced_kyc_validation` function
- Line 737: `if overall_score >= 50:`

## Code Changes Summary

### Modified Files:
1. **`ai_kyc_validator.py`**
   - Enhanced `validate_document_advanced()` function (lines 414-650)
   - Updated `perform_advanced_kyc_validation()` function (lines 850-950)
   - Fixed column name: `verification_date` → `verified_at`

### Key Functions Modified:

1. **`validate_document_advanced(application_id, document_type)`**
   - Added comprehensive file validation
   - Added image quality checks (blur, brightness, contrast, resolution)
   - Added photo-specific validation (face detection, liveness)
   - Added OCR validation with confidence checks
   - Added document-specific format validation
   - Returns detailed validation results with critical issues flagged

2. **`perform_advanced_kyc_validation(application_id, customer_id)`**
   - Now updates each document individually
   - Each document gets its own verification status based on its validation
   - Fixed column name in UPDATE queries
   - Better error handling and ASCII-safe notes

## Testing Recommendations

1. **Test Rejection Cases:**
   - Upload a very small file (< 2KB) - should be rejected
   - Upload a blurry image - should be rejected or penalized
   - Upload a dark image - should be rejected
   - Upload a photo without a face - should be rejected
   - Upload an identity document with invalid format - should be rejected

2. **Test Approval Cases:**
   - Upload high-quality documents - should be approved
   - Upload clear photos with faces - should be approved
   - Upload valid identity documents - should be approved

3. **Verify Document Status:**
   - After validation, check `documents` table
   - `verification_status` should be 'verified' or 'rejected' (not 'pending')
   - `verified_at` should be populated
   - `verification_notes` should explain the decision

## Database Schema Reference

**Documents Table:**
- `verification_status`: VARCHAR(50) - 'pending', 'verified', 'rejected', 'needs_review'
- `verified_at`: TIMESTAMP - When document was verified
- `verification_notes`: TEXT - Explanation of verification decision

## Migration Notes

**No database migration required** - only code changes.

The column `verified_at` already exists in the database schema. The fix was just using the correct column name in the code.

## Future Enhancements

1. **Adjustable Thresholds:**
   - Make validation thresholds configurable via environment variables
   - Allow different thresholds for different document types

2. **Advanced OCR:**
   - Integrate with real OCR APIs (Google Vision, AWS Textract)
   - Better text extraction and validation

3. **Machine Learning:**
   - Train models for document authenticity detection
   - Fraud detection based on patterns

4. **Real-time Validation:**
   - Validate documents as they're uploaded
   - Show immediate feedback to users

## Files to Update on Other Systems

1. **`ai_kyc_validator.py`** - Complete file replacement
   - Enhanced `validate_document_advanced()` function
   - Updated `perform_advanced_kyc_validation()` function

## Verification Steps

After updating the code:

1. **Check Document Status:**
   ```sql
   SELECT document_id, document_type, verification_status, verified_at, verification_notes
   FROM documents
   WHERE application_id = '<your_application_id>'
   ORDER BY created_at;
   ```

2. **Re-validate Existing Applications:**
   - Go to Admin → Customer Management
   - Click "🔄 Re-validate KYC" for a customer
   - Check that document statuses are updated

3. **Test New Submissions:**
   - Submit a new KYC application
   - Check that documents are validated and status is set correctly

## Notes

- The validation is now more strict and realistic
- Documents are individually validated, not just based on overall KYC status
- Rejection cases are properly implemented
- All validation notes are ASCII-safe for database storage
- Column names are corrected to match database schema


