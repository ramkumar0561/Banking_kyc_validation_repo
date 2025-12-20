"""
Audit Reports Module
Integrated into main application
"""

import streamlit as st
import pandas as pd
from database_config import db
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict

class AuditReports:
    """Generate and export audit reports"""
    
    @staticmethod
    def get_audit_logs(start_date: datetime = None, end_date: datetime = None, 
                      action_type: str = None) -> pd.DataFrame:
        """Get audit logs as DataFrame"""
        try:
            query = """
                SELECT 
                    al.log_id,
                    al.created_at,
                    u.username,
                    u.email,
                    al.action_type,
                    al.entity_type,
                    al.entity_id,
                    al.description,
                    al.ip_address
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND al.created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND al.created_at <= %s"
                params.append(end_date)
            
            if action_type:
                query += " AND al.action_type = %s"
                params.append(action_type)
            
            query += " ORDER BY al.created_at DESC"
            
            logs = db.execute_query(query, tuple(params) if params else None)
            
            if logs:
                return pd.DataFrame(logs)
            else:
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching audit logs: {str(e)}")
            return pd.DataFrame()
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame) -> BytesIO:
        """Export DataFrame to CSV"""
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return output
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame) -> BytesIO:
        """Export DataFrame to Excel"""
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Audit Report')
            output.seek(0)
            return output
        except ImportError:
            return None
    
    @staticmethod
    def render_reports_page():
        """Render the audit reports page"""
        st.header("📊 Audit Reports & Compliance")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())
        
        action_type = st.selectbox(
            "Action Type",
            ["All", "login", "logout", "document_upload", "application_submit", "application_approve"]
        )
        
        action_filter = None if action_type == "All" else action_type
        
        logs_df = AuditReports.get_audit_logs(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()),
            action_filter
        )
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                csv_data = AuditReports.export_to_csv(logs_df)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            with col2:
                excel_data = AuditReports.export_to_excel(logs_df)
                if excel_data:
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("No audit logs found for the selected period")

audit_reports = AuditReports()

