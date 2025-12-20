# Fixes Applied - December 2024

## ✅ Issue 1: Check Application Status - Missing `kyc_status` Column

### Problem
The "Check Application Status" page was failing with error:
```
column c.kyc_status does not exist
```

### Solution Applied
1. **Created Migration Script**: `migrate_add_kyc_status.sql` - SQL script to add the missing column
2. **Updated Queries**: Modified both `app_main.py` and `db_helpers.py` to handle missing column gracefully
3. **Created Migration Guide**: `MIGRATION_INSTRUCTIONS.md` with step-by-step instructions

### What You Need to Do
**Run the migration SQL in DBeaver:**

1. Open DBeaver → Connect to your PostgreSQL database
2. Open SQL Editor (Right-click database → SQL Editor → New SQL Script)
3. Copy and paste the contents of `migrate_add_kyc_status.sql`
4. Execute the script (F5 or Execute button)

**OR run this SQL directly:**

```sql
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'kyc_status'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN kyc_status VARCHAR(50) DEFAULT 'Not Submitted' 
        CHECK (kyc_status IN ('Not Submitted', 'In Progress', 'Submitted', 'Under Review', 'Approved', 'Rejected'));
    END IF;
END $$;

UPDATE customers 
SET kyc_status = 'Not Submitted' 
WHERE kyc_status IS NULL;
```

### Temporary Workaround
The application will now work even without the column (with a warning), but **you should run the migration** for full functionality.

---

## ✅ Issue 2: Webcam Functionality - Dynamic Control

### Problem
Webcam was always initializing, even when "Upload Photo" was selected, causing poor user experience.

### Solution Applied
1. **Changed Radio Options**: Updated from `["Upload Photo", "Use Webcam"]` to `["Upload from Local", "Use Web Cam"]`
2. **Conditional Webcam Initialization**: Webcam (`st.camera_input`) now only initializes when "Use Web Cam" is selected
3. **Improved User Experience**: Clear separation between upload and webcam options

### Code Changes
- **File**: `app_main.py`
- **Location**: KYC Portal section (lines ~590-604)
- **Change**: Wrapped `handle_webcam_capture()` in `elif photo_mode == "Use Web Cam":` block

### Result
- ✅ Webcam only activates when user selects "Use Web Cam"
- ✅ No camera permission prompts when using "Upload from Local"
- ✅ Better user experience with clear option separation

---

## Files Modified

1. **app_main.py**
   - Updated webcam initialization logic
   - Added column existence check for status queries
   - Improved error handling

2. **db_helpers.py**
   - Updated `check_application_status()` to handle missing `kyc_status` column
   - Added fallback queries when column doesn't exist

3. **New Files Created**
   - `migrate_add_kyc_status.sql` - SQL migration script
   - `migrate_add_kyc_status.py` - Python migration script (optional)
   - `MIGRATION_INSTRUCTIONS.md` - Step-by-step migration guide
   - `FIXES_APPLIED.md` - This file

---

## Testing Checklist

After running the migration:

- [ ] Check Application Status page works with Email search
- [ ] Check Application Status page works with Phone search
- [ ] Check Application Status page works with Application ID search
- [ ] KYC Portal - "Upload from Local" works without camera prompt
- [ ] KYC Portal - "Use Web Cam" activates camera correctly
- [ ] All 5 status states display correctly (A, B, C, D, E)

---

## Next Steps

1. **Run the migration SQL** in DBeaver (see MIGRATION_INSTRUCTIONS.md)
2. **Test the application** using the checklist above
3. **Verify** that status checking works for all search types

---

**Status**: ✅ Both issues fixed. Migration required for full functionality.

