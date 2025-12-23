# Duplicate Customer & Registration Validation Fixes

## Summary of All Fixes

### 1. ✅ Fixed Duplicate Customers in Admin Page

**Problem:** Customers appearing multiple times (e.g., Sam Altman, Max Smith showing twice)

**Root Cause:** LEFT JOIN with `kyc_applications` table was creating multiple rows when a customer had multiple applications.

**Solution:** 
- Changed query to use `DISTINCT ON (c.customer_id)` 
- Orders by customer_id and latest application first
- Ensures only one row per customer (latest application)

**Code Change:**
```sql
SELECT DISTINCT ON (c.customer_id)
    c.customer_id,
    ...
FROM customers c
LEFT JOIN users u ON c.user_id = u.user_id
LEFT JOIN kyc_applications ka ON c.customer_id = ka.customer_id
ORDER BY c.customer_id, ka.created_at DESC NULLS LAST, c.created_at DESC
```

### 2. ✅ Username Uniqueness Validation

**New Functions in `db_helpers.py`:**
- `check_username_exists(username)` - Checks if username already exists
- `check_email_exists(email)` - Checks if email already exists

**Implementation:**
- Validates username before creating user account
- Shows error: "Username already exists. Please choose a different username."
- Prevents duplicate usernames at database level

### 3. ✅ Phone Number Validation with Country Code

**Changes:**
- Added country code selector dropdown (+91, +1, +44, +61, +971, +86, +65)
- Phone number input restricted to 10 digits (max_chars=10)
- Validates that phone number is exactly 10 digits
- Stores phone as: `{country_code} {10_digit_number}` (e.g., "+91 9876543210")

**Validation:**
- Removes spaces and non-digits
- Checks length is exactly 10
- Shows error if not 10 digits

### 4. ✅ Duplicate Account Prevention

**Checks Performed:**
1. **Username** - Must be unique
2. **Email** - Must be unique
3. **Phone Number** - Must be unique (with country code)
4. **PAN Card** - Must be unique (if provided in KYC)
5. **Aadhar Number** - Must be unique (if provided in KYC)

**New Functions in `db_helpers.py`:**
- `check_phone_exists(phone)` - Checks if phone number exists
- `check_pan_exists(pan)` - Checks if PAN card exists
- `check_aadhar_exists(aadhar)` - Checks if Aadhar number exists

**Error Messages:**
- Username: "Username already exists! Please choose a different username."
- Email: "Email already registered! Please use a different email or login."
- Phone: "Phone number already registered! Please use a different phone number or login."
- PAN: "PAN Card already registered! Please use a different PAN or contact support."
- Aadhar: "Aadhar Number already registered! Please use a different Aadhar or contact support."

### 5. ✅ File Upload Size & Type Restrictions

**Photo Upload:**
- **Max Size:** 5MB
- **Allowed Types:** JPG, PNG, JPEG
- **Validation:** Checks size and type before accepting
- **Error Messages:** Shows file size in MB if too large

**Identity Document Upload:**
- **Max Size:** 10MB
- **Allowed Types:** PDF, JPG, PNG, JPEG
- **Validation:** Checks size and type before accepting
- **Error Messages:** Shows file size in MB if too large

**Implementation:**
- Validates on upload (immediate feedback)
- Validates again before submission (double check)
- Clears invalid files from session state
- Shows clear error messages with file size

### 6. ✅ Password Validation

**Requirements:**
- Minimum 8 characters
- Validates before submission
- Shows error if too short

## Files Modified

### `app_main.py`:
1. **Admin Customer Query** - Changed to `DISTINCT ON` to prevent duplicates
2. **Registration Form** - Added country code selector and phone validation
3. **Registration Validation** - Added duplicate checks for username, email, phone
4. **KYC Portal** - Added duplicate checks for PAN/Aadhar
5. **File Uploads** - Added size and type validation for photos and documents

### `db_helpers.py`:
1. **New Functions:**
   - `check_username_exists()`
   - `check_email_exists()`
   - `check_phone_exists()`
   - `check_pan_exists()`
   - `check_aadhar_exists()`
2. **Updated `create_user()`** - Now checks for duplicates before creating

## Validation Flow

### Registration:
1. User fills form
2. Validates required fields
3. Validates phone (10 digits)
4. Validates password (8+ chars)
5. Checks username uniqueness
6. Checks email uniqueness
7. Checks phone uniqueness
8. Creates account if all pass

### KYC Submission:
1. User uploads documents
2. Validates file size (photo: 5MB, doc: 10MB)
3. Validates file type (photo: JPG/PNG, doc: PDF/JPG/PNG)
4. Checks PAN uniqueness (if provided)
5. Checks Aadhar uniqueness (if provided)
6. Submits if all pass

## Testing Checklist

- [ ] Admin page shows unique customers (no duplicates)
- [ ] Username uniqueness enforced (error if duplicate)
- [ ] Email uniqueness enforced (error if duplicate)
- [ ] Phone number validation (10 digits required)
- [ ] Country code selector works
- [ ] Phone stored with country code
- [ ] PAN duplicate check works
- [ ] Aadhar duplicate check works
- [ ] Photo upload size validation (5MB max)
- [ ] Photo upload type validation (JPG/PNG only)
- [ ] Document upload size validation (10MB max)
- [ ] Document upload type validation (PDF/JPG/PNG only)
- [ ] Password validation (8+ chars)

## Database Considerations

**Unique Constraints Recommended:**
- `users.username` - Should have UNIQUE constraint
- `users.email` - Should have UNIQUE constraint
- `customers.phone_number` - Should have UNIQUE constraint
- `customers.pan_card` - Should have UNIQUE constraint (if not NULL)
- `customers.aadhar_no` - Should have UNIQUE constraint (if not NULL)

**Note:** The application-level checks will catch duplicates even if database constraints are not set, but database constraints provide an additional safety layer.


