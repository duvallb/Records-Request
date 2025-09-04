#!/usr/bin/env python3
"""
Test the admin requests master list endpoint directly
"""
import requests
import json

def test_admin_requests_endpoint():
    base_url = "https://foia-request.preview.emergentagent.com/api"
    
    # Login as admin
    admin_login = {
        "email": "request@shakerpd.com",
        "password": "AdminTest123!"
    }
    
    print("🔐 Logging in as admin...")
    login_response = requests.post(f"{base_url}/auth/login", json=admin_login)
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Admin login successful")
    
    # Test the master requests endpoint
    print("\n🔍 Testing /admin/requests-master-list endpoint...")
    
    master_response = requests.get(f"{base_url}/admin/requests-master-list", headers=headers)
    
    print(f"Status Code: {master_response.status_code}")
    
    if master_response.status_code == 200:
        data = master_response.json()
        print(f"✅ Success! Found {len(data)} requests")
        
        if len(data) > 0:
            print(f"\n📋 Sample request:")
            sample = data[0]
            print(f"  ID: {sample.get('id', 'N/A')}")
            print(f"  Title: {sample.get('title', 'N/A')}")
            print(f"  Status: {sample.get('status', 'N/A')}")
            print(f"  Requester: {sample.get('requester_name', 'N/A')}")
            print(f"  Created: {sample.get('created_at', 'N/A')}")
        else:
            print("📭 No requests found in database")
    else:
        print(f"❌ Failed: {master_response.status_code}")
        print(f"Response: {master_response.text}")
    
    # Also test other admin endpoints for comparison
    print(f"\n🔍 Testing other admin endpoints...")
    
    endpoints = [
        "admin/staff-members",
        "admin/unassigned-requests", 
        "admin/users"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{base_url}/{endpoint}", headers=headers)
        print(f"{endpoint}: {response.status_code} - {len(response.json()) if response.status_code == 200 else 'ERROR'} items")

if __name__ == "__main__":
    test_admin_requests_endpoint()