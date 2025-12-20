# Setup Guide - Horizon Bank KYC System

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Optional but Recommended)

**Windows:**
- Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Install and note the installation path
- Update `ocr_engine.py` if path is different

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 3. Configure Database

Edit `database_config.py` with your PostgreSQL credentials:

```python
self.config = {
    'host': 'localhost',
    'port': '5432',
    'database': 'horizon_bank_kyc',
    'user': 'postgres',
    'password': 'your_password_here'
}
```

### 4. Initialize Database

```bash
python database_init.py
```

This will:
- Create the database if it doesn't exist
- Create all required tables
- Insert default document requirements
- Create indexes and triggers

### 5. Run the Application

```bash
streamlit run app_main.py
```

The application will open at `http://localhost:8501`

## Verification

1. **Test Registration:**
   - Go to "Open Account"
   - Fill all mandatory fields
   - Submit registration
   - Verify account is created

2. **Test Login:**
   - Login with registered credentials
   - Should redirect to KYC Portal if KYC not submitted

3. **Test KYC Portal:**
   - Upload identity document
   - Upload photo or use webcam
   - Submit KYC application

4. **Test Status Check:**
   - Search by email/phone/application ID
   - Verify status is displayed correctly

5. **Test Admin Dashboard:**
   - Create admin user (see below)
   - Enable Admin Mode
   - Access Admin Dashboard

## Creating Admin User

1. Register a normal user
2. Connect to PostgreSQL:
```sql
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```
3. Login and enable Admin Mode

## Troubleshooting

### Database Connection Failed
- Check PostgreSQL service is running
- Verify credentials in `database_config.py`
- Ensure database exists: `psql -U postgres -l`

### Import Errors
- Install all dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

### Webcam Not Working
- Check browser permissions
- Use "Upload Photo" option
- Ensure secure context (HTTPS or localhost)

### OCR Errors
- Install Tesseract OCR
- Check path in `ocr_engine.py`
- System will use mock OCR if unavailable

## Next Steps

After setup:
1. Test user registration
2. Test KYC submission
3. Create admin user
4. Test admin dashboard
5. Generate audit reports

---

**Ready to use!** 🎉

