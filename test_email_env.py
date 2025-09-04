#!/usr/bin/env python3
"""
Test email environment variable loading
"""
import os

def test_email_env():
    print("🔍 TESTING EMAIL ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    # Load environment variables the same way as server.py
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = os.environ.get("SMTP_PORT", "587")
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@police.gov")
    
    print(f"SMTP_SERVER: '{SMTP_SERVER}'")
    print(f"SMTP_PORT: '{SMTP_PORT}'")
    print(f"SMTP_USERNAME: '{SMTP_USERNAME}'")
    print(f"SMTP_PASSWORD: '{'*' * len(SMTP_PASSWORD)}' (length: {len(SMTP_PASSWORD)})")
    print(f"FROM_EMAIL: '{FROM_EMAIL}'")
    
    print(f"\n🔍 CONDITION CHECKS:")
    print(f"not SMTP_USERNAME: {not SMTP_USERNAME}")
    print(f"not SMTP_PASSWORD: {not SMTP_PASSWORD}")
    print(f"Condition (not SMTP_USERNAME or not SMTP_PASSWORD): {not SMTP_USERNAME or not SMTP_PASSWORD}")
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("\n❌ EMAIL WILL BE LOGGED ONLY (not sent)")
        print("   Reason: SMTP_USERNAME or SMTP_PASSWORD is empty")
    else:
        print("\n✅ EMAIL WILL BE SENT")
        print("   All SMTP credentials are present")

if __name__ == "__main__":
    test_email_env()