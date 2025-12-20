-- Migration Script: Add kyc_status column to customers table
-- Run this script in DBeaver or psql to update your database schema

-- Check if column exists and add it if it doesn't
DO $$ 
BEGIN
    -- Check if column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'kyc_status'
    ) THEN
        -- Add the column
        ALTER TABLE customers 
        ADD COLUMN kyc_status VARCHAR(50) DEFAULT 'Not Submitted' 
        CHECK (kyc_status IN ('Not Submitted', 'In Progress', 'Submitted', 'Under Review', 'Approved', 'Rejected'));
        
        RAISE NOTICE 'Column kyc_status added successfully';
    ELSE
        RAISE NOTICE 'Column kyc_status already exists';
    END IF;
END $$;

-- Update existing records to have default value if NULL
UPDATE customers 
SET kyc_status = 'Not Submitted' 
WHERE kyc_status IS NULL;

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'customers' 
AND column_name = 'kyc_status';

