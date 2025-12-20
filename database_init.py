"""
Database Initialization Script
Run this script to create the database schema
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from database_config import DatabaseConfig
import os

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    config = DatabaseConfig()
    
    # Connect to default postgres database to create our database
    try:
        conn = psycopg2.connect(
            host=config.config['host'],
            port=config.config['port'],
            database='postgres',  # Connect to default database
            user=config.config['user'],
            password=config.config['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config.config['database']}'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(f"CREATE DATABASE {config.config['database']}")
            print(f"✅ Database '{config.config['database']}' created successfully")
        else:
            print(f"ℹ️  Database '{config.config['database']}' already exists")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
        return False

def initialize_schema():
    """Initialize database schema by reading and executing SQL file"""
    try:
        # Connect to database first
        config = DatabaseConfig()
        conn = config.get_connection_simple()
        cur = conn.cursor()
        
        # Drop existing views if they exist (to handle re-initialization)
        try:
            cur.execute("DROP VIEW IF EXISTS v_customer_kyc_dashboard CASCADE;")
            cur.execute("DROP VIEW IF EXISTS v_application_status_summary CASCADE;")
            conn.commit()
            print("   ℹ️  Dropped existing views (if any)")
        except Exception as e:
            print(f"   ℹ️  Note: {str(e)}")
            conn.rollback()
        
        # Read SQL schema file
        with open('database_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema SQL
        cur.execute(schema_sql)
        conn.commit()
        
        print("✅ Database schema initialized successfully")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error initializing schema: {str(e)}")
        import traceback
        print(f"\nDetailed error:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Horizon Bank KYC - Database Initialization")
    print("=" * 60)
    
    print("\n1. Creating database if not exists...")
    if create_database_if_not_exists():
        print("\n2. Initializing database schema...")
        if initialize_schema():
            print("\n" + "=" * 60)
            print("✅ Database initialization completed successfully!")
            print("=" * 60)
        else:
            print("\n❌ Schema initialization failed")
    else:
        print("\n❌ Database creation failed")

