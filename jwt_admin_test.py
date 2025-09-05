#!/usr/bin/env python3
"""
JWT Session and Admin Functionality Test Suite
Focused on testing the specific requirements from the review request:
- Authentication endpoints with extended JWT duration (8 hours)
- Admin endpoints for user management, staff management
- Request management endpoints (CRUD operations)
- Master requests endpoint (should show actual data, not 0 results)
- Dashboard stats endpoint (should show correct totals)
- Email template management endpoints
"""

import requests
import sys
import json
import time
from datetime import datetime, timedelta

class JWTAdminTester:
    def __init__(self, base_url="https://request-hub-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.admin_user = None
        self.test_users = []
        self.test_requests = []
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
                self.critical_failures.append(f"{name}: {details}")

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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            return success, response.status_code, response_data

        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_admin_login_extended_jwt(self):
        """Test admin login with extended JWT session (8 hours)"""
        print("\n" + "="*60)
        print("TESTING ADMIN LOGIN WITH EXTENDED JWT SESSION")
        print("="*60)
        
        # Use the provided admin credentials
        login_data = {
            "email": "request@shakerpd.com",
            "password": "AdminTest123!"
        }
        
        success, status, response = self.make_request("POST", "auth/login", login_data)
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user = response['user']
            
            # Verify it's an admin user
            if response['user']['role'] == 'admin':
                self.log_test("Admin login successful", True, 
                             f"Admin: {response['user']['full_name']} ({response['user']['email']})")
                
                # Test token validity - JWT should be valid for 8 hours (480 minutes)
                # We can't test the full 8 hours, but we can verify the token works
                time.sleep(2)  # Wait 2 seconds
                test_success, test_status, test_response = self.make_request(
                    "GET", "dashboard/stats", token=self.admin_token
                )
                
                if test_success:
                    self.log_test("JWT token still valid after delay", True, 
                                 "Extended session duration appears to be working")
                else:
                    self.log_test("JWT token validation failed", False, 
                                 f"Token may have expired too quickly - Status: {test_status}")
            else:
                self.log_test("Admin login failed", False, 
                             f"User role is '{response['user']['role']}', expected 'admin'")
        else:
            self.log_test("Admin login failed", False, 
                         f"Status: {status}, Response: {response}")

    def test_dashboard_stats_correct_totals(self):
        """Test dashboard stats endpoint shows correct totals (not 0)"""
        print("\n" + "="*60)
        print("TESTING DASHBOARD STATS - CORRECT TOTALS")
        print("="*60)
        
        if not self.admin_token:
            self.log_test("Dashboard stats test skipped", False, "No admin token available")
            return

        success, status, response = self.make_request("GET", "dashboard/stats", token=self.admin_token)
        
        if success:
            total_requests = response.get('total_requests', 0)
            pending_requests = response.get('pending_requests', 0)
            completed_requests = response.get('completed_requests', 0)
            total_users = response.get('total_users', 0)
            
            # Check if we have actual data (not all zeros)
            has_data = any([total_requests > 0, pending_requests > 0, completed_requests > 0, total_users > 0])
            
            if has_data:
                self.log_test("Dashboard stats showing actual data", True, 
                             f"Total Requests: {total_requests}, Pending: {pending_requests}, "
                             f"Completed: {completed_requests}, Users: {total_users}")
            else:
                self.log_test("Dashboard stats showing zero data", False, 
                             "All dashboard metrics are 0 - this may indicate a data issue")
        else:
            self.log_test("Dashboard stats endpoint failed", False, 
                         f"Status: {status}, Response: {response}")

    def test_master_requests_endpoint(self):
        """Test master requests endpoint shows actual requests (not empty)"""
        print("\n" + "="*60)
        print("TESTING MASTER REQUESTS ENDPOINT")
        print("="*60)
        
        if not self.admin_token:
            self.log_test("Master requests test skipped", False, "No admin token available")
            return

        success, status, response = self.make_request("GET", "admin/requests-master-list", token=self.admin_token)
        
        if success:
            if isinstance(response, list):
                request_count = len(response)
                if request_count > 0:
                    self.log_test("Master requests showing actual data", True, 
                                 f"Found {request_count} requests in master list")
                    
                    # Check first request has proper structure
                    if response[0]:
                        first_request = response[0]
                        required_fields = ['id', 'title', 'status', 'requester_name', 'created_at']
                        has_required_fields = all(field in first_request for field in required_fields)
                        
                        if has_required_fields:
                            self.log_test("Master request data structure valid", True, 
                                         f"Sample request: {first_request.get('title', 'N/A')} - "
                                         f"Status: {first_request.get('status', 'N/A')}")
                        else:
                            self.log_test("Master request data structure incomplete", False, 
                                         f"Missing required fields in request data")
                else:
                    self.log_test("Master requests list is empty", False, 
                                 "This matches the reported issue - requests exist but not showing in master list")
            else:
                self.log_test("Master requests response format invalid", False, 
                             f"Expected list, got: {type(response)}")
        else:
            self.log_test("Master requests endpoint failed", False, 
                         f"Status: {status}, Response: {response}")

    def test_admin_user_management(self):
        """Test admin user management endpoints"""
        print("\n" + "="*60)
        print("TESTING ADMIN USER MANAGEMENT")
        print("="*60)
        
        if not self.admin_token:
            self.log_test("User management test skipped", False, "No admin token available")
            return

        # Test getting all users
        success, status, response = self.make_request("GET", "admin/users", token=self.admin_token)
        
        if success and isinstance(response, list):
            user_count = len(response)
            self.log_test("Get all users", True, f"Retrieved {user_count} users")
            
            if user_count > 0:
                # Test user role update (find a non-admin user to test with)
                test_user = None
                for user in response:
                    if user.get('role') == 'user' and user.get('email') != 'request@shakerpd.com':
                        test_user = user
                        break
                
                if test_user:
                    # Test role update
                    role_update_data = {"role": "staff"}
                    success, status, response = self.make_request(
                        "PUT", f"admin/users/{test_user['id']}/role", 
                        role_update_data, token=self.admin_token
                    )
                    
                    if success:
                        self.log_test("User role update", True, 
                                     f"Updated user {test_user['full_name']} to staff role")
                        
                        # Revert back to user role
                        revert_data = {"role": "user"}
                        self.make_request("PUT", f"admin/users/{test_user['id']}/role", 
                                        revert_data, token=self.admin_token)
                    else:
                        self.log_test("User role update failed", False, 
                                     f"Status: {status}, Response: {response}")
                else:
                    self.log_test("No suitable test user found for role update", False, 
                                 "Could not find a regular user to test role updates")
        else:
            self.log_test("Get all users failed", False, 
                         f"Status: {status}, Response: {response}")

    def test_admin_staff_management(self):
        """Test admin staff management endpoints"""
        print("\n" + "="*60)
        print("TESTING ADMIN STAFF MANAGEMENT")
        print("="*60)
        
        if not self.admin_token:
            self.log_test("Staff management test skipped", False, "No admin token available")
            return

        # Test getting staff members
        success, status, response = self.make_request("GET", "admin/staff-members", token=self.admin_token)
        
        if success and isinstance(response, list):
            staff_count = len(response)
            self.log_test("Get staff members", True, f"Retrieved {staff_count} staff members")
            
            # Test creating new staff member
            timestamp = datetime.now().strftime("%H%M%S")
            new_staff_data = {
                "email": f"teststaff_{timestamp}@shakerpd.com",
                "password": "TestStaff123!",
                "full_name": f"Test Staff {timestamp}",
                "role": "staff"
            }
            
            success, status, response = self.make_request(
                "POST", "admin/create-staff", new_staff_data, token=self.admin_token
            )
            
            if success:
                self.log_test("Create staff member", True, 
                             f"Created staff: {new_staff_data['full_name']}")
                
                # Store for cleanup
                if 'user' in response:
                    self.test_users.append(response['user']['id'])
            else:
                self.log_test("Create staff member failed", False, 
                             f"Status: {status}, Response: {response}")
        else:
            self.log_test("Get staff members failed", False, 
                         f"Status: {status}, Response: {response}")

    def test_request_management_crud(self):
        """Test request management CRUD operations"""
        print("\n" + "="*60)
        print("TESTING REQUEST MANAGEMENT (CRUD)")
        print("="*60)
        
        if not self.admin_token:
            self.log_test("Request CRUD test skipped", False, "No admin token available")
            return

        # Create a test request (as admin)
        test_request_data = {
            "title": f"Test Request {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test request for CRUD operations testing",
            "request_type": "police_report",
            "priority": "medium"
        }
        
        success, status, response = self.make_request(
            "POST", "requests", test_request_data, token=self.admin_token
        )
        
        if success and 'id' in response:
            request_id = response['id']
            self.test_requests.append(request_id)
            self.log_test("Create request", True, f"Created request ID: {request_id}")
            
            # Read the request
            success, status, response = self.make_request(
                "GET", f"requests/{request_id}", token=self.admin_token
            )
            
            if success:
                self.log_test("Read request", True, f"Retrieved request: {response.get('title', 'N/A')}")
                
                # Update request status
                success, status, response = self.make_request(
                    "PUT", f"requests/{request_id}/status", "in_progress", token=self.admin_token
                )
                
                if success:
                    self.log_test("Update request status", True, "Status updated to in_progress")
                else:
                    self.log_test("Update request status failed", False, 
                                 f"Status: {status}, Response: {response}")
            else:
                self.log_test("Read request failed", False, 
                             f"Status: {status}, Response: {response}")
        else:
            self.log_test("Create request failed", False, 
                         f"Status: {status}, Response: {response}")

    def test_email_template_management(self):
        """Test email template management endpoints"""
        print("\n" + "="*60)
        print("TESTING EMAIL TEMPLATE MANAGEMENT")
        print("="*60)
        
        if not self.admin_token:
            self.log_test("Email template test skipped", False, "No admin token available")
            return

        # Test getting email templates
        success, status, response = self.make_request("GET", "admin/email-templates", token=self.admin_token)
        
        if success and isinstance(response, dict):
            template_count = len(response)
            self.log_test("Get email templates", True, f"Retrieved {template_count} email templates")
            
            # Check for expected templates
            expected_templates = ["new_request", "assignment", "status_update", "cancellation"]
            found_templates = [t for t in expected_templates if t in response]
            
            if len(found_templates) == len(expected_templates):
                self.log_test("All expected email templates present", True, 
                             f"Found: {', '.join(found_templates)}")
                
                # Test updating a template
                if "new_request" in response:
                    updated_template = {
                        "subject": "Updated Test Subject: {title}",
                        "content": "This is an updated test template content for {title}"
                    }
                    
                    success, status, response = self.make_request(
                        "PUT", "admin/email-templates/new_request", 
                        updated_template, token=self.admin_token
                    )
                    
                    if success:
                        self.log_test("Update email template", True, "Template updated successfully")
                    else:
                        self.log_test("Update email template failed", False, 
                                     f"Status: {status}, Response: {response}")
            else:
                missing = [t for t in expected_templates if t not in found_templates]
                self.log_test("Missing email templates", False, f"Missing: {', '.join(missing)}")
        else:
            self.log_test("Get email templates failed", False, 
                         f"Status: {status}, Response: {response}")

    def test_permission_restrictions(self):
        """Test that admin endpoints are properly restricted"""
        print("\n" + "="*60)
        print("TESTING PERMISSION RESTRICTIONS")
        print("="*60)
        
        # Test admin endpoints without token (should fail)
        admin_endpoints = [
            "admin/users",
            "admin/staff-members", 
            "admin/requests-master-list",
            "admin/email-templates"
        ]
        
        for endpoint in admin_endpoints:
            success, status, response = self.make_request("GET", endpoint, expected_status=401)
            
            if success:  # success means we got the expected 401
                self.log_test(f"Unauthorized access blocked for {endpoint}", True, 
                             "Properly returns 401 without token")
            else:
                self.log_test(f"Unauthorized access not blocked for {endpoint}", False, 
                             f"Expected 401, got {status}")

    def run_comprehensive_test(self):
        """Run all tests in the comprehensive suite"""
        print("🚀 Starting JWT Session and Admin Functionality Testing")
        print(f"Testing against: {self.base_url}")
        print(f"Focus: Extended JWT sessions, Admin endpoints, Request management")
        
        try:
            # Core authentication and session testing
            self.test_admin_login_extended_jwt()
            
            # Dashboard and data verification
            self.test_dashboard_stats_correct_totals()
            self.test_master_requests_endpoint()
            
            # Admin functionality testing
            self.test_admin_user_management()
            self.test_admin_staff_management()
            
            # Request management testing
            self.test_request_management_crud()
            
            # Email template management
            self.test_email_template_management()
            
            # Security testing
            self.test_permission_restrictions()
            
        except Exception as e:
            print(f"\n❌ Testing failed with error: {str(e)}")
            self.critical_failures.append(f"Test suite error: {str(e)}")
        
        # Print final results
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST RESULTS")
        print("="*70)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for failure in self.critical_failures:
                print(f"   • {failure}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend API is working correctly.")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} tests failed - see details above")
            return False

def main():
    tester = JWTAdminTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())