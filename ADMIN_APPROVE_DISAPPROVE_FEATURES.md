# Admin Approve/Disapprove & Strict KYC Validation Features

## Summary of Changes

This document outlines all the new features added for admin KYC management and strict validation.

## 1. Admin Approve/Disapprove Feature

### New Functions in `db_helpers.py`:

#### `admin_approve_kyc(application_id, customer_id, admin_user_id, admin_notes)`
- Manually approves a KYC application
- Updates `kyc_applications` status to 'approved'
- Updates `customers.kyc_status` to 'Approved'
- Marks all documents as 'verified'
- Logs audit trail

#### `admin_reject_kyc(application_id, customer_id, admin_user_id, rejection_reason)`
- Manually rejects a KYC application
- Updates `kyc_applications` status to 'rejected'
- Updates `customers.kyc_status` to 'Rejected'
- Marks all documents as 'rejected'
- Stores rejection reason
- Logs audit trail

### Admin UI Changes (`app_main.py`):

**Location:** Admin → Customer Management → Customer Details

**New Buttons:**
1. **✅ Approve KYC** - Approves the customer's KYC application
2. **❌ Reject KYC** - Rejects with a required rejection reason text input
3. **🔄 Re-validate KYC** - Re-runs AI validation (existing, moved to new section)

**Features:**
- Buttons are in a dedicated "Admin Actions" section
- Rejection requires a reason (mandatory)
- Success/error messages displayed
- Automatic page refresh after action

## 2. Enhanced Document Upload Display

### Changes in Admin Customer Management:

**Before:** Only showed upload time
**After:** Shows upload time + document name

**Example:**
- **Document Upload Time:** `2025-12-21 10:30:45 (pan_card_123.png)`
- **Photo Upload Time:** `2025-12-21 10:31:20 (photo_webcam.jpg)`

**New Section:** "📄 Uploaded Documents"
- Lists all uploaded documents with:
  - Document type (Identity Proof, Photo, etc.)
  - Document name
  - Upload timestamp

## 3. Customer Rejection Message Display

### Dashboard View (`app_main.py`):

**When KYC is Rejected:**
- Shows large error message with rejection reason
- Displays next steps for customer
- "Resubmit KYC Documents" button
- Automatically resets KYC status to allow resubmission

**Message Includes:**
- Rejection reason (from admin or validation)
- Clear next steps
- Instructions to ensure documents match

### Status Check View (`app_main.py`):

**When Status is Rejected:**
- Shows rejection message in status check results
- Displays rejection reason
- Provides guidance for resubmission

### Helper Function (`_display_application_details`):

**Enhanced to show:**
- Rejection reason if status is rejected
- Next steps for customer
- Clear call-to-action

## 4. Strict KYC Validation

### Face Matching (`ai_kyc_validator.py`):

**New Function:** `compare_faces(image1_path, image2_path)`

**How it works:**
1. Detects faces in both images (photo and ID document)
2. Extracts face regions
3. Resizes faces to same size (100x100)
4. Uses template matching for similarity
5. Calculates histogram correlation
6. Combined similarity score (70% template + 30% histogram)
7. **Threshold:** 60% similarity required for match

**Rejection Criteria:**
- No face in photo → Critical rejection
- No face in ID document → Critical rejection
- Similarity < 60% → Critical rejection (-50 points)

### Document Type Detection (`ai_kyc_validator.py`):

**New Function:** `detect_document_type_from_ocr(ocr_data, extracted_text)`

**How it works:**
1. Checks OCR data for PAN/Aadhar numbers
2. Checks text for keywords ("INCOME TAX", "AADHAAR", "PAN")
3. Validates format patterns:
   - PAN: `ABCDE1234F` (5 letters + 4 digits + 1 letter)
   - Aadhar: `123456789012` (12 digits)
4. Returns: 'pan', 'aadhar', or 'unknown'

**Validation Logic:**
- Compares customer's selected document type (from registration) with detected type
- **Critical Rejection** if mismatch:
  - Selected PAN but uploaded Aadhar → Rejected
  - Selected Aadhar but uploaded PAN → Rejected
  - Score set to 0
  - Document marked as invalid

### Stricter Format Validation:

**PAN Validation:**
- Must be exactly 10 characters
- Format: 5 letters + 4 digits + 1 letter
- Rejects if format doesn't match

**Aadhar Validation:**
- Must be exactly 12 digits
- Can have spaces/hyphens (removed for validation)
- Rejects if not 12 digits

### Enhanced Validation Thresholds:

**Before:**
- Overall score >= 50% → Approved
- Document score >= 60% → Verified

**After:**
- Overall score >= 70% → Approved (stricter)
- Document score >= 60% → Verified
- **Critical issues cause automatic rejection:**
  - Face doesn't match → Rejected
  - Document type mismatch → Rejected
  - Critical validation issues → Rejected

## 5. Validation Flow

### New Strict Validation Process:

```
1. Photo Validation
   ├─ Face Detection
   ├─ Liveness Check
   └─ Quality Analysis

2. Identity Document Validation
   ├─ OCR Extraction
   ├─ Format Validation (PAN/Aadhar)
   ├─ Document Type Detection
   └─ Field Completeness

3. Face Matching (NEW)
   ├─ Extract face from photo
   ├─ Extract face from ID document
   ├─ Compare faces
   └─ Reject if similarity < 60%

4. Document Type Validation (NEW)
   ├─ Detect document type from OCR
   ├─ Compare with customer selection
   └─ Reject if mismatch

5. Overall Score Calculation
   ├─ Photo: 40% weight
   ├─ Address: 15% weight
   ├─ Identity Doc: 30% weight
   └─ Photo Doc: 15% weight

6. Final Decision
   ├─ Critical issues? → Rejected
   ├─ Score >= 70%? → Approved
   └─ Otherwise → Rejected
```

## 6. Database Updates

### When Admin Approves:
- `kyc_applications.application_status` → 'approved'
- `kyc_applications.verification_date` → Current timestamp
- `kyc_applications.verified_by` → Admin user ID
- `customers.kyc_status` → 'Approved'
- `documents.verification_status` → 'verified' (all documents)

### When Admin Rejects:
- `kyc_applications.application_status` → 'rejected'
- `kyc_applications.verification_date` → Current timestamp
- `kyc_applications.verified_by` → Admin user ID
- `kyc_applications.rejection_reason` → Admin's reason
- `customers.kyc_status` → 'Rejected'
- `documents.verification_status` → 'rejected' (all documents)
- `documents.verification_notes` → Rejection reason

## 7. Files Modified

### `db_helpers.py`:
- Added `admin_approve_kyc()` function
- Added `admin_reject_kyc()` function

### `ai_kyc_validator.py`:
- Added `compare_faces()` function
- Added `detect_document_type_from_ocr()` function
- Enhanced `perform_advanced_kyc_validation()` with:
  - Face matching validation
  - Document type detection and validation
  - Stricter approval thresholds

### `app_main.py`:
- Added approve/disapprove buttons in admin customer management
- Enhanced document upload time display
- Added rejection message display in Dashboard
- Added rejection message display in Status Check
- Enhanced `_display_application_details()` to show rejection reasons

## 8. Testing Checklist

### Admin Features:
- [ ] Admin can approve KYC from customer management page
- [ ] Admin can reject KYC with reason
- [ ] Rejection reason is stored in database
- [ ] Documents show correct upload times with names
- [ ] All documents listed in "Uploaded Documents" section

### Customer Features:
- [ ] Rejection message shows on Dashboard when logged in
- [ ] Rejection message shows on Status Check page
- [ ] Rejection reason is displayed clearly
- [ ] "Resubmit KYC" button works and resets status
- [ ] Customer can resubmit after rejection

### Validation Features:
- [ ] Face matching works (rejects if faces don't match)
- [ ] Document type detection works (PAN vs Aadhar)
- [ ] Document type mismatch causes rejection
- [ ] PAN format validation (10 chars: 5+4+1)
- [ ] Aadhar format validation (12 digits)
- [ ] Stricter approval threshold (70% instead of 50%)

## 9. Usage Examples

### Admin Approving KYC:
1. Go to Admin → Customer Management
2. Find customer
3. Click customer name to expand details
4. Scroll to "Admin Actions" section
5. Click "✅ Approve KYC"
6. Success message appears
7. Customer status updates to "Approved"

### Admin Rejecting KYC:
1. Go to Admin → Customer Management
2. Find customer
3. Click customer name to expand details
4. Scroll to "Admin Actions" section
5. Enter rejection reason in text box
6. Click "❌ Reject KYC"
7. Success message appears
8. Customer sees rejection message on login

### Customer Viewing Rejection:
1. Customer logs in
2. Sees rejection message on Dashboard
3. Reads rejection reason
4. Clicks "Resubmit KYC Documents"
5. Status resets to "Not Submitted"
6. Can upload new documents

## 10. Notes

- All rejection reasons are stored in ASCII-safe format
- Face matching uses OpenCV template matching (60% threshold)
- Document type detection uses OCR data and text patterns
- Admin actions are logged in audit trail
- Customer can resubmit after rejection (status resets)
- Stricter validation ensures higher quality KYC approvals


