#!/usr/bin/env python3
"""
Focused test to verify the specific issues found and test the corrected request status update
"""

import requests
import sys
import json
from datetime import datetime

class FocusedAdminTester:
    def __init__(self, base_url="https://request-hub-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            return success, response.status_code, response_data

        except Exception as e:
            return False, 0, {"error": str(e)}

    def get_admin_token(self):
        """Get admin token for testing"""
        login_data = {
            "email": "request@shakerpd.com",
            "password": "AdminTest123!"
        }
        
        success, status, response = self.make_request("POST", "auth/login", login_data)
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print("✅ Admin login successful")
            return True
        else:
            print(f"❌ Admin login failed: {status} - {response}")
            return False

    def test_request_status_update_corrected(self):
        """Test request status update with correct API format"""
        print("\n" + "="*60)
        print("TESTING REQUEST STATUS UPDATE (CORRECTED)")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        # First create a test request
        test_request_data = {
            "title": f"Status Update Test {datetime.now().strftime('%H%M%S')}",
            "description": "Test request for status update",
            "request_type": "police_report",
            "priority": "medium"
        }
        
        success, status, response = self.make_request(
            "POST", "requests", test_request_data, token=self.admin_token
        )
        
        if success and 'id' in response:
            request_id = response['id']
            print(f"✅ Created test request: {request_id}")
            
            # Now test status update with correct format (using request body, not query param)
            status_update_data = "in_progress"  # Send as JSON string
            
            success, status, response = self.make_request(
                "PUT", f"requests/{request_id}/status", 
                status_update_data, token=self.admin_token
            )
            
            if success:
                print("✅ Request status update successful")
                return True
            else:
                print(f"❌ Request status update failed: {status} - {response}")
                return False
        else:
            print(f"❌ Failed to create test request: {status} - {response}")
            return False

    def test_permission_responses(self):
        """Test that permission responses are appropriate (403 vs 401)"""
        print("\n" + "="*60)
        print("TESTING PERMISSION RESPONSES")
        print("="*60)
        
        # Test admin endpoints without token - should return 401 (unauthorized)
        # But 403 (forbidden) is also acceptable if the system detects missing auth
        admin_endpoints = [
            "admin/users",
            "admin/staff-members", 
            "admin/requests-master-list",
            "admin/email-templates"
        ]
        
        all_blocked = True
        for endpoint in admin_endpoints:
            success, status, response = self.make_request("GET", endpoint)
            
            # Both 401 and 403 are acceptable for unauthorized access
            if status in [401, 403]:
                print(f"✅ {endpoint}: Properly blocked (Status: {status})")
            else:
                print(f"❌ {endpoint}: Not properly blocked (Status: {status})")
                all_blocked = False
        
        return all_blocked

    def verify_master_requests_data_quality(self):
        """Verify the master requests data quality and structure"""
        print("\n" + "="*60)
        print("VERIFYING MASTER REQUESTS DATA QUALITY")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        success, status, response = self.make_request("GET", "admin/requests-master-list", token=self.admin_token)
        
        if success and isinstance(response, list):
            request_count = len(response)
            print(f"✅ Master requests endpoint working: {request_count} requests found")
            
            if request_count > 0:
                # Analyze data quality
                sample_request = response[0]
                required_fields = ['id', 'title', 'status', 'requester_name', 'created_at', 'request_type']
                
                missing_fields = [field for field in required_fields if field not in sample_request]
                
                if not missing_fields:
                    print("✅ Request data structure is complete")
                    
                    # Check for different statuses
                    statuses = set(req.get('status', 'unknown') for req in response[:10])  # Check first 10
                    print(f"✅ Found request statuses: {', '.join(statuses)}")
                    
                    # Check for assigned vs unassigned
                    assigned_count = sum(1 for req in response if req.get('assigned_staff_name'))
                    unassigned_count = request_count - assigned_count
                    print(f"✅ Assignment distribution: {assigned_count} assigned, {unassigned_count} unassigned")
                    
                    return True
                else:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
            else:
                print("⚠️  Master requests list is empty - this could indicate the reported issue")
                return False
        else:
            print(f"❌ Master requests endpoint failed: {status} - {response}")
            return False

    def run_focused_tests(self):
        """Run focused tests on the specific issues"""
        print("🎯 Running Focused Admin Functionality Tests")
        print(f"Testing against: {self.base_url}")
        
        results = []
        
        # Get admin token first
        if not self.get_admin_token():
            print("❌ Cannot proceed without admin token")
            return False
        
        # Test the corrected request status update
        results.append(self.test_request_status_update_corrected())
        
        # Test permission responses (both 401 and 403 are acceptable)
        results.append(self.test_permission_responses())
        
        # Verify master requests data quality
        results.append(self.verify_master_requests_data_quality())
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("\n" + "="*60)
        print("FOCUSED TEST RESULTS")
        print("="*60)
        print(f"📊 Tests passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All focused tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests had issues")
            return False

def main():
    tester = FocusedAdminTester()
    success = tester.run_focused_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())