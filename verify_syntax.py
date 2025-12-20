"""
Syntax Verification Script
Run this to verify all Python files have correct syntax
"""

import ast
import sys
from pathlib import Path

def verify_file(file_path):
    """Verify a Python file has correct syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print(f"[OK] {file_path} - Syntax OK")
        return True
    except SyntaxError as e:
        print(f"[ERROR] {file_path} - Syntax Error:")
        print(f"   Line {e.lineno}: {e.msg}")
        if e.text:
            print(f"   {e.text.strip()}")
        return False
    except Exception as e:
        print(f"[WARNING] {file_path} - Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Syntax Verification - Horizon Bank KYC System")
    print("=" * 60)
    
    files_to_check = [
        "app_main.py",
        "database_config.py",
        "database_init.py",
        "db_helpers.py",
        "styling.py",
        "ocr_engine.py",
        "notifications.py",
        "admin_dashboard.py",
        "audit_reports.py"
    ]
    
    all_ok = True
    for file in files_to_check:
        if Path(file).exists():
            if not verify_file(file):
                all_ok = False
        else:
            print(f"[WARNING] {file} - File not found")
    
    print("=" * 60)
    if all_ok:
        print("[SUCCESS] All files have correct syntax!")
    else:
        print("[ERROR] Some files have syntax errors. Please fix them.")
    print("=" * 60)

