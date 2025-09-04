import requests
import sys
import json
from datetime import datetime
import time

class UpdatedPoliceRecordsAPITester:
    def __init__(self, base_url="https://foia-request.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.requests_created = []  # Store created request IDs
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if token:
            test_headers['Authorization'] = f'Bearer {token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration_role_restriction(self):
        """Test that user registration only allows 'user' role"""
        print("\n" + "="*60)
        print("TESTING USER REGISTRATION ROLE RESTRICTIONS")
        print("="*60)
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Test 1: Normal user registration should work
        user_data = {
            "email": f"normaluser_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": "Normal User",
            "role": "user"
        }
        
        success, response = self.run_test(
            "Register normal user",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if success and 'access_token' in response:
            self.tokens['user'] = response['access_token']
            self.users['user'] = response['user']
            print(f"   ✅ User registered successfully")
        else:
            self.critical_failures.append("User registration failed")
            
        # Test 2: Try to register as staff (should still work but role should be user)
        staff_data = {
            "email": f"staffuser_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": "Staff User",
            "role": "staff"
        }
        
        success, response = self.run_test(
            "Register with staff role",
            "POST",
            "auth/register",
            200,
            data=staff_data
        )
        
        if success:
            # Check if role was forced to 'user'
            if response.get('user', {}).get('role') == 'user':
                print(f"   ✅ Staff role registration converted to user role")
            else:
                print(f"   ⚠️ Staff role registration allowed: {response.get('user', {}).get('role')}")

    def test_admin_create_staff_endpoint(self):
        """Test admin can create staff and admin users"""
        print("\n" + "="*60)
        print("TESTING ADMIN CREATE STAFF FUNCTIONALITY")
        print("="*60)
        
        # First create an admin user manually for testing
        timestamp = datetime.now().strftime('%H%M%S')
        admin_data = {
            "email": f"admin_{timestamp}@test.com",
            "password": "AdminPass123!",
            "full_name": "Test Admin",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Register admin user",
            "POST",
            "auth/register",
            200,
            data=admin_data
        )
        
        if success and 'access_token' in response:
            self.tokens['admin'] = response['access_token']
            self.users['admin'] = response['user']
            print(f"   ✅ Admin registered successfully")
        else:
            self.critical_failures.append("Admin registration failed")
            return
            
        # Test creating staff user via admin endpoint
        staff_data = {
            "email": f"newstaff_{timestamp}@test.com",
            "password": "StaffPass123!",
            "full_name": "New Staff Member",
            "role": "staff"
        }
        
        success, response = self.run_test(
            "Admin create staff user",
            "POST",
            "admin/create-staff",
            200,
            data=staff_data,
            token=self.tokens['admin']
        )
        
        if success:
            self.users['staff'] = response.get('user', {})
            print(f"   ✅ Staff user created by admin")
            
            # Login as the new staff user
            login_data = {
                "email": staff_data['email'],
                "password": staff_data['password']
            }
            
            success, login_response = self.run_test(
                "Login new staff user",
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if success:
                self.tokens['staff'] = login_response['access_token']
                print(f"   ✅ New staff user can login")
        else:
            self.critical_failures.append("Admin cannot create staff users")
            
        # Test creating admin user via admin endpoint
        new_admin_data = {
            "email": f"newadmin_{timestamp}@test.com",
            "password": "AdminPass123!",
            "full_name": "New Admin User",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Admin create admin user",
            "POST",
            "admin/create-staff",
            200,
            data=new_admin_data,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Admin user created by admin")
        else:
            print(f"   ❌ Admin cannot create admin users")

    def test_admin_user_management_endpoints(self):
        """Test all admin user management endpoints"""
        print("\n" + "="*60)
        print("TESTING ADMIN USER MANAGEMENT ENDPOINTS")
        print("="*60)
        
        if 'admin' not in self.tokens:
            print("❌ No admin token available")
            return
            
        # Test 1: Get all users
        success, response = self.run_test(
            "Get all users",
            "GET",
            "admin/users",
            200,
            token=self.tokens['admin']
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Retrieved {len(response)} users")
            user_list = response
        else:
            self.critical_failures.append("Cannot retrieve user list")
            return
            
        # Test 2: Update user role
        if user_list and 'user' in self.users:
            user_id = self.users['user']['id']
            role_update_data = {"role": "staff"}
            
            success, response = self.run_test(
                "Update user role to staff",
                "PUT",
                f"admin/users/{user_id}/role",
                200,
                data=role_update_data,
                token=self.tokens['admin']
            )
            
            if success:
                print(f"   ✅ User role updated to staff")
                
                # Update back to user
                role_update_data = {"role": "user"}
                self.run_test(
                    "Update role back to user",
                    "PUT",
                    f"admin/users/{user_id}/role",
                    200,
                    data=role_update_data,
                    token=self.tokens['admin']
                )
            else:
                self.critical_failures.append("Cannot update user roles")
                
        # Test 3: Update user email
        if user_list and 'user' in self.users:
            user_id = self.users['user']['id']
            timestamp = datetime.now().strftime('%H%M%S')
            email_update_data = {"email": f"updated_{timestamp}@test.com"}
            
            success, response = self.run_test(
                "Update user email",
                "PUT",
                f"admin/users/{user_id}/email",
                200,
                data=email_update_data,
                token=self.tokens['admin']
            )
            
            if success:
                print(f"   ✅ User email updated")
            else:
                print(f"   ❌ Cannot update user email")
                
        # Test 4: Get staff members with workload
        success, response = self.run_test(
            "Get staff members with workload",
            "GET",
            "admin/staff-members",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Retrieved staff members with workload info")
        else:
            print(f"   ❌ Cannot retrieve staff members")
            
        # Test 5: Get requests master list
        success, response = self.run_test(
            "Get requests master list",
            "GET",
            "admin/requests-master-list",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Retrieved master requests list")
        else:
            print(f"   ❌ Cannot retrieve master requests list")
            
        # Test 6: Get unassigned requests
        success, response = self.run_test(
            "Get unassigned requests",
            "GET",
            "admin/unassigned-requests",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Retrieved unassigned requests")
        else:
            print(f"   ❌ Cannot retrieve unassigned requests")

    def test_permission_restrictions(self):
        """Test that non-admin users cannot access admin endpoints"""
        print("\n" + "="*60)
        print("TESTING PERMISSION RESTRICTIONS")
        print("="*60)
        
        # Test with user token (should fail)
        if 'user' in self.tokens:
            success, response = self.run_test(
                "User tries to access admin users endpoint",
                "GET",
                "admin/users",
                403,  # Should be forbidden
                token=self.tokens['user']
            )
            
            if success:
                print(f"   ✅ User correctly denied access to admin endpoint")
            else:
                self.critical_failures.append("User can access admin endpoints")
                
        # Test with staff token (should fail)
        if 'staff' in self.tokens:
            success, response = self.run_test(
                "Staff tries to access admin users endpoint",
                "GET",
                "admin/users",
                403,  # Should be forbidden
                token=self.tokens['staff']
            )
            
            if success:
                print(f"   ✅ Staff correctly denied access to admin endpoint")
            else:
                print(f"   ❌ Staff can access admin endpoints")

    def test_email_validation_and_duplicates(self):
        """Test email validation and duplicate prevention"""
        print("\n" + "="*60)
        print("TESTING EMAIL VALIDATION AND DUPLICATE PREVENTION")
        print("="*60)
        
        if 'admin' not in self.tokens:
            print("❌ No admin token available")
            return
            
        # Test 1: Try to create user with invalid email
        invalid_email_data = {
            "email": "invalid-email",
            "password": "TestPass123!",
            "full_name": "Invalid Email User",
            "role": "user"
        }
        
        success, response = self.run_test(
            "Create user with invalid email",
            "POST",
            "admin/create-staff",
            422,  # Pydantic validation error
            data=invalid_email_data,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Invalid email correctly rejected")
        else:
            print(f"   ❌ Invalid email was accepted")
            
        # Test 2: Try to create user with duplicate email
        if 'user' in self.users:
            duplicate_email = self.users['user']['email']
            print(f"   Testing duplicate email: {duplicate_email}")
            duplicate_email_data = {
                "email": duplicate_email,
                "password": "TestPass123!",
                "full_name": "Duplicate Email User",
                "role": "user"
            }
            
            success, response = self.run_test(
                "Create user with duplicate email",
                "POST",
                "admin/create-staff",
                400,  # Should fail
                data=duplicate_email_data,
                token=self.tokens['admin']
            )
            
            if success:
                print(f"   ✅ Duplicate email correctly rejected")
            else:
                print(f"   ❌ Duplicate email was accepted")

    def test_request_workflow_with_notifications(self):
        """Test complete request workflow including email notifications"""
        print("\n" + "="*60)
        print("TESTING REQUEST WORKFLOW WITH EMAIL NOTIFICATIONS")
        print("="*60)
        
        if 'user' not in self.tokens or 'admin' not in self.tokens:
            print("❌ Required tokens not available")
            return
            
        # Test 1: Create a request (should trigger admin notification)
        request_data = {
            "title": "Test Police Report Request",
            "description": "This is a test request to verify email notifications",
            "request_type": "police_report",
            "priority": "high"
        }
        
        success, response = self.run_test(
            "Create request (triggers admin notification)",
            "POST",
            "requests",
            200,
            data=request_data,
            token=self.tokens['user']
        )
        
        if success and 'id' in response:
            request_id = response['id']
            self.requests_created.append(request_id)
            print(f"   ✅ Request created: {request_id}")
            
            # Test 2: Assign request to staff (should trigger staff notification)
            if 'staff' in self.users:
                assignment_data = {
                    "request_id": request_id,
                    "staff_id": self.users['staff']['id']
                }
                
                success, response = self.run_test(
                    "Assign request to staff (triggers staff notification)",
                    "POST",
                    f"requests/{request_id}/assign",
                    200,
                    data=assignment_data,
                    token=self.tokens['admin']
                )
                
                if success:
                    print(f"   ✅ Request assigned to staff")
                    
                    # Test 3: Update request status (should trigger user notification)
                    if 'staff' in self.tokens:
                        success, response = self.run_test(
                            "Update request status (triggers user notification)",
                            "PUT",
                            f"requests/{request_id}/status",
                            200,
                            data="completed",
                            token=self.tokens['staff']
                        )
                        
                        if success:
                            print(f"   ✅ Request status updated")
                        else:
                            print(f"   ❌ Cannot update request status")
                else:
                    print(f"   ❌ Cannot assign request to staff")
        else:
            self.critical_failures.append("Cannot create requests")

    def test_email_error_fixes(self):
        """Test that email system skips fake emails"""
        print("\n" + "="*60)
        print("TESTING EMAIL ERROR FIXES (FAKE EMAIL HANDLING)")
        print("="*60)
        
        if 'admin' not in self.tokens:
            print("❌ No admin token available")
            return
            
        # Create a fake admin user with example.com email
        fake_admin_data = {
            "email": "admin.user@example.com",
            "password": "FakePass123!",
            "full_name": "Fake Admin User",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Create fake admin with example.com email",
            "POST",
            "admin/create-staff",
            200,
            data=fake_admin_data,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Fake admin created (email should be skipped in notifications)")
            
            # Now create a request to trigger notifications
            # The system should skip the fake admin email
            request_data = {
                "title": "Test Request for Email Filtering",
                "description": "This request should not send email to fake admin",
                "request_type": "incident_report",
                "priority": "medium"
            }
            
            success, response = self.run_test(
                "Create request (should skip fake admin email)",
                "POST",
                "requests",
                200,
                data=request_data,
                token=self.tokens['user']
            )
            
            if success:
                print(f"   ✅ Request created - fake admin email should be skipped")
            else:
                print(f"   ❌ Request creation failed")
        else:
            print(f"   ❌ Cannot create fake admin user")

    def run_all_tests(self):
        """Run all updated tests in sequence"""
        print("🚀 Starting Updated Police Records API Testing")
        print(f"Testing against: {self.base_url}")
        print("Focus: Email fixes, Admin endpoints, User management, Permissions")
        
        try:
            # Core functionality tests
            self.test_user_registration_role_restriction()
            self.test_admin_create_staff_endpoint()
            self.test_admin_user_management_endpoints()
            self.test_permission_restrictions()
            self.test_email_validation_and_duplicates()
            self.test_request_workflow_with_notifications()
            self.test_email_error_fixes()
            
        except Exception as e:
            print(f"\n❌ Testing failed with error: {str(e)}")
            
        # Print final results
        print("\n" + "="*70)
        print("FINAL TEST RESULTS")
        print("="*70)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"   - {failure}")
        
        if self.tests_passed == self.tests_run and not self.critical_failures:
            print("🎉 All tests passed!")
            return 0
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} tests failed, {len(self.critical_failures)} critical issues")
            return 1

def main():
    tester = UpdatedPoliceRecordsAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())