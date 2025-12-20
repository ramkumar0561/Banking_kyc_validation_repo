# Complete Database Migration Guide

## Issue: Missing Columns in `customers` Table

The application expects several columns in the `customers` table that may not exist in your database:
- `kyc_status`
- `nominee_name`
- `nominee_relation`
- `otp_verified`
- `first_name`
- `last_name`
- `marital_status`
- `salary`
- `annual_income`
- `occupation`
- `photo_path`

## Solution: Run Comprehensive Migration

### Step 1: Open DBeaver

1. Open DBeaver
2. Connect to your PostgreSQL database (`horizon`)
3. Right-click on your database → **SQL Editor** → **New SQL Script**

### Step 2: Run Migration Script

Copy and paste the **entire contents** of `migrate_all_missing_columns.sql` into the SQL Editor, then:

1. Click **Execute** (or press **F5**)
2. Wait for the script to complete
3. Check the output messages - you should see notices for each column

### Step 3: Verify Migration

Run this query to verify all columns were added:

```sql
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'customers' 
AND column_name IN (
    'kyc_status', 
    'nominee_name', 
    'nominee_relation', 
    'otp_verified',
    'first_name',
    'last_name',
    'marital_status',
    'salary',
    'annual_income',
    'occupation',
    'photo_path'
)
ORDER BY column_name;
```

You should see all 11 columns listed.

### Step 4: Test the Application

1. Restart your Streamlit application
2. Try the "Check Application Status" page
3. Test with Email, Phone, and Application ID searches

## Alternative: Quick SQL (Copy-Paste Ready)

If you prefer, you can run this simplified version directly:

```sql
-- Add all missing columns in one go
DO $$ 
BEGIN
    -- kyc_status
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'kyc_status') THEN
        ALTER TABLE customers ADD COLUMN kyc_status VARCHAR(50) DEFAULT 'Not Submitted' 
        CHECK (kyc_status IN ('Not Submitted', 'In Progress', 'Submitted', 'Under Review', 'Approved', 'Rejected'));
    END IF;

    -- nominee_name
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'nominee_name') THEN
        ALTER TABLE customers ADD COLUMN nominee_name VARCHAR(100);
    END IF;

    -- nominee_relation
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'nominee_relation') THEN
        ALTER TABLE customers ADD COLUMN nominee_relation VARCHAR(50);
    END IF;

    -- otp_verified
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'otp_verified') THEN
        ALTER TABLE customers ADD COLUMN otp_verified BOOLEAN DEFAULT FALSE;
    END IF;

    -- first_name
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'first_name') THEN
        ALTER TABLE customers ADD COLUMN first_name VARCHAR(50);
    END IF;

    -- last_name
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'last_name') THEN
        ALTER TABLE customers ADD COLUMN last_name VARCHAR(50);
    END IF;

    -- marital_status
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'marital_status') THEN
        ALTER TABLE customers ADD COLUMN marital_status VARCHAR(20);
    END IF;

    -- salary
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'salary') THEN
        ALTER TABLE customers ADD COLUMN salary DECIMAL(15, 2);
    END IF;

    -- annual_income
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'annual_income') THEN
        ALTER TABLE customers ADD COLUMN annual_income DECIMAL(15, 2);
    END IF;

    -- occupation
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'occupation') THEN
        ALTER TABLE customers ADD COLUMN occupation VARCHAR(100);
    END IF;

    -- photo_path
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'customers' AND column_name = 'photo_path') THEN
        ALTER TABLE customers ADD COLUMN photo_path TEXT;
    END IF;
END $$;

-- Set default values
UPDATE customers SET kyc_status = 'Not Submitted' WHERE kyc_status IS NULL;
UPDATE customers SET otp_verified = FALSE WHERE otp_verified IS NULL;
```

## Troubleshooting

### Error: "column already exists"
- This is normal - the script checks before adding
- The script is safe to run multiple times

### Error: "syntax error"
- Make sure you're running the entire DO block
- Check that you're connected to the correct database

### Still seeing errors after migration?
1. Verify columns exist (use Step 3 query above)
2. Restart Streamlit application
3. Clear browser cache
4. Check application logs for specific error messages

## What This Migration Does

1. **Adds missing columns** - Only adds columns that don't exist
2. **Sets defaults** - Initializes `kyc_status` and `otp_verified` with defaults
3. **Safe to rerun** - Checks existence before adding
4. **No data loss** - Existing data is preserved

---

**After running this migration, the "Check Application Status" feature will work correctly!**

