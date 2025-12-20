# Database Migration Instructions

## Issue: Missing `kyc_status` Column

The `customers` table is missing the `kyc_status` column, which is required for the application status check functionality.

## Solution: Run Migration SQL

### Option 1: Using DBeaver (Recommended)

1. Open DBeaver and connect to your PostgreSQL database
2. Open a new SQL Editor (Right-click on your database → SQL Editor → New SQL Script)
3. Copy and paste the contents of `migrate_add_kyc_status.sql`
4. Execute the script (Press F5 or click the Execute button)
5. Verify the column was added by running:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'customers' AND column_name = 'kyc_status';
   ```

### Option 2: Using psql Command Line

```bash
psql -U postgres -d horizon -f migrate_add_kyc_status.sql
```

### Option 3: Run SQL Directly

If you prefer, you can run this SQL directly in DBeaver:

```sql
-- Add kyc_status column if it doesn't exist
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

-- Update existing records
UPDATE customers 
SET kyc_status = 'Not Submitted' 
WHERE kyc_status IS NULL;
```

## Verification

After running the migration, verify it worked:

```sql
-- Check if column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'customers' 
AND column_name = 'kyc_status';

-- Check existing data
SELECT customer_id, full_name, kyc_status 
FROM customers 
LIMIT 5;
```

## What This Migration Does

1. **Adds `kyc_status` column** to the `customers` table if it doesn't exist
2. **Sets default value** to 'Not Submitted' for all existing records
3. **Adds a CHECK constraint** to ensure only valid status values are allowed

## After Migration

Once the migration is complete:
- ✅ The "Check Application Status" page will work correctly
- ✅ KYC status tracking will function properly
- ✅ All existing customers will have `kyc_status = 'Not Submitted'`

---

**Note:** This migration is safe to run multiple times - it checks if the column exists before adding it.

