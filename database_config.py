"""
Database Configuration and Connection Module
Handles PostgreSQL database connections and configuration
"""

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict, Any
import streamlit as st

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'horizon_bank_kyc'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        self.connection_pool: Optional[pool.ThreadedConnectionPool] = None
    
    def create_connection_pool(self, min_conn=1, max_conn=10):
        """Create a connection pool for database connections"""
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                min_conn, max_conn,
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            return True
        except Exception as e:
            st.error(f"Error creating connection pool: {str(e)}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        if self.connection_pool is None:
            self.create_connection_pool()
        
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def get_connection_simple(self):
        """Get a simple database connection (for initialization)"""
        try:
            return psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection_simple()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Database connection test failed: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[list]:
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    if fetch:
                        return cur.fetchall()
                    return None
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            raise
    
    def close_pool(self):
        """Close the connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()

# Global database instance
db = DatabaseConfig()

