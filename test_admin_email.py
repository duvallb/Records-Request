#!/usr/bin/env python3
"""
Test script to send email directly to administrator
"""
import requests
import json
import sys

def test_admin_email():
    base_url = "https://request-hub-6.preview.emergentagent.com/api"
    
    # First, create an admin user and login
    print("🔐 Creating admin user for email test...")
    
    admin_data = {
        "email": "request@shakerpd.com",
        "password": "AdminTest123!",
        "full_name": "Test Administrator",
        "role": "admin"
    }
    
    # Register admin (or it might already exist)
    register_response = requests.post(f"{base_url}/auth/register", json=admin_data)
    print(f"Register response: {register_response.status_code}")
    
    # Login to get token
    login_data = {
        "email": "request@shakerpd.com",
        "password": "AdminTest123!"
    }
    
    login_response = requests.post(f"{base_url}/auth/login", json=login_data)
    print(f"Login response: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        print(f"✅ Admin login successful")
        
        # Send test email
        print(f"📧 Sending test email to request@shakerpd.com...")
        headers = {"Authorization": f"Bearer {token}"}
        
        email_response = requests.post(f"{base_url}/test-email", headers=headers)
        print(f"Email test response: {email_response.status_code}")
        print(f"Response: {email_response.json()}")
        
        if email_response.status_code == 200:
            print("✅ Test email sent successfully!")
            print("📧 Check your inbox at request@shakerpd.com")
        else:
            print("❌ Failed to send test email")
            
    else:
        print("❌ Admin login failed")
        print(f"Response: {login_response.json()}")

if __name__ == "__main__":
    test_admin_email()