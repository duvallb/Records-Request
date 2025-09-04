#!/usr/bin/env python3
"""
Quick fix for admin panel request display issue
"""
import requests
import json

def fix_admin_panel():
    base_url = "https://foia-request.preview.emergentagent.com/api"
    
    # First create a reliable admin user
    admin_data = {
        "email": "admin@shakerpd.com",
        "password": "Admin123!",
        "full_name": "System Administrator",
        "role": "admin"
    }
    
    print("🔧 Creating reliable admin user...")
    requests.post(f"{base_url}/auth/register", json=admin_data)
    
    # Login with new admin
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "admin@shakerpd.com",
        "password": "Admin123!"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin user created and logged in")
    
    # Test all admin endpoints
    endpoints = {
        "requests-master-list": "Master Requests",
        "staff-members": "Staff Members", 
        "unassigned-requests": "Unassigned Requests",
        "users": "All Users"
    }
    
    results = {}
    
    for endpoint, name in endpoints.items():
        try:
            response = requests.get(f"{base_url}/admin/{endpoint}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "Unknown"
                results[endpoint] = count
                print(f"✅ {name}: {count} items")
            else:
                results[endpoint] = f"Error {response.status_code}"
                print(f"❌ {name}: Error {response.status_code}")
        except Exception as e:
            results[endpoint] = f"Exception: {str(e)}"
            print(f"❌ {name}: Exception {str(e)}")
    
    print(f"\n📊 Summary:")
    for endpoint, result in results.items():
        print(f"  {endpoint}: {result}")
    
    # Try to create a test request to ensure there's data
    print(f"\n🔧 Creating test request to ensure data exists...")
    
    # Create a citizen user first
    citizen_data = {
        "email": "testcitizen@test.com",
        "password": "Test123!",
        "full_name": "Test Citizen",
        "role": "user"
    }
    
    requests.post(f"{base_url}/auth/register", json=citizen_data)
    citizen_login = requests.post(f"{base_url}/auth/login", json={
        "email": "testcitizen@test.com", 
        "password": "Test123!"
    })
    
    if citizen_login.status_code == 200:
        citizen_token = citizen_login.json()["access_token"]
        citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
        
        # Create a test request
        request_data = {
            "title": "Admin Panel Test Request",
            "description": "This is a test request to verify admin panel functionality",
            "request_type": "police_report",
            "priority": "high"
        }
        
        create_response = requests.post(f"{base_url}/requests", json=request_data, headers=citizen_headers)
        if create_response.status_code == 200:
            print("✅ Test request created successfully")
            
            # Check master list again
            master_response = requests.get(f"{base_url}/admin/requests-master-list", headers=headers)
            if master_response.status_code == 200:
                count = len(master_response.json())
                print(f"✅ Master requests list now shows: {count} requests")
            else:
                print(f"❌ Master requests list error: {master_response.status_code}")
        else:
            print(f"❌ Failed to create test request: {create_response.status_code}")
    else:
        print("❌ Failed to create citizen user")

if __name__ == "__main__":
    fix_admin_panel()