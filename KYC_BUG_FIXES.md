# KYC Bug Fixes and Enhancements

## Summary of All Fixes

### 1. ✅ Fixed KYC Revalidation Status Sync

**Problem:** When admin rejects KYC, then revalidates it, it shows approved in admin page but still shows rejected in user login.

**Root Cause:** Status updates were not properly synchronized between `kyc_applications` and `customers` tables after revalidation.

**Solution:**
- Enhanced `perform_advanced_kyc_validation()` to ensure both tables are updated
- Added double-check to ensure `application_status` matches `kyc_status`
- Added proper status mapping: 'approved' → 'Approved', 'rejected' → 'Rejected'
- Added refresh after revalidation to update UI everywhere

**Code Changes:**
- `ai_kyc_validator.py`: Enhanced status update logic with double-check
- `app_main.py`: Added success message and forced refresh after revalidation

### 2. ✅ Fixed Resubmit KYC Button

**Problem:** When user clicks "Resubmit KYC", it was submitting old documents instead of guiding to upload new ones.

**Solution:**
- Clear all document session state when resubmit is clicked
- Clear: `identity_doc_kyc`, `camera_photo_kyc`, `uploaded_photo_kyc`, `doc_type_kyc`
- Reset KYC status to 'Not Submitted'
- Navigate to KYC Portal with scroll-to-top
- User must upload new documents (old ones are cleared)

**Code Changes:**
- `app_main.py`: Clear session state before navigating to KYC Portal
- Added scroll-to-top JavaScript when navigating

### 3. ✅ Added Scroll-to-Top on KYC Portal

**Problem:** When navigating to KYC Portal, page shows at bottom instead of top.

**Solution:**
- Added JavaScript scroll-to-top when KYC Portal page loads
- Uses both instant and smooth scroll for reliability
- Also added scroll-to-top when clicking "Resubmit KYC" button

**Code Changes:**
- `app_main.py`: Added scroll script at start of KYC Portal view
- Added scroll script in resubmit button handler

### 4. ✅ Implemented Individual Document Rejection

**Problem:** Admin could only reject entire KYC, not individual documents (photo or identity document).

**Solution:**
- Added `admin_reject_document()` function in `db_helpers.py`
- Added individual "Reject" button for each document in admin page
- Rejection updates:
  - Document `verification_status` to 'rejected'
  - KYC `application_status` to 'pending_resubmission'
  - Customer `kyc_status` to 'Pending Resubmission'
- User only needs to resubmit the rejected document

**New Function:**
```python
def admin_reject_document(document_id, application_id, customer_id, admin_user_id, rejection_reason, document_type)
```

**UI Changes:**
- Added third column in document list for rejection button
- Shows document verification status (✅ Verified, ❌ Rejected, ⏳ Pending)
- Rejection requires reason input
- Confirmation dialog before rejection

**Code Changes:**
- `db_helpers.py`: New `admin_reject_document()` function
- `app_main.py`: Added rejection UI in admin customer management page

### 5. ✅ Enhanced AI Document Type Detection

**Problem:** User could select PAN in dropdown but upload Aadhar card and it would be accepted.

**Solution:**
- Enhanced `detect_document_type_from_ocr()` to detect document type from OCR data
- Validates document type match during validation
- If mismatch detected, adds critical issue and rejects
- Checks for PAN format (5 letters, 4 digits, 1 letter)
- Checks for Aadhar format (12 digits in groups of 4)

**Validation Logic:**
- Customer selects document type (PAN/Aadhar/Passport)
- AI detects actual document type from OCR
- If mismatch: Critical issue → Automatic rejection
- Error message: "Document type mismatch: Selected PAN but uploaded AADHAR"

**Code Changes:**
- `ai_kyc_validator.py`: Enhanced document type detection and validation
- Already implemented in `perform_advanced_kyc_validation()`

### 6. ✅ Enhanced Blur and Clarity Detection

**Problem:** Blurred or unclear documents/photos were being accepted.

**Solution:**
- Enhanced `analyze_image_quality()` with advanced blur detection
- Uses Laplacian variance for sharpness measurement
- Uses edge detection for clarity assessment
- Multiple thresholds:
  - Very blurry: Laplacian variance < 100 → -30 points
  - Slightly blurry: Laplacian variance < 200 → -15 points
  - Low detail: Edge density < 0.05 → -20 points
  - Limited detail: Edge density < 0.1 → -10 points

**AI Features:**
- **Sharpness Detection:** Laplacian variance (lower = more blurry)
- **Edge Density:** Percentage of pixels that are edges (lower = less detail)
- **Quality Score:** Combined score with penalties for blur/clarity issues

**Rejection Criteria:**
- If quality score < 60: Document rejected
- Blur issues are flagged in validation notes
- User sees specific blur/clarity issues in rejection message

**Code Changes:**
- `ai_kyc_validator.py`: Enhanced `analyze_image_quality()` with blur detection
- Added edge density calculation
- Added multiple quality thresholds

## User Experience Improvements

### For Users:
1. **Resubmit KYC:** Now properly clears old documents and guides to upload new ones
2. **Scroll to Top:** KYC Portal always shows from top
3. **Individual Document Rejection:** Only need to resubmit rejected document, not all documents
4. **Clear Error Messages:** See specific issues (blur, document type mismatch, etc.)

### For Admins:
1. **Individual Document Control:** Can reject photo OR identity document separately
2. **Status Sync:** Revalidation updates status everywhere (admin page, user login, status check)
3. **Document Status Display:** See verification status for each document (✅/❌/⏳)
4. **Better Validation:** AI detects document type mismatches and blur issues automatically

## Testing Checklist

- [ ] Admin rejects KYC → User sees rejected status
- [ ] Admin revalidates KYC → Status updates everywhere (admin, user login, status check)
- [ ] User clicks "Resubmit KYC" → Old documents cleared, must upload new ones
- [ ] KYC Portal loads → Page shows from top
- [ ] Admin rejects photo only → User only needs to resubmit photo
- [ ] Admin rejects identity document only → User only needs to resubmit identity document
- [ ] User selects PAN but uploads Aadhar → Rejected with mismatch message
- [ ] User uploads blurred photo → Rejected with blur message
- [ ] User uploads unclear document → Rejected with clarity message
- [ ] Document type detection works for PAN, Aadhar, Passport

## Files Modified

1. **`app_main.py`**:
   - Fixed resubmit KYC button (clear session state)
   - Added scroll-to-top on KYC Portal
   - Added individual document rejection UI
   - Enhanced revalidation refresh

2. **`db_helpers.py`**:
   - Added `admin_reject_document()` function

3. **`ai_kyc_validator.py`**:
   - Enhanced status sync (double-check)
   - Enhanced blur/clarity detection
   - Document type detection already implemented

## Database Changes

**New Status Values:**
- `customers.kyc_status`: 'Pending Resubmission' (for partial rejection)
- `kyc_applications.application_status`: 'pending_resubmission' (for partial rejection)
- `documents.verification_status`: 'rejected' (for individual document rejection)

## Notes

- Individual document rejection allows partial resubmission (better UX)
- AI validation now catches document type mismatches automatically
- Blur detection uses industry-standard Laplacian variance method
- All status updates are synchronized across all tables
- User must upload new documents when resubmitting (old ones cleared)


