#!/usr/bin/env python3
"""
Check current state of the application after rollback
"""
import requests
import json

def check_current_state():
    base_url = "https://request-hub-6.preview.emergentagent.com/api"
    
    print("🔍 CHECKING CURRENT APPLICATION STATE AFTER ROLLBACK")
    print("=" * 60)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{base_url.replace('/api', '')}")
        print(f"✅ Frontend accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend not accessible: {str(e)}")
    
    # Test admin login
    admin_credentials = [
        {"email": "request@shakerpd.com", "password": "AdminTest123!"},
        {"email": "admin@shakerpd.com", "password": "Admin123!"},
    ]
    
    admin_token = None
    for creds in admin_credentials:
        try:
            login_response = requests.post(f"{base_url}/auth/login", json=creds)
            if login_response.status_code == 200:
                admin_token = login_response.json()["access_token"]
                print(f"✅ Admin login successful: {creds['email']}")
                break
            else:
                print(f"❌ Admin login failed for {creds['email']}: {login_response.status_code}")
        except Exception as e:
            print(f"❌ Admin login error for {creds['email']}: {str(e)}")
    
    if not admin_token:
        print("❌ CRITICAL: No admin access available")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test admin endpoints
    admin_endpoints = {
        "admin/users": "User Management",
        "admin/staff-members": "Staff Management", 
        "admin/requests-master-list": "Master Requests",
        "admin/unassigned-requests": "Unassigned Requests"
    }
    
    print(f"\n🔧 TESTING ADMIN ENDPOINTS:")
    missing_endpoints = []
    
    for endpoint, name in admin_endpoints.items():
        try:
            response = requests.get(f"{base_url}/{endpoint}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "Unknown"
                print(f"✅ {name}: {count} items")
            else:
                print(f"❌ {name}: Error {response.status_code}")
                missing_endpoints.append(endpoint)
        except Exception as e:
            print(f"❌ {name}: Exception {str(e)}")
            missing_endpoints.append(endpoint)
    
    # Test user creation capabilities
    print(f"\n👥 TESTING USER MANAGEMENT:")
    try:
        users_response = requests.get(f"{base_url}/admin/users", headers=headers)
        if users_response.status_code == 200:
            users = users_response.json()
            print(f"✅ Can access user list: {len(users)} users")
            
            # Test role update capability
            if users:
                test_user = users[0]
                role_update = {"role": test_user["role"]}  # Same role to avoid changes
                role_response = requests.put(f"{base_url}/admin/users/{test_user['id']}/role", 
                                           json=role_update, headers=headers)
                if role_response.status_code == 200:
                    print("✅ User role management working")
                else:
                    print(f"❌ User role management failed: {role_response.status_code}")
        else:
            print(f"❌ Cannot access user management: {users_response.status_code}")
    except Exception as e:
        print(f"❌ User management error: {str(e)}")
    
    # Test registration security
    print(f"\n🔐 TESTING REGISTRATION SECURITY:")
    try:
        # Try to register as staff (should fail or be blocked)
        staff_attempt = {
            "email": "test@test.com",
            "password": "Test123!",
            "full_name": "Test User",
            "role": "staff"
        }
        reg_response = requests.post(f"{base_url}/auth/register", json=staff_attempt)
        if reg_response.status_code == 200:
            user_data = reg_response.json()
            actual_role = user_data.get("user", {}).get("role", "unknown")
            if actual_role == "user":
                print("✅ Registration security working - staff role converted to user")
            else:
                print(f"❌ Registration security issue - role is {actual_role}")
        else:
            print(f"⚠️ Registration test failed: {reg_response.status_code}")
    except Exception as e:
        print(f"❌ Registration security test error: {str(e)}")
    
    # Test email configuration
    print(f"\n📧 TESTING EMAIL CONFIGURATION:")
    try:
        with open('/app/backend/.env', 'r') as f:
            env_content = f.read()
        
        checks = [
            "SMTP_SERVER=\"smtp.dreamhost.com\"" in env_content or "SMTP_SERVER=smtp.dreamhost.com" in env_content,
            "SMTP_USERNAME=\"request@shakerpd.com\"" in env_content or "SMTP_USERNAME=request@shakerpd.com" in env_content,
            "SMTP_PASSWORD=\"Acac!a38\"" in env_content or "SMTP_PASSWORD=Acac!a38" in env_content,
        ]
        
        if all(checks):
            print("✅ Email configuration present")
        else:
            print("❌ Email configuration missing or incorrect")
            print(f"   SMTP_SERVER check: {'✓' if checks[0] else '✗'}")
            print(f"   SMTP_USERNAME check: {'✓' if checks[1] else '✗'}")
            print(f"   SMTP_PASSWORD check: {'✓' if checks[2] else '✗'}")
            
    except Exception as e:
        print(f"❌ Email configuration check error: {str(e)}")
    
    # Summary
    print(f"\n📋 SUMMARY:")
    if missing_endpoints:
        print(f"❌ Missing endpoints: {', '.join(missing_endpoints)}")
    else:
        print("✅ All admin endpoints working")
        
    print(f"\nℹ️ If everything shows as working, the rollback may have only")
    print(f"   affected the deployed version, not the development code.")

if __name__ == "__main__":
    check_current_state()