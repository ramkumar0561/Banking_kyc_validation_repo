# Horizon Bank - Professional Banking Portal

A comprehensive Banking KYC (Know Your Customer) document upload and verification system with progressive onboarding, OCR integration, and admin dashboard.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python database_init.py
```

### 3. Run Application
```bash
streamlit run app_main.py
```

## ✨ Key Features

### Progressive KYC Flow
- **Step 1: Registration** - Create account with personal, employment, and address details
- **Step 2: Post-Login KYC Portal** - Complete identity verification and photo upload
- **Optional Fields** - Nominee details, OTP verification, additional information

### Enhanced Status Tracking
- **State A:** No account found
- **State B:** Wrong credentials (handled in login)
- **State C:** KYC not submitted
- **State D:** KYC in progress
- **State E:** KYC approved and active

### OCR Document Verification
- Automatic text extraction from documents
- Aadhar, PAN, Passport validation
- Completeness checking
- Confidence scoring

### Admin Dashboard (Integrated)
- Access via Admin Mode toggle
- Pending applications view
- Fraud alerts
- System health metrics
- Document verification tools

### Audit Reports (Integrated)
- CSV/Excel export
- Application audit trails
- Compliance reports
- Date range filtering

## 📁 Project Structure

```
AIDEMO/
├── app_main.py              # Main application (Run this!)
├── database_config.py       # PostgreSQL connection
├── database_schema.sql      # Database schema
├── database_init.py         # Database initialization
├── db_helpers.py           # Database operations
├── styling.py              # Professional banking CSS
├── ocr_engine.py           # OCR document verification
├── notifications.py        # Toast notifications
├── admin_dashboard.py      # Admin panel
├── audit_reports.py        # Audit reports
└── requirements.txt        # Dependencies
```

## 🔧 Configuration

### Database Setup
Edit `database_config.py` with your PostgreSQL credentials:
```python
'host': 'localhost',
'port': '5432',
'database': 'horizon_bank_kyc',
'user': 'postgres',
'password': 'your_password'
```

### Admin Access
To create an admin user:
```sql
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

## 📊 Database Schema

- **users** - Authentication
- **customers** - Customer profiles with KYC status
- **kyc_applications** - Application tracking
- **documents** - Document metadata with OCR data
- **audit_logs** - Complete audit trail
- **notifications** - Customer notifications

## 🎯 User Flow

1. **Registration** → Create account (KYC Status: 'Not Submitted')
2. **First Login** → Redirected to KYC Portal
3. **KYC Portal** → Upload identity document & photo (Mandatory)
4. **Optional** → Add nominee details, OTP verification
5. **Submission** → KYC Status: 'Submitted'
6. **Admin Review** → Verification process
7. **Approval** → KYC Status: 'Approved'

## 🔐 Security Features

- Password hashing (SHA-256)
- SQL injection prevention
- Session management
- Complete audit logging
- Role-based access control

## 📝 Status Check States

- **State A:** "No account found with these details."
- **State B:** "Incorrect credentials. Please try again." (Login page)
- **State C:** "Application Details Found. Status: 📄 KYC not submitted, action required."
- **State D:** "Application Details Found. Status: 📄 KYC submitted, verification in progress."
- **State E:** "Application Details Found. Status: ✅ KYC Verified & Account Fully Active."

## 🐛 Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check credentials in `database_config.py`
- Run `python database_init.py`

### Webcam Not Working
- Check browser permissions
- Use "Upload Photo" as fallback
- Ensure HTTPS or localhost (secure context required)

### OCR Not Working
- Install Tesseract OCR
- System uses mock OCR if unavailable
- Check `ocr_engine.py` for path configuration

## 📚 Documentation

- `SETUP_GUIDE.md` - Detailed setup instructions
- `USER_MANUAL.md` - End user guide
- `ADMIN_GUIDE.md` - Admin dashboard guide

## 🎉 Features Implemented

✅ Progressive KYC Flow (Registration → Post-Login KYC)
✅ Enhanced Status Checking (5 States)
✅ Webcam Integration with Fallback
✅ OCR Document Verification
✅ Admin Dashboard (Integrated)
✅ Audit Reports (Integrated)
✅ Professional Banking UI
✅ Complete Data Persistence

---

**Built with:** Streamlit, PostgreSQL, Python, OCR (Tesseract)
**Status:** Production-Ready ✅

