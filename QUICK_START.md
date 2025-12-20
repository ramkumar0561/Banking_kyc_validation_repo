# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database
```bash
python database_init.py
```

### Step 3: Run Application
```bash
streamlit run app_main.py
```

## 📋 Key Features

### For Users:
1. **Register** → Create account (Personal Info, Employment, Address)
2. **Login** → Access your account
3. **Complete KYC** → Upload identity document & photo (mandatory)
4. **Check Status** → Track your application progress

### For Admins:
1. **Enable Admin Mode** → Toggle in sidebar
2. **Admin Dashboard** → View pending applications, fraud alerts
3. **Audit Reports** → Generate compliance reports, export CSV/Excel

## 🔑 Important Notes

- **Registration** creates account with KYC Status: "Not Submitted"
- **First Login** redirects to KYC Portal automatically
- **KYC Portal** requires identity document and photo (mandatory)
- **Status Check** shows 5 different states based on application progress
- **Admin Mode** requires admin role (set in database)

## 🐛 Quick Troubleshooting

**Database not connecting?**
- Check PostgreSQL is running
- Verify credentials in `database_config.py`

**Webcam not working?**
- Use "Upload Photo" option
- Check browser permissions

**Can't access admin?**
- Update user role: `UPDATE users SET role = 'admin' WHERE username = 'your_username';`

---

**That's it!** You're ready to use the application. 🎉

