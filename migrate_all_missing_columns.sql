-- Comprehensive Migration Script: Add ALL Missing Columns to customers table
-- Run this script in DBeaver or psql to update your database schema
-- This script is safe to run multiple times - it checks if columns exist before adding them

DO $$ 
BEGIN
    -- Add kyc_status column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'kyc_status'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN kyc_status VARCHAR(50) DEFAULT 'Not Submitted' 
        CHECK (kyc_status IN ('Not Submitted', 'In Progress', 'Submitted', 'Under Review', 'Approved', 'Rejected'));
        
        RAISE NOTICE 'Column kyc_status added successfully';
    ELSE
        RAISE NOTICE 'Column kyc_status already exists';
    END IF;

    -- Add nominee_name column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'nominee_name'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN nominee_name VARCHAR(100);
        
        RAISE NOTICE 'Column nominee_name added successfully';
    ELSE
        RAISE NOTICE 'Column nominee_name already exists';
    END IF;

    -- Add nominee_relation column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'nominee_relation'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN nominee_relation VARCHAR(50);
        
        RAISE NOTICE 'Column nominee_relation added successfully';
    ELSE
        RAISE NOTICE 'Column nominee_relation already exists';
    END IF;

    -- Add otp_verified column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'otp_verified'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN otp_verified BOOLEAN DEFAULT FALSE;
        
        RAISE NOTICE 'Column otp_verified added successfully';
    ELSE
        RAISE NOTICE 'Column otp_verified already exists';
    END IF;

    -- Add first_name column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'first_name'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN first_name VARCHAR(50);
        
        -- If full_name exists, try to extract first name (optional)
        UPDATE customers 
        SET first_name = SPLIT_PART(full_name, ' ', 1)
        WHERE first_name IS NULL AND full_name IS NOT NULL;
        
        RAISE NOTICE 'Column first_name added successfully';
    ELSE
        RAISE NOTICE 'Column first_name already exists';
    END IF;

    -- Add last_name column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'last_name'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN last_name VARCHAR(50);
        
        -- If full_name exists, try to extract last name (optional)
        UPDATE customers 
        SET last_name = CASE 
            WHEN array_length(string_to_array(full_name, ' '), 1) > 1 
            THEN array_to_string((string_to_array(full_name, ' '))[2:], ' ')
            ELSE ''
        END
        WHERE last_name IS NULL AND full_name IS NOT NULL;
        
        RAISE NOTICE 'Column last_name added successfully';
    ELSE
        RAISE NOTICE 'Column last_name already exists';
    END IF;

    -- Add marital_status column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'marital_status'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN marital_status VARCHAR(20);
        
        RAISE NOTICE 'Column marital_status added successfully';
    ELSE
        RAISE NOTICE 'Column marital_status already exists';
    END IF;

    -- Add salary column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'salary'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN salary DECIMAL(15, 2);
        
        RAISE NOTICE 'Column salary added successfully';
    ELSE
        RAISE NOTICE 'Column salary already exists';
    END IF;

    -- Add annual_income column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'annual_income'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN annual_income DECIMAL(15, 2);
        
        RAISE NOTICE 'Column annual_income added successfully';
    ELSE
        RAISE NOTICE 'Column annual_income already exists';
    END IF;

    -- Add occupation column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'occupation'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN occupation VARCHAR(100);
        
        RAISE NOTICE 'Column occupation added successfully';
    ELSE
        RAISE NOTICE 'Column occupation already exists';
    END IF;

    -- Add photo_path column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'customers' 
        AND column_name = 'photo_path'
    ) THEN
        ALTER TABLE customers 
        ADD COLUMN photo_path TEXT;
        
        RAISE NOTICE 'Column photo_path added successfully';
    ELSE
        RAISE NOTICE 'Column photo_path already exists';
    END IF;

END $$;

-- Update existing records with default values
UPDATE customers 
SET kyc_status = 'Not Submitted' 
WHERE kyc_status IS NULL;

UPDATE customers 
SET otp_verified = FALSE 
WHERE otp_verified IS NULL;

-- Verify all columns were added
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

