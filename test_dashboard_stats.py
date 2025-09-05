#!/usr/bin/env python3
"""
Test dashboard stats endpoint and fix data display issues
"""
import requests

def test_dashboard_stats():
    base_url = "https://foia-request.preview.emergentagent.com/api"
    
    # Login as admin
    admin_login = {
        "email": "request@shakerpd.com",
        "password": "AdminTest123!"
    }
    
    print("🔍 Testing Dashboard Stats...")
    
    login_response = requests.post(f"{base_url}/auth/login", json=admin_login)
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test dashboard stats
    stats_response = requests.get(f"{base_url}/dashboard/stats", headers=headers)
    print(f"Dashboard stats status: {stats_response.status_code}")
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print("📊 Dashboard Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Stats failed: {stats_response.text}")
    
    # Test requests endpoint
    requests_response = requests.get(f"{base_url}/requests", headers=headers)
    if requests_response.status_code == 200:
        requests_data = requests_response.json()
        print(f"📋 Direct requests count: {len(requests_data)}")
        if requests_data:
            print(f"   Sample request: {requests_data[0].get('title', 'No title')}")
    else:
        print(f"❌ Requests failed: {requests_response.text}")
    
    # Test users endpoint
    users_response = requests.get(f"{base_url}/admin/users", headers=headers)
    if users_response.status_code == 200:
        users_data = users_response.json()
        print(f"👥 Direct users count: {len(users_data)}")
        role_counts = {}
        for user in users_data:
            role = user.get('role', 'unknown')
            role_counts[role] = role_counts.get(role, 0) + 1
        print(f"   Role breakdown: {role_counts}")
    else:
        print(f"❌ Users failed: {users_response.text}")

if __name__ == "__main__":
    test_dashboard_stats()