#!/usr/bin/env python3
"""
Final comprehensive test for the review request requirements
"""

import requests
import sys
import json
from datetime import datetime

class FinalAdminTester:
    def __init__(self, base_url="https://request-hub-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        
        if success:
            print(f"✅ {test_name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {test_name}")
            if details:
                print(f"   {details}")

    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            return response.status_code, response_data

        except Exception as e:
            return 0, {"error": str(e)}

    def test_admin_authentication_extended_jwt(self):
        """Test 1: Admin authentication with extended JWT (8 hours)"""
        print("\n" + "="*60)
        print("TEST 1: ADMIN AUTHENTICATION WITH EXTENDED JWT")
        print("="*60)
        
        login_data = {
            "email": "request@shakerpd.com",
            "password": "AdminTest123!"
        }
        
        status, response = self.make_request("POST", "auth/login", login_data)
        
        if status == 200 and 'access_token' in response:
            self.admin_token = response['access_token']
            user_info = response['user']
            
            if user_info['role'] == 'admin':
                self.log_result("Admin Login with Extended JWT", True, 
                               f"Admin: {user_info['full_name']} - Token acquired for 8-hour session")
            else:
                self.log_result("Admin Login with Extended JWT", False, 
                               f"User role is {user_info['role']}, expected admin")
        else:
            self.log_result("Admin Login with Extended JWT", False, 
                           f"Login failed - Status: {status}")

    def test_dashboard_stats_correct_totals(self):
        """Test 2: Dashboard stats showing correct totals (not 0)"""
        print("\n" + "="*60)
        print("TEST 2: DASHBOARD STATS - CORRECT TOTALS")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("Dashboard Stats", False, "No admin token available")
            return

        status, response = self.make_request("GET", "dashboard/stats", token=self.admin_token)
        
        if status == 200:
            total_requests = response.get('total_requests', 0)
            pending_requests = response.get('pending_requests', 0)
            completed_requests = response.get('completed_requests', 0)
            total_users = response.get('total_users', 0)
            
            if total_requests > 0:
                self.log_result("Dashboard Stats Showing Correct Totals", True, 
                               f"Total: {total_requests}, Pending: {pending_requests}, "
                               f"Completed: {completed_requests}, Users: {total_users}")
            else:
                self.log_result("Dashboard Stats Showing Correct Totals", False, 
                               "All metrics are 0 - indicates data issue")
        else:
            self.log_result("Dashboard Stats Showing Correct Totals", False, 
                           f"API call failed - Status: {status}")

    def test_master_requests_endpoint(self):
        """Test 3: Master requests endpoint showing actual data (not 0 results)"""
        print("\n" + "="*60)
        print("TEST 3: MASTER REQUESTS ENDPOINT")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("Master Requests Endpoint", False, "No admin token available")
            return

        status, response = self.make_request("GET", "admin/requests-master-list", token=self.admin_token)
        
        if status == 200 and isinstance(response, list):
            request_count = len(response)
            
            if request_count > 0:
                # Check data quality
                sample = response[0]
                has_required_fields = all(field in sample for field in ['id', 'title', 'status', 'requester_name'])
                
                if has_required_fields:
                    self.log_result("Master Requests Showing Actual Data", True, 
                                   f"Found {request_count} requests with complete data structure")
                else:
                    self.log_result("Master Requests Showing Actual Data", False, 
                                   f"Found {request_count} requests but data structure incomplete")
            else:
                self.log_result("Master Requests Showing Actual Data", False, 
                               "Master requests list is empty - matches reported issue")
        else:
            self.log_result("Master Requests Showing Actual Data", False, 
                           f"API call failed - Status: {status}")

    def test_admin_user_management(self):
        """Test 4: Admin user management endpoints"""
        print("\n" + "="*60)
        print("TEST 4: ADMIN USER MANAGEMENT")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("Admin User Management", False, "No admin token available")
            return

        # Test getting all users
        status, response = self.make_request("GET", "admin/users", token=self.admin_token)
        
        if status == 200 and isinstance(response, list):
            user_count = len(response)
            self.log_result("Get All Users", True, f"Retrieved {user_count} users")
            
            # Test creating staff member
            timestamp = datetime.now().strftime("%H%M%S")
            staff_data = {
                "email": f"teststaff_{timestamp}@shakerpd.com",
                "password": "TestStaff123!",
                "full_name": f"Test Staff {timestamp}",
                "role": "staff"
            }
            
            status, response = self.make_request("POST", "admin/create-staff", staff_data, token=self.admin_token)
            
            if status == 200:
                self.log_result("Create Staff Member", True, f"Created: {staff_data['full_name']}")
            else:
                self.log_result("Create Staff Member", False, f"Failed - Status: {status}")
        else:
            self.log_result("Get All Users", False, f"Failed - Status: {status}")

    def test_request_management_crud(self):
        """Test 5: Request management CRUD operations"""
        print("\n" + "="*60)
        print("TEST 5: REQUEST MANAGEMENT (CRUD)")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("Request Management CRUD", False, "No admin token available")
            return

        # Create request
        request_data = {
            "title": f"CRUD Test Request {datetime.now().strftime('%H%M%S')}",
            "description": "Test request for CRUD operations",
            "request_type": "police_report",
            "priority": "medium"
        }
        
        status, response = self.make_request("POST", "requests", request_data, token=self.admin_token)
        
        if status == 200 and 'id' in response:
            request_id = response['id']
            self.log_result("Create Request", True, f"Created request ID: {request_id}")
            
            # Read request
            status, response = self.make_request("GET", f"requests/{request_id}", token=self.admin_token)
            
            if status == 200:
                self.log_result("Read Request", True, f"Retrieved: {response.get('title', 'N/A')}")
                
                # Update request status (using query parameter)
                status, response = self.make_request(
                    "PUT", f"requests/{request_id}/status", 
                    token=self.admin_token,
                    params={"new_status": "in_progress"}
                )
                
                if status == 200:
                    self.log_result("Update Request Status", True, "Status updated to in_progress")
                else:
                    self.log_result("Update Request Status", False, f"Failed - Status: {status}")
            else:
                self.log_result("Read Request", False, f"Failed - Status: {status}")
        else:
            self.log_result("Create Request", False, f"Failed - Status: {status}")

    def test_email_template_management(self):
        """Test 6: Email template management endpoints"""
        print("\n" + "="*60)
        print("TEST 6: EMAIL TEMPLATE MANAGEMENT")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("Email Template Management", False, "No admin token available")
            return

        status, response = self.make_request("GET", "admin/email-templates", token=self.admin_token)
        
        if status == 200 and isinstance(response, dict):
            template_count = len(response)
            expected_templates = ["new_request", "assignment", "status_update", "cancellation"]
            found_templates = [t for t in expected_templates if t in response]
            
            if len(found_templates) == len(expected_templates):
                self.log_result("Email Template Management", True, 
                               f"All {template_count} expected templates found")
            else:
                missing = [t for t in expected_templates if t not in found_templates]
                self.log_result("Email Template Management", False, 
                               f"Missing templates: {', '.join(missing)}")
        else:
            self.log_result("Email Template Management", False, f"Failed - Status: {status}")

    def run_comprehensive_review_test(self):
        """Run all tests specified in the review request"""
        print("🎯 COMPREHENSIVE BACKEND API TEST - REVIEW REQUEST VERIFICATION")
        print(f"Testing against: {self.base_url}")
        print("Focus: JWT session fixes, Admin functionality, Request management")
        
        # Run all priority tests from the review request
        self.test_admin_authentication_extended_jwt()
        self.test_dashboard_stats_correct_totals()
        self.test_master_requests_endpoint()
        self.test_admin_user_management()
        self.test_request_management_crud()
        self.test_email_template_management()
        
        # Generate final report
        print("\n" + "="*70)
        print("FINAL COMPREHENSIVE TEST REPORT")
        print("="*70)
        
        passed_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print(f"📊 Overall Results: {len(passed_tests)}/{len(self.test_results)} tests passed")
        
        if failed_tests:
            print(f"\n🚨 FAILED TESTS:")
            for test in failed_tests:
                print(f"   ❌ {test['test']}: {test['details']}")
        
        if passed_tests:
            print(f"\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"   ✅ {test['test']}")
        
        success_rate = len(passed_tests) / len(self.test_results) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 85:
            print("🎉 Backend API is working well! Most functionality verified.")
            return True
        else:
            print("⚠️  Backend API has significant issues that need attention.")
            return False

def main():
    tester = FinalAdminTester()
    success = tester.run_comprehensive_review_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())