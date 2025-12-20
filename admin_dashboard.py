"""
Admin Dashboard Module
Integrated into main application
"""

import streamlit as st
from database_config import db
from db_helpers import log_audit
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any

class AdminDashboard:
    """Admin dashboard for bank staff"""
    
    @staticmethod
    def get_pending_applications(limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending KYC applications"""
        try:
            query = """
                SELECT 
                    ka.application_id,
                    ka.customer_id,
                    c.full_name,
                    u.email,
                    c.phone_number,
                    ka.application_status,
                    ka.submission_date,
                    COUNT(DISTINCT d.document_id) as document_count,
                    COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END) as verified_count
                FROM kyc_applications ka
                LEFT JOIN customers c ON ka.customer_id = c.customer_id
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN documents d ON ka.application_id = d.application_id
                WHERE ka.application_status IN ('submitted', 'under_review', 'document_verification', 'pending_resubmission')
                GROUP BY ka.application_id, ka.customer_id, c.full_name, u.email, c.phone_number, 
                         ka.application_status, ka.submission_date
                ORDER BY ka.submission_date DESC
                LIMIT %s
            """
            return db.execute_query(query, (limit,))
        except Exception as e:
            st.error(f"Error fetching pending applications: {str(e)}")
            return []
    
    @staticmethod
    def get_fraud_alerts(limit: int = 20) -> List[Dict[str, Any]]:
        """Get fraud alerts"""
        try:
            query = """
                SELECT 
                    ka.application_id,
                    c.full_name,
                    u.email,
                    c.pan_card,
                    c.aadhar_no,
                    ka.submission_date,
                    COUNT(DISTINCT d.document_id) as doc_count,
                    COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END) as rejected_docs
                FROM kyc_applications ka
                LEFT JOIN customers c ON ka.customer_id = c.customer_id
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN documents d ON ka.application_id = d.application_id
                WHERE d.verification_status = 'rejected' OR ka.application_status = 'rejected'
                GROUP BY ka.application_id, c.full_name, u.email, c.pan_card, c.aadhar_no, ka.submission_date
                HAVING COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END) > 0
                ORDER BY ka.submission_date DESC
                LIMIT %s
            """
            return db.execute_query(query, (limit,))
        except Exception as e:
            return []
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            health = {}
            query = "SELECT COUNT(*) as count FROM kyc_applications"
            result = db.execute_one(query)
            health['total_applications'] = result['count'] if result else 0
            
            query = """
                SELECT application_status, COUNT(*) as count
                FROM kyc_applications
                GROUP BY application_status
            """
            status_counts = db.execute_query(query)
            health['status_breakdown'] = {row['application_status']: row['count'] for row in status_counts}
            
            query = """
                SELECT COUNT(*) as count
                FROM kyc_applications
                WHERE application_status IN ('submitted', 'under_review', 'document_verification')
            """
            result = db.execute_one(query)
            health['pending_applications'] = result['count'] if result else 0
            
            return health
        except Exception as e:
            return {}
    
    @staticmethod
    def update_application_status(application_id: str, new_status: str, verified_by: str, notes: str = None):
        """Update application status"""
        try:
            query = """
                UPDATE kyc_applications
                SET application_status = %s,
                    verification_date = CASE WHEN %s IN ('approved', 'rejected') THEN CURRENT_TIMESTAMP ELSE verification_date END,
                    verified_by = %s,
                    notes = COALESCE(%s, notes),
                    updated_at = CURRENT_TIMESTAMP
                WHERE application_id = %s
            """
            db.execute_query(query, (new_status, new_status, verified_by, notes, application_id), fetch=False)
            
            if new_status == 'approved':
                query = "UPDATE customers SET kyc_status = 'Approved' WHERE customer_id = (SELECT customer_id FROM kyc_applications WHERE application_id = %s)"
                db.execute_query(query, (application_id,), fetch=False)
            
            log_audit(verified_by, 'application_approve' if new_status == 'approved' else 'application_reject',
                     'application', application_id, f"Application status changed to {new_status}")
            return True
        except Exception as e:
            st.error(f"Error updating application status: {str(e)}")
            return False
    
    @staticmethod
    def render_dashboard():
        """Render the admin dashboard"""
        st.header("🔐 Admin Dashboard")
        st.markdown("---")
        
        health = AdminDashboard.get_system_health()
        if health:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Applications", health.get('total_applications', 0))
            with col2:
                st.metric("Pending Review", health.get('pending_applications', 0))
            with col3:
                st.metric("Approved", health.get('status_breakdown', {}).get('approved', 0))
            with col4:
                st.metric("Rejected", health.get('status_breakdown', {}).get('rejected', 0))
        
        tab1, tab2, tab3 = st.tabs(["📋 Pending Applications", "🚨 Fraud Alerts", "✅ Verify Applications"])
        
        with tab1:
            applications = AdminDashboard.get_pending_applications()
            if applications:
                df = pd.DataFrame(applications)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No pending applications")
        
        with tab2:
            alerts = AdminDashboard.get_fraud_alerts()
            if alerts:
                for alert in alerts:
                    with st.expander(f"⚠️ Alert: {alert.get('full_name', 'Unknown')}"):
                        st.write(f"**Application ID:** {alert.get('application_id')}")
                        st.write(f"**Rejected Documents:** {alert.get('rejected_docs', 0)}")
            else:
                st.success("✅ No fraud alerts")
        
        with tab3:
            application_id = st.text_input("Enter Application ID to verify")
            if application_id:
                query = """
                    SELECT ka.*, c.full_name, u.email
                    FROM kyc_applications ka
                    LEFT JOIN customers c ON ka.customer_id = c.customer_id
                    LEFT JOIN users u ON c.user_id = u.user_id
                    WHERE ka.application_id = %s
                """
                app = db.execute_one(query, (application_id,))
                if app:
                    st.write(f"**Customer:** {app['full_name']}")
                    st.write(f"**Status:** {app['application_status']}")
                    
                    new_status = st.selectbox(
                        "Update Status",
                        ["under_review", "document_verification", "approved", "rejected"]
                    )
                    notes = st.text_area("Notes (optional)")
                    
                    if st.button("Update Status"):
                        if AdminDashboard.update_application_status(
                            application_id, new_status, 
                            st.session_state.user['user_id'], notes
                        ):
                            st.success("Status updated!")
                            st.rerun()

admin_dashboard = AdminDashboard()

