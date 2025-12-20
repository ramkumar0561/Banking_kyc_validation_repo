"""
Migration Script: Add kyc_status column to customers table if it doesn't exist
Run this script to update your database schema
"""

import sys
from database_config import Database

def migrate_add_kyc_status():
    """Add kyc_status column to customers table if it doesn't exist"""
    db = Database()
    
    try:
        # Check if column exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='customers' AND column_name='kyc_status'
        """
        result = db.execute_one(check_query)
        
        if result:
            print("✅ Column 'kyc_status' already exists in 'customers' table.")
            return True
        
        # Add the column
        print("Adding 'kyc_status' column to 'customers' table...")
        alter_query = """
            ALTER TABLE customers 
            ADD COLUMN kyc_status VARCHAR(50) DEFAULT 'Not Submitted' 
            CHECK (kyc_status IN ('Not Submitted', 'In Progress', 'Submitted', 'Under Review', 'Approved', 'Rejected'))
        """
        db.execute_query(alter_query, fetch=False)
        print("✅ Successfully added 'kyc_status' column to 'customers' table.")
        
        # Update existing records to have default value
        update_query = "UPDATE customers SET kyc_status = 'Not Submitted' WHERE kyc_status IS NULL"
        db.execute_query(update_query, fetch=False)
        print("✅ Updated existing records with default 'kyc_status' value.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add kyc_status Column")
    print("=" * 60)
    
    success = migrate_add_kyc_status()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)

