# Testing Rejection Cases - Quick Guide

## How to Test Document Rejection

### 1. Test Critical Rejection Cases

#### A. File Too Small (Corrupted)
- **Action:** Upload a file smaller than 2KB
- **Expected Result:** Document rejected with note "File too small (possibly corrupted)"
- **How to Create:** Create a tiny text file or use a corrupted image

#### B. Low Resolution Image
- **Action:** Upload an image smaller than 50K pixels (e.g., 200x200 pixels)
- **Expected Result:** Document rejected with note "Image resolution too low (below 50K pixels)"
- **How to Create:** Resize an image to very small dimensions

#### C. Blurry Image
- **Action:** Upload a heavily blurred image
- **Expected Result:** Document rejected with note "Image too blurry (cannot read text/features)"
- **How to Create:** Apply heavy blur filter to an image

#### D. Dark Image
- **Action:** Upload a very dark image (brightness < 30)
- **Expected Result:** Document rejected with note "Image too dark (unreadable)"
- **How to Create:** Darken an image significantly in an image editor

#### E. Photo Without Face
- **Action:** Upload a photo that doesn't contain a face (landscape, object, etc.)
- **Expected Result:** Document rejected with note "No face detected in photo"
- **How to Create:** Use any image without a person's face

#### F. Invalid Identity Document Format
- **Action:** Upload an identity document with invalid PAN/Aadhar format
- **Expected Result:** Document rejected with note about invalid format
- **How to Create:** Use a document with wrong number of digits

### 2. Test Warning Cases (Score Penalties)

#### A. Low Quality Image
- **Action:** Upload an image with low contrast or moderate blur
- **Expected Result:** Document may be approved but with lower score, or rejected if score < 60%
- **How to Create:** Slightly blur or reduce contrast of an image

#### B. Overexposed Image
- **Action:** Upload a very bright/overexposed image
- **Expected Result:** Score penalty, may be rejected if overall score < 60%
- **How to Create:** Increase brightness significantly

#### C. Low OCR Confidence
- **Action:** Upload a document with poor text quality
- **Expected Result:** Score penalty, rejected if OCR confidence < 50%
- **How to Create:** Use a document with faded text or poor scan quality

### 3. Test Approval Cases

#### A. High Quality Photo
- **Action:** Upload a clear, well-lit photo with a visible face
- **Expected Result:** Document approved with high score
- **Requirements:**
  - Resolution > 100K pixels
  - Clear, not blurry
  - Good brightness (50-220)
  - Face clearly visible and centered

#### B. Valid Identity Document
- **Action:** Upload a clear identity document (PAN/Aadhar)
- **Expected Result:** Document approved
- **Requirements:**
  - Clear, readable text
  - Valid format (PAN = 10 chars, Aadhar = 12 digits)
  - OCR confidence > 70%
  - All required fields present

## Validation Score Breakdown

### Document Validation Scoring:
- **Starting Score:** 100 points
- **Approval Threshold:** 60 points (60%)
- **Critical Issues:** -40 to -50 points each
- **Warning Issues:** -5 to -25 points each

### Score Calculation Example:

**Good Document:**
- Starting: 100
- No issues: 0
- **Final Score: 100** ✅ Approved

**Poor Document:**
- Starting: 100
- Low resolution: -20
- Blurry: -15
- Low OCR confidence: -20
- **Final Score: 45** ❌ Rejected

**Critical Issue Document:**
- Starting: 100
- No face detected: -50 (critical)
- **Final Score: 50** ❌ Rejected (critical issue)

## How to Verify Document Status

### In Database (DBeaver):
```sql
SELECT 
    document_id,
    document_type,
    document_name,
    verification_status,
    verified_at,
    verification_notes
FROM documents
WHERE application_id = '<application_id>'
ORDER BY created_at;
```

### In Admin Panel:
1. Go to Admin → Customer Management
2. Find the customer
3. Click on customer name to view details
4. Check "Document Verification Status" section
5. Each document should show:
   - ✅ Verified (green) - if approved
   - ❌ Rejected (red) - if rejected
   - ⏳ Pending - should NOT appear after validation

## Common Issues and Solutions

### Issue: Document still shows "Pending"
**Solution:**
1. Re-validate the KYC from Admin panel
2. Check that `verified_at` column exists in database
3. Verify the validation ran successfully (check logs)

### Issue: All documents approved even with poor quality
**Solution:**
1. Check validation thresholds (should be 60% for documents)
2. Verify that validation is actually running
3. Check `verification_notes` to see what validation found

### Issue: Documents rejected even with good quality
**Solution:**
1. Check `verification_notes` for specific issues
2. Verify file format is supported
3. Check that image is not corrupted
4. Ensure OCR data is available for identity documents

## Testing Checklist

- [ ] Upload very small file (< 2KB) - should reject
- [ ] Upload low resolution image (< 50K pixels) - should reject
- [ ] Upload blurry image - should reject
- [ ] Upload dark image - should reject
- [ ] Upload photo without face - should reject
- [ ] Upload valid high-quality photo - should approve
- [ ] Upload valid identity document - should approve
- [ ] Upload invalid format document - should reject
- [ ] Check document status in database after validation
- [ ] Verify `verified_at` timestamp is set
- [ ] Verify `verification_notes` explains the decision
- [ ] Test re-validation from admin panel

## Expected Behavior After Fix

1. **After KYC Submission:**
   - Documents are automatically validated
   - Each document gets individual status (verified/rejected)
   - Status is NOT "pending" after validation

2. **After Re-validation:**
   - All documents are re-validated
   - Statuses are updated based on current validation
   - Timestamps are updated

3. **Document Status Display:**
   - Shows ✅ Verified for approved documents
   - Shows ❌ Rejected for rejected documents
   - Shows ⏳ Pending ONLY if validation hasn't run yet


