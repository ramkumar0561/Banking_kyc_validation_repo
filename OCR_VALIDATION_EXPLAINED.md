# OCR & Document Validation Explained

## How It Works

### Overview
The system uses **OCR (Optical Character Recognition)** to extract text from uploaded documents, then validates the extracted information using **pattern matching** and **format validation**.

## Technology Stack

### 1. OCR Engine
- **Primary Tool:** Tesseract OCR (open-source OCR engine)
- **Python Library:** `pytesseract`
- **Fallback:** Mock OCR when Tesseract is not installed (for testing)

### 2. Validation Method
- **Pattern Matching:** Uses **Regular Expressions (Regex)** to find and validate document numbers
- **Format Validation:** Checks if extracted numbers match expected formats
- **Field Extraction:** Extracts name, date of birth, address, etc.

## How PAN Number Detection Works

### Step 1: OCR Text Extraction
When you upload a PAN card image:
1. **Tesseract OCR** reads the image and extracts all text
2. Example extracted text:
   ```
   INCOME TAX DEPARTMENT
   GOVT. OF INDIA
   
   Name: JOHN DOE
   Father's Name: JAMES DOE
   Date of Birth: 01/01/1990
   PAN: ABCDE1234F
   ```

### Step 2: PAN Format Detection
The system uses **Regex Pattern** to find PAN numbers:

**PAN Format:** `ABCDE1234F` (5 letters + 4 digits + 1 letter)

**Regex Pattern:**
```python
r'\b([A-Z]{5})[\s\-]?(\d{4})[\s\-]?([A-Z]{1})\b'
```

**What it matches:**
- `ABCDE1234F` ✅
- `ABCDE 1234 F` ✅ (with spaces)
- `ABCDE-1234-F` ✅ (with hyphens)
- `ABCDE1234F` ✅ (no spaces)

**What it rejects:**
- `ABCD1234F` ❌ (only 4 letters, should be 5)
- `ABCDE123F` ❌ (only 3 digits, should be 4)
- `ABCDE12345F` ❌ (5 digits, should be 4)

### Step 3: Validation Logic
```python
def validate_pan(extracted_text):
    # 1. Find PAN number using regex
    pan_match = re.search(pan_pattern, extracted_text)
    
    # 2. Extract PAN number
    pan_number = pan_match.group(1) + pan_match.group(2) + pan_match.group(3)
    # Result: "ABCDE1234F"
    
    # 3. Validate format
    if len(pan_number) == 10:  # Must be exactly 10 characters
        # Valid PAN format
    else:
        # Invalid format
```

### Step 4: Field Extraction
The system also extracts:
- **Name:** Looks for "Name:" or "NAME:" followed by text
- **Father's Name:** Looks for "Father" or "Father's Name"
- **Date of Birth:** Looks for "DOB" or "Date of Birth" followed by date

### Step 5: Score Calculation
- PAN Number found: +35 points
- Name found: +25 points
- Father's Name found: +10 points
- Date of Birth found: +10 points
- **Minimum for approval:** 60 points (PAN + Name)

## How Aadhar Number Detection Works

### Step 1: OCR Text Extraction
Example extracted text:
```
GOVERNMENT OF INDIA
AADHAAR

Name: JOHN DOE
Date of Birth: 01/01/1990
Address: 123 Main Street, City, State - 123456
Aadhaar No: 1234 5678 9012
```

### Step 2: Aadhar Format Detection
**Aadhar Format:** 12 digits (can be space-separated)

**Regex Pattern:**
```python
r'\b\d{4}\s?\d{4}\s?\d{4}\b'
```

**What it matches:**
- `123456789012` ✅
- `1234 5678 9012` ✅ (with spaces)
- `1234-5678-9012` ✅ (with hyphens)

**What it rejects:**
- `12345678901` ❌ (only 11 digits)
- `1234567890123` ❌ (13 digits)
- `ABCD56789012` ❌ (contains letters)

### Step 3: Validation Logic
```python
def validate_aadhar(extracted_text):
    # 1. Find Aadhar number using regex
    aadhar_match = re.search(aadhar_pattern, extracted_text)
    
    # 2. Remove spaces
    aadhar_number = re.sub(r'\s', '', aadhar_match.group())
    # Result: "123456789012"
    
    # 3. Validate format
    if len(aadhar_number) == 12:  # Must be exactly 12 digits
        # Valid Aadhar format
    else:
        # Invalid format
```

## Document Type Detection

The system automatically detects document type in this order:

1. **By Keywords:**
   - If text contains "AADHAAR" or "AADHAR" → Aadhar card
   - If text contains "INCOME TAX" or "PAN" → PAN card

2. **By Format Pattern:**
   - If text matches PAN format (`ABCDE1234F`) → PAN card
   - If text matches Aadhar format (`1234 5678 9012`) → Aadhar card

3. **By Filename:**
   - If filename contains "pan" → Try PAN validation
   - If filename contains "aadhar" → Try Aadhar validation

## Validation Flow Diagram

```
Upload Document
      ↓
OCR Text Extraction (Tesseract)
      ↓
Detect Document Type
      ↓
┌─────────────────┬─────────────────┐
│   PAN Card      │  Aadhar Card    │
│                 │                 │
│ 1. Find PAN     │ 1. Find Aadhar  │
│    (5+4+1)      │    (12 digits)  │
│ 2. Extract Name │ 2. Extract Name │
│ 3. Extract DOB  │ 3. Extract DOB  │
│ 4. Calculate    │ 4. Calculate    │
│    Score        │    Score        │
└─────────────────┴─────────────────┘
      ↓
Validation Result
      ↓
Store in Database (ocr_extracted_data)
      ↓
AI Validator Checks Format
      ↓
Approve/Reject Document
```

## Example: PAN Validation in Action

### Input Image:
```
┌─────────────────────────┐
│ INCOME TAX DEPARTMENT   │
│ GOVT. OF INDIA         │
│                         │
│ Name: RAM KUMAR        │
│ Father: KUMAR SINGH    │
│ DOB: 15/05/1990        │
│ PAN: ABCDE1234F        │
└─────────────────────────┘
```

### OCR Extraction:
```
INCOME TAX DEPARTMENT
GOVT. OF INDIA

Name: RAM KUMAR
Father: KUMAR SINGH
DOB: 15/05/1990
PAN: ABCDE1234F
```

### Validation Process:
1. **Detect Type:** "INCOME TAX" found → PAN card
2. **Extract PAN:** Regex finds `ABCDE1234F`
3. **Validate Format:** Length = 10 ✅
4. **Extract Name:** "RAM KUMAR" ✅
5. **Calculate Score:** 35 (PAN) + 25 (Name) = 60 points ✅
6. **Result:** Valid PAN card

### If PAN Format is Wrong:
```
PAN: ABCD1234F  (only 4 letters)
```
- Regex finds: `ABCD1234F`
- Length check: 9 characters ❌
- **Result:** "PAN number format invalid"

## Example: Aadhar Validation in Action

### Input Image:
```
┌─────────────────────────┐
│ GOVERNMENT OF INDIA     │
│ AADHAAR                 │
│                         │
│ Name: RAM KUMAR        │
│ DOB: 15/05/1990         │
│ Address: 123 Main St   │
│ Aadhaar: 1234 5678 9012 │
└─────────────────────────┘
```

### OCR Extraction:
```
GOVERNMENT OF INDIA
AADHAAR

Name: RAM KUMAR
DOB: 15/05/1990
Address: 123 Main St
Aadhaar: 1234 5678 9012
```

### Validation Process:
1. **Detect Type:** "AADHAAR" found → Aadhar card
2. **Extract Aadhar:** Regex finds `1234 5678 9012`
3. **Remove Spaces:** `123456789012`
4. **Validate Format:** Length = 12 digits ✅
5. **Extract Name:** "RAM KUMAR" ✅
6. **Calculate Score:** 30 (Aadhar) + 25 (Name) = 55 points
7. **Result:** Valid Aadhar card

### If Aadhar Format is Wrong:
```
Aadhaar: 1234 5678 901  (only 11 digits)
```
- Regex finds: `1234 5678 901`
- Length check: 11 digits ❌
- **Result:** "Aadhar number format invalid"

## AI Tools Used

### 1. Tesseract OCR
- **What it does:** Converts image to text
- **How it works:** Uses machine learning models trained on millions of images
- **Accuracy:** ~95% for clear, high-quality images
- **Limitations:** Struggles with blurry, dark, or low-resolution images

### 2. Regular Expressions (Regex)
- **What it does:** Pattern matching to find and validate document numbers
- **How it works:** Defines patterns (like PAN format) and searches text
- **Accuracy:** 100% for format validation (if pattern matches, format is correct)
- **Limitations:** Can't verify if number is real/active (only format)

### 3. OpenCV (for image quality)
- **What it does:** Analyzes image quality (blur, brightness, contrast)
- **How it works:** Computer vision algorithms
- **Used for:** Ensuring OCR can read the document properly

## Limitations & Future Enhancements

### Current Limitations:
1. **Format Validation Only:** Checks if format is correct, not if number is real
2. **OCR Accuracy:** Depends on image quality
3. **No Database Verification:** Doesn't check against government databases

### Future Enhancements:
1. **API Integration:** Connect to government APIs to verify document authenticity
2. **Machine Learning:** Train models to detect fake documents
3. **Advanced OCR:** Use cloud OCR services (Google Vision, AWS Textract) for better accuracy
4. **Real-time Validation:** Validate as user uploads, show immediate feedback

## Testing the Validation

### Test PAN Validation:
1. Upload a PAN card image
2. Check OCR extraction in database: `ocr_extracted_data` column
3. Look for `pan_number` field in validation result
4. Check if format is correct (10 characters: 5 letters + 4 digits + 1 letter)

### Test Aadhar Validation:
1. Upload an Aadhar card image
2. Check OCR extraction in database: `ocr_extracted_data` column
3. Look for `aadhar_number` field in validation result
4. Check if format is correct (12 digits)

### View Validation Results:
```sql
SELECT 
    document_id,
    document_type,
    document_name,
    ocr_extracted_data,
    verification_status,
    verification_notes
FROM documents
WHERE application_id = '<your_application_id>';
```

## Summary

**How PAN/Aadhar Detection Works:**
1. ✅ **OCR extracts text** from image (Tesseract)
2. ✅ **Regex patterns find** document numbers (PAN/Aadhar format)
3. ✅ **Format validation** checks if number matches expected format
4. ✅ **Field extraction** gets name, DOB, etc.
5. ✅ **Score calculation** determines if document is valid
6. ✅ **AI validator** checks format again and approves/rejects

**The system can detect:**
- ✅ PAN format: `ABCDE1234F` (5 letters + 4 digits + 1 letter)
- ✅ Aadhar format: `123456789012` (12 digits)
- ✅ Name, DOB, Address (if present in document)

**The system validates:**
- ✅ Format correctness (length, pattern)
- ✅ Field completeness (PAN/Aadhar + Name minimum)
- ✅ Document quality (for OCR accuracy)


