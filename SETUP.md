# Ti Tans Bank KYC System - Setup Guide

## Prerequisites

### 1. Python Environment

**Required Version**: Python 3.8 or higher

**Check Python Version**:
```bash
python --version
# or
python3 --version
```

**Install Python** (if not installed):
- Windows: Download from [python.org](https://www.python.org/downloads/)
- macOS: `brew install python3`
- Linux: `sudo apt-get install python3 python3-pip`

### 2. PostgreSQL Database

**Required Version**: PostgreSQL 12 or higher

**Install PostgreSQL**:
- Windows: Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- macOS: `brew install postgresql`
- Linux: `sudo apt-get install postgresql postgresql-contrib`

**Verify Installation**:
```bash
psql --version
```

**Start PostgreSQL Service**:
- Windows: Start PostgreSQL service from Services
- macOS: `brew services start postgresql`
- Linux: `sudo systemctl start postgresql`

### 3. Tesseract OCR Engine (Optional but Recommended)

**Purpose**: Real OCR text extraction from documents

**Install Tesseract**:
- Windows: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
  - Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

**Verify Installation**:
```bash
tesseract --version
```

**Note**: The system works without Tesseract (uses mock OCR), but real OCR provides better validation.

## Environment Setup

### Step 1: Clone/Download Project

```bash
cd /path/to/project
# Project should be in: C:\Users\Ram Kumar\OneDrive\Desktop\djangoo\AIDEMO
```

### Step 2: Create Virtual Environment

**Windows**:
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Verify Activation**:
- Prompt should show `(.venv)` prefix

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Verify Installation**:
```bash
pip list
# Should show: streamlit, psycopg2-binary, Pillow, pandas, etc.
```

### Step 4: Set Up PostgreSQL Database

#### 4.1. Create Database

**Using psql**:
```bash
psql -U postgres
```

```sql
CREATE DATABASE horizon_bank_kyc;
\q
```

**Using pgAdmin**:
1. Open pgAdmin
2. Right-click "Databases" → "Create" → "Database"
3. Name: `horizon_bank_kyc`
4. Owner: `postgres`
5. Click "Save"

#### 4.2. Initialize Schema

```bash
python database_init.py
```

**Expected Output**:
```
Database 'horizon_bank_kyc' created successfully.
Schema initialized successfully.
Tables created: users, customers, kyc_applications, documents, audit_logs, notifications
Views created: v_application_status_summary, v_customer_kyc_dashboard
```

### Step 5: Configure Environment Variables

**Option 1: Copy from template (Recommended)**
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

**Option 2: Create `.env` file manually** in project root:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=horizon_bank_kyc
DB_USER=postgres
DB_PASSWORD=test

# Optional: Tesseract Path (Windows)
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

**Note**: 
- The `.env` file is in `.gitignore` (not tracked by git) for security
- Default password is `test` (change in production)
- Tesseract path only needed if Tesseract is installed in non-default location
- If `.env` doesn't exist, the system uses default values from `database_config.py`

## Software Integration

### PyCharm Setup

#### 1. Open Project in PyCharm

1. Launch PyCharm
2. File → Open → Select project directory (`AIDEMO`)
3. PyCharm will detect Python files

#### 2. Configure Python Interpreter

1. File → Settings → Project → Python Interpreter
2. Click gear icon → "Add..."
3. Select "Existing environment"
4. Browse to `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python` (macOS/Linux)
5. Click "OK"

#### 3. Configure Run Configuration

1. Run → Edit Configurations
2. Click "+" → "Python"
3. Name: "Ti Tans Bank KYC"
4. Script path: `app_main.py`
5. Working directory: Project root
6. Python interpreter: `.venv` interpreter
7. Click "OK"

#### 4. Run Application

- Click green "Run" button or press `Shift+F10`
- Application will start on `http://localhost:8501`

### DBeaver Setup (PostgreSQL Visualization)

#### 1. Install DBeaver

- Download from [dbeaver.io](https://dbeaver.io/download/)
- Install and launch

#### 2. Create PostgreSQL Connection

1. Database → New Database Connection
2. Select "PostgreSQL"
3. Click "Next"

#### 3. Configure Connection

**Main Tab**:
- Host: `localhost`
- Port: `5432`
- Database: `horizon_bank_kyc`
- Username: `postgres`
- Password: `test` (or your password)

**Driver Properties** (if needed):
- Click "Edit Driver Settings"
- Ensure PostgreSQL driver is installed

#### 4. Test Connection

1. Click "Test Connection"
2. If driver missing, DBeaver will prompt to download
3. Click "Finish" after successful test

#### 5. Explore Database

- Expand connection → `horizon_bank_kyc` → Schemas → `public` → Tables
- View tables: `users`, `customers`, `kyc_applications`, `documents`, etc.
- Right-click table → "View Data" to see records

### Streamlit Configuration

#### Run Application

**Command Line**:
```bash
streamlit run app_main.py
```

**PyCharm**:
- Use run configuration created above

**Default URL**: `http://localhost:8501`

#### Custom Port

```bash
streamlit run app_main.py --server.port 8502
```

## Verification Steps

### 1. Database Connection Test

**In Application**:
1. Launch application
2. Check sidebar for "🟢 Database Connected" indicator
3. If red, check database credentials in `.env`

**Manual Test**:
```python
python -c "from database_config import db; print('Connected!' if db.test_connection() else 'Failed')"
```

### 2. OCR Engine Test

**Check Tesseract**:
```python
python -c "from ocr_engine import ocr_engine; print('Tesseract:', ocr_engine.tesseract_available)"
```

**Expected**: `Tesseract: True` (if installed) or `False` (uses mock)

### 3. Application Test

1. Navigate to Landing Page
2. Click "Open Account" → Fill registration form
3. Submit → Should create account
4. Login with credentials
5. Should redirect to KYC Portal (first login)

## Troubleshooting

### Database Connection Issues

**Error**: `Connection refused` or `password authentication failed`

**Solutions**:
1. Verify PostgreSQL is running: `pg_isready`
2. Check credentials in `.env` file
3. Verify database exists: `psql -U postgres -l`
4. Check `pg_hba.conf` for authentication settings

### Tesseract Not Found

**Error**: `TesseractNotFoundError`

**Solutions**:
1. Install Tesseract (see Prerequisites)
2. Add path to `.env`: `TESSERACT_CMD=/path/to/tesseract`
3. System works without Tesseract (uses mock OCR)

### Port Already in Use

**Error**: `Port 8501 is already in use`

**Solutions**:
1. Use different port: `streamlit run app_main.py --server.port 8502`
2. Kill existing process:
   - Windows: `netstat -ano | findstr :8501` then `taskkill /PID <pid> /F`
   - macOS/Linux: `lsof -ti:8501 | xargs kill`

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solutions**:
1. Activate virtual environment: `.venv\Scripts\activate` (Windows)
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Verify Python interpreter in PyCharm

### Schema Initialization Errors

**Error**: `relation already exists`

**Solutions**:
1. Drop and recreate database:
   ```sql
   DROP DATABASE horizon_bank_kyc;
   CREATE DATABASE horizon_bank_kyc;
   ```
2. Re-run `python database_init.py`

## Production Deployment Considerations

### Security

1. **Change Default Password**: Update `DB_PASSWORD` in `.env`
2. **Use Environment Variables**: Never commit `.env` to version control
3. **Enable SSL**: Configure PostgreSQL SSL connections
4. **Password Hashing**: Consider upgrading from SHA-256 to bcrypt

### Performance

1. **Connection Pooling**: Already implemented (1-10 connections)
2. **Database Indexing**: Ensure indexes on frequently queried columns
3. **Caching**: Consider Redis for session management
4. **CDN**: Serve static assets via CDN

### Monitoring

1. **Logging**: Implement structured logging (e.g., Python `logging` module)
2. **Error Tracking**: Integrate Sentry or similar
3. **Database Monitoring**: Use pg_stat_statements for query analysis
4. **Application Metrics**: Monitor response times, error rates

## Next Steps

1. **Review Architecture**: Read `ARCHITECTURE.md` for system design
2. **User Guide**: Read `USER_MANUAL.md` for user workflows
3. **Admin Guide**: Read `ADMIN_GUIDE.md` for admin operations
4. **Test System**: Create test accounts and verify KYC flow
5. **Customize**: Adjust validation thresholds in `kyc_validator.py` and `ai_kyc_validator.py`

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review error logs in application console
3. Check database logs: `tail -f /var/log/postgresql/postgresql.log`
4. Review audit logs in `audit_logs` table

