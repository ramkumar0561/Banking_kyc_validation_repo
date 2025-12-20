-- =====================================================
-- Horizon Bank KYC System - Database Schema
-- PostgreSQL Database Design
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. USERS TABLE (Authentication & Login)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'customer' CHECK (role IN ('customer', 'admin', 'verifier')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- =====================================================
-- 2. CUSTOMERS TABLE (Customer Profile)
-- =====================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    marital_status VARCHAR(20),
    age INTEGER,
    address TEXT,
    city_town VARCHAR(100),
    pincode VARCHAR(10),
    pan_card VARCHAR(20),
    aadhar_no VARCHAR(20),
    phone_number VARCHAR(15),
    salary DECIMAL(15, 2),
    annual_income DECIMAL(15, 2),
    occupation VARCHAR(100),
    photo_path TEXT,
    kyc_status VARCHAR(50) DEFAULT 'Not Submitted' CHECK (kyc_status IN ('Not Submitted', 'In Progress', 'Submitted', 'Under Review', 'Approved', 'Rejected')),
    nominee_name VARCHAR(100),
    nominee_relation VARCHAR(50),
    otp_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. KYC_APPLICATIONS TABLE (KYC Application Status)
-- =====================================================
CREATE TABLE IF NOT EXISTS kyc_applications (
    application_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(customer_id) ON DELETE CASCADE,
    application_status VARCHAR(50) DEFAULT 'submitted' 
        CHECK (application_status IN ('submitted', 'under_review', 'document_verification', 
              'approved', 'rejected', 'pending_resubmission')),
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verification_date TIMESTAMP,
    verified_by UUID REFERENCES users(user_id),
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. DOCUMENTS TABLE (Uploaded Documents)
-- =====================================================
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES kyc_applications(application_id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL 
        CHECK (document_type IN ('identity_proof', 'address_proof', 'photo', 'other')),
    document_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    ocr_extracted_data JSONB,
    verification_status VARCHAR(50) DEFAULT 'pending'
        CHECK (verification_status IN ('pending', 'verified', 'rejected', 'needs_review')),
    verification_notes TEXT,
    verified_by UUID REFERENCES users(user_id),
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 5. DOCUMENT_REQUIREMENTS TABLE (KYC Document Requirements)
-- =====================================================
CREATE TABLE IF NOT EXISTS document_requirements (
    requirement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type VARCHAR(50) NOT NULL,
    document_name VARCHAR(100) NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    accepted_formats TEXT[],
    max_file_size_mb INTEGER DEFAULT 10,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 6. AUDIT_LOGS TABLE (Audit Trail)
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    action_type VARCHAR(50) NOT NULL 
        CHECK (action_type IN ('login', 'logout', 'document_upload', 'document_verification', 
              'application_submit', 'application_approve', 'application_reject', 
              'profile_update', 'password_change', 'admin_action')),
    entity_type VARCHAR(50),
    entity_id UUID,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 7. NOTIFICATIONS TABLE (Customer Notifications)
-- =====================================================
CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(customer_id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES for Performance
-- =====================================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_kyc_status ON customers(kyc_status);
CREATE INDEX idx_kyc_applications_customer_id ON kyc_applications(customer_id);
CREATE INDEX idx_kyc_applications_status ON kyc_applications(application_status);
CREATE INDEX idx_documents_application_id ON documents(application_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_notifications_customer_id ON notifications(customer_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- =====================================================
-- TRIGGERS for updated_at timestamps
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kyc_applications_updated_at BEFORE UPDATE ON kyc_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INSERT DEFAULT DOCUMENT REQUIREMENTS
-- =====================================================
INSERT INTO document_requirements (document_type, document_name, is_mandatory, accepted_formats, max_file_size_mb, description)
VALUES 
    ('identity_proof', 'Aadhar Card', TRUE, ARRAY['pdf', 'jpg', 'png'], 10, 'Government issued Aadhar card'),
    ('identity_proof', 'PAN Card', TRUE, ARRAY['pdf', 'jpg', 'png'], 10, 'Permanent Account Number card'),
    ('identity_proof', 'Passport', FALSE, ARRAY['pdf', 'jpg', 'png'], 10, 'Valid passport'),
    ('identity_proof', 'Voter ID', FALSE, ARRAY['pdf', 'jpg', 'png'], 10, 'Voter identification card'),
    ('address_proof', 'Utility Bill', TRUE, ARRAY['pdf', 'jpg', 'png'], 10, 'Electricity, water, or gas bill'),
    ('address_proof', 'Bank Statement', FALSE, ARRAY['pdf'], 10, 'Bank statement with address'),
    ('address_proof', 'Rental Agreement', FALSE, ARRAY['pdf', 'jpg', 'png'], 10, 'Rental agreement document'),
    ('photo', 'Passport Photo', TRUE, ARRAY['jpg', 'png'], 5, 'Recent passport size photograph')
ON CONFLICT DO NOTHING;

-- =====================================================
-- VIEWS for Reporting
-- =====================================================

-- View: Application Status Summary
CREATE OR REPLACE VIEW v_application_status_summary AS
SELECT 
    ka.application_status,
    COUNT(*) as total_count,
    COUNT(CASE WHEN ka.created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days
FROM kyc_applications ka
GROUP BY ka.application_status;

-- View: Customer KYC Dashboard
CREATE OR REPLACE VIEW v_customer_kyc_dashboard AS
SELECT 
    c.customer_id,
    c.full_name,
    u.email,
    c.kyc_status,
    ka.application_id,
    ka.application_status,
    ka.submission_date,
    ka.verification_date,
    COUNT(DISTINCT d.document_id) as total_documents,
    COUNT(DISTINCT CASE WHEN d.verification_status = 'verified' THEN d.document_id END) as verified_documents,
    COUNT(DISTINCT CASE WHEN d.verification_status = 'rejected' THEN d.document_id END) as rejected_documents
FROM customers c
LEFT JOIN users u ON c.user_id = u.user_id
LEFT JOIN kyc_applications ka ON c.customer_id = ka.customer_id
LEFT JOIN documents d ON ka.application_id = d.application_id
GROUP BY c.customer_id, c.full_name, u.email, c.kyc_status, ka.application_id, ka.application_status, ka.submission_date, ka.verification_date;

