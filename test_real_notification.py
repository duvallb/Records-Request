#!/usr/bin/env python3
"""
Test real notification workflow with actual administrator email
"""
import requests
import json
import time

def test_real_email_notification():
    base_url = "https://foia-request.preview.emergentagent.com/api"
    
    print("🔍 Testing REAL email notification workflow...")
    print("=" * 60)
    
    # Step 1: Create a citizen user
    print("👤 Creating citizen user...")
    citizen_data = {
        "email": "test.citizen@testdomain.com",
        "password": "CitizenTest123!",
        "full_name": "Test Citizen",
        "role": "user"
    }
    
    citizen_register = requests.post(f"{base_url}/auth/register", json=citizen_data)
    citizen_login = requests.post(f"{base_url}/auth/login", json={
        "email": citizen_data["email"],
        "password": citizen_data["password"]
    })
    
    if citizen_login.status_code != 200:
        print("❌ Failed to create/login citizen")
        return
        
    citizen_token = citizen_login.json()["access_token"]
    print("✅ Citizen user ready")
    
    # Step 2: Ensure admin user exists with real email
    print("👤 Setting up administrator...")
    admin_data = {
        "email": "request@shakerpd.com",  # Real admin email
        "password": "AdminTest123!",
        "full_name": "Shaker Police Administrator",
        "role": "admin"
    }
    
    requests.post(f"{base_url}/auth/register", json=admin_data)  # May already exist
    admin_login = requests.post(f"{base_url}/auth/login", json={
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    
    if admin_login.status_code != 200:
        print("❌ Failed to setup administrator")
        return
        
    admin_token = admin_login.json()["access_token"]
    print("✅ Administrator ready")
    
    # Step 3: Create a new request that should trigger admin notification
    print("📝 Creating new records request...")
    request_data = {
        "title": "Police Report Request - Main Street Incident",
        "description": "I need a copy of the police report for incident #2024-12345 that occurred on Main Street on December 15, 2024. This is for insurance purposes.",
        "request_type": "police_report",
        "priority": "high"
    }
    
    headers = {"Authorization": f"Bearer {citizen_token}"}
    request_response = requests.post(f"{base_url}/requests", json=request_data, headers=headers)
    
    if request_response.status_code != 200:
        print("❌ Failed to create request")
        print(f"Response: {request_response.json()}")
        return
        
    request_id = request_response.json()["id"]
    print(f"✅ Request created: {request_id}")
    print(f"📧 Admin notification email should be sent to: request@shakerpd.com")
    
    # Step 4: Wait a moment for email processing
    print("⏳ Waiting for email processing...")
    time.sleep(3)
    
    # Step 5: Test assignment notification
    print("📋 Testing assignment notification...")
    
    # Create staff user first
    staff_data = {
        "email": "test.staff@testdomain.com",
        "password": "StaffTest123!",
        "full_name": "Test Staff Officer",
        "role": "staff"
    }
    
    requests.post(f"{base_url}/auth/register", json=staff_data)
    staff_login = requests.post(f"{base_url}/auth/login", json={
        "email": staff_data["email"],
        "password": staff_data["password"]
    })
    
    if staff_login.status_code == 200:
        staff_id = staff_login.json()["user"]["id"]
        
        # Assign request to staff
        assignment_data = {
            "request_id": request_id,
            "staff_id": staff_id
        }
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        assign_response = requests.post(
            f"{base_url}/requests/{request_id}/assign", 
            json=assignment_data, 
            headers=admin_headers
        )
        
        if assign_response.status_code == 200:
            print(f"✅ Request assigned to staff")
            print(f"📧 Staff notification email should be sent to: {staff_data['email']}")
        else:
            print(f"❌ Failed to assign request: {assign_response.status_code}")
    
    print("=" * 60)
    print("✅ Email notification test completed!")
    print("📧 Check your email inbox at: request@shakerpd.com")
    print("📧 You should have received:")
    print("   - New request notification email")
    print("   - (If assignment worked) Assignment confirmation email")

if __name__ == "__main__":
    test_real_email_notification()