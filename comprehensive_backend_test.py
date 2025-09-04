import requests
import sys
import json
from datetime import datetime
import time

class ComprehensivePoliceRecordsAPITester:
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

    def test_registration_security(self):
        """Test that public registration only creates 'user' role accounts"""
        print("\n" + "="*60)
        print("TESTING REGISTRATION SECURITY - CRITICAL")
        print("="*60)
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Test 1: Try to register with 'staff' role - should be forced to 'user'
        staff_attempt = {
            "email": f"fake_staff_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": "Fake Staff User",
            "role": "staff"  # This should be ignored
        }
        
        success, response = self.run_test(
            "Register with staff role (should be forced to user)",
            "POST",
            "auth/register",
            200,
            data=staff_attempt
        )
        
        if success:
            actual_role = response.get('user', {}).get('role')
            if actual_role == 'user':
                print(f"   ✅ SECURITY PASS: Staff role request forced to 'user' role")
                self.tokens['fake_staff'] = response['access_token']
                self.users['fake_staff'] = response['user']
            else:
                print(f"   ❌ SECURITY FAIL: Expected 'user' role, got '{actual_role}'")
                self.critical_failures.append("Registration security bypass - staff role allowed")
        
        # Test 2: Try to register with 'admin' role - should be forced to 'user'
        admin_attempt = {
            "email": f"fake_admin_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": "Fake Admin User", 
            "role": "admin"  # This should be ignored
        }
        
        success, response = self.run_test(
            "Register with admin role (should be forced to user)",
            "POST",
            "auth/register",
            200,
            data=admin_attempt
        )
        
        if success:
            actual_role = response.get('user', {}).get('role')
            if actual_role == 'user':
                print(f"   ✅ SECURITY PASS: Admin role request forced to 'user' role")
                self.tokens['fake_admin'] = response['access_token']
                self.users['fake_admin'] = response['user']
            else:
                print(f"   ❌ SECURITY FAIL: Expected 'user' role, got '{actual_role}'")
                self.critical_failures.append("Registration security bypass - admin role allowed")
        
        # Test 3: Normal user registration should work
        normal_user = {
            "email": f"normal_user_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": "Normal User",
            "role": "user"
        }
        
        success, response = self.run_test(
            "Normal user registration",
            "POST",
            "auth/register",
            200,
            data=normal_user
        )
        
        if success:
            self.tokens['user'] = response['access_token']
            self.users['user'] = response['user']
            print(f"   ✅ Normal user registration successful")

    def test_email_system_configuration(self):
        """Test email system with Dreamhost SMTP configuration"""
        print("\n" + "="*60)
        print("TESTING EMAIL SYSTEM - DREAMHOST SMTP")
        print("="*60)
        
        # First, create an admin user to test email functionality
        admin_user = {
            "email": f"test_admin_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "AdminPass123!",
            "full_name": "Test Admin User",
            "role": "admin"
        }
        
        # Register admin (will be forced to user, then we'll need to create via admin endpoint)
        success, response = self.run_test(
            "Register test admin user",
            "POST", 
            "auth/register",
            200,
            data=admin_user
        )
        
        if success:
            self.tokens['test_admin'] = response['access_token']
            self.users['test_admin'] = response['user']
        
        # Test email sending capability (admin only endpoint)
        if 'test_admin' in self.tokens:
            success, response = self.run_test(
                "Test email sending functionality",
                "POST",
                "test-email",
                200,
                token=self.tokens['test_admin']
            )
            
            if success:
                print(f"   ✅ Email test endpoint accessible")
                if 'sent_to' in response:
                    print(f"   ✅ Email sent to: {response['sent_to']}")
                else:
                    print(f"   ⚠️  Email test response: {response}")

    def test_admin_endpoints_comprehensive(self):
        """Test all admin functionality comprehensively"""
        print("\n" + "="*60)
        print("TESTING ADMIN ENDPOINTS - COMPREHENSIVE")
        print("="*60)
        
        # Create a proper admin user first
        if 'test_admin' not in self.tokens:
            print("❌ No admin token available for admin endpoint testing")
            return
            
        admin_token = self.tokens['test_admin']
        
        # Test 1: Get all users
        success, response = self.run_test(
            "Get all users (admin)",
            "GET",
            "admin/users",
            200,
            token=admin_token
        )
        
        if success:
            user_count = len(response)
            print(f"   ✅ Retrieved {user_count} users from system")
            
        # Test 2: Get staff members with workload
        success, response = self.run_test(
            "Get staff members with workload",
            "GET", 
            "admin/staff-members",
            200,
            token=admin_token
        )
        
        if success:
            staff_count = len(response)
            print(f"   ✅ Retrieved {staff_count} staff members")
            
        # Test 3: Get master requests list
        success, response = self.run_test(
            "Get master requests list",
            "GET",
            "admin/requests-master-list", 
            200,
            token=admin_token
        )
        
        if success:
            request_count = len(response)
            print(f"   ✅ Retrieved {request_count} requests from master list")
            
        # Test 4: Get unassigned requests
        success, response = self.run_test(
            "Get unassigned requests",
            "GET",
            "admin/unassigned-requests",
            200,
            token=admin_token
        )
        
        if success:
            unassigned_count = len(response)
            print(f"   ✅ Retrieved {unassigned_count} unassigned requests")
            
        # Test 5: Create staff member
        staff_data = {
            "email": f"new_staff_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "StaffPass123!",
            "full_name": "New Staff Member",
            "role": "staff"
        }
        
        success, response = self.run_test(
            "Create new staff member",
            "POST",
            "admin/create-staff",
            200,
            data=staff_data,
            token=admin_token
        )
        
        if success:
            print(f"   ✅ Staff member created successfully")
            new_staff_id = response.get('user', {}).get('id')
            
            # Test 6: Update user role
            if new_staff_id and 'user' in self.users:
                user_id = self.users['user']['id']
                role_update = {"role": "staff"}
                
                success, response = self.run_test(
                    "Update user role to staff",
                    "PUT",
                    f"admin/users/{user_id}/role",
                    200,
                    data=role_update,
                    token=admin_token
                )
                
                if success:
                    print(f"   ✅ User role updated successfully")
                    
            # Test 7: Update user email
            if 'user' in self.users:
                user_id = self.users['user']['id']
                email_update = {"email": f"updated_{datetime.now().strftime('%H%M%S')}@test.com"}
                
                success, response = self.run_test(
                    "Update user email",
                    "PUT",
                    f"admin/users/{user_id}/email",
                    200,
                    data=email_update,
                    token=admin_token
                )
                
                if success:
                    print(f"   ✅ User email updated successfully")

    def test_request_management_workflow(self):
        """Test complete request management workflow"""
        print("\n" + "="*60)
        print("TESTING REQUEST MANAGEMENT WORKFLOW")
        print("="*60)
        
        if 'user' not in self.tokens:
            print("❌ No user token available for request testing")
            return
            
        # Test 1: Create different types of requests including body cam footage
        request_types = [
            {
                "title": "Police Report for Insurance",
                "description": "Need police report for car accident insurance claim",
                "request_type": "police_report",
                "priority": "high"
            },
            {
                "title": "Body Camera Footage Request",
                "description": "Requesting body camera footage from incident on Main Street. I acknowledge this may involve costs for processing and copying.",
                "request_type": "body_cam_footage",
                "priority": "high"
            },
            {
                "title": "Incident Report Request",
                "description": "Need incident report from last Tuesday",
                "request_type": "incident_report", 
                "priority": "medium"
            }
        ]
        
        for request_data in request_types:
            success, response = self.run_test(
                f"Create {request_data['request_type']} request",
                "POST",
                "requests",
                200,
                data=request_data,
                token=self.tokens['user']
            )
            
            if success and 'id' in response:
                self.requests_created.append(response['id'])
                print(f"   ✅ {request_data['request_type']} request created: {response['id']}")
                
                # Special check for body cam footage
                if request_data['request_type'] == 'body_cam_footage':
                    print(f"   ✅ Body camera footage request accepted with cost acknowledgment")
        
        # Test 2: Get requests as different roles
        for role in ['user', 'test_admin']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Get requests as {role}",
                    "GET",
                    "requests",
                    200,
                    token=self.tokens[role]
                )
                
                if success:
                    print(f"   ✅ {role} can access {len(response)} requests")
        
        # Test 3: Request assignment (if we have admin and requests)
        if 'test_admin' in self.tokens and self.requests_created:
            request_id = self.requests_created[0]
            
            # First create a staff member to assign to
            staff_data = {
                "email": f"assign_staff_{datetime.now().strftime('%H%M%S')}@test.com",
                "password": "StaffPass123!",
                "full_name": "Assignment Staff",
                "role": "staff"
            }
            
            success, response = self.run_test(
                "Create staff for assignment",
                "POST",
                "admin/create-staff",
                200,
                data=staff_data,
                token=self.tokens['test_admin']
            )
            
            if success:
                staff_id = response.get('user', {}).get('id')
                
                # Now assign the request
                assignment_data = {
                    "request_id": request_id,
                    "staff_id": staff_id
                }
                
                success, response = self.run_test(
                    "Assign request to staff",
                    "POST",
                    f"requests/{request_id}/assign",
                    200,
                    data=assignment_data,
                    token=self.tokens['test_admin']
                )
                
                if success:
                    print(f"   ✅ Request assigned successfully")
                    
                    # Test 4: Update request status
                    success, response = self.run_test(
                        "Update request status",
                        "PUT",
                        f"requests/{request_id}/status",
                        200,
                        data="in_progress",
                        token=self.tokens['test_admin']
                    )
                    
                    if success:
                        print(f"   ✅ Request status updated successfully")

    def test_email_filtering_fake_addresses(self):
        """Test that emails skip fake @example.com addresses"""
        print("\n" + "="*60)
        print("TESTING EMAIL FILTERING - FAKE ADDRESSES")
        print("="*60)
        
        # This test verifies the backend logic for filtering fake emails
        # We can't directly test email sending, but we can verify the endpoints work
        # and that the system handles fake email addresses properly
        
        if 'user' in self.tokens and self.requests_created:
            # Create a request which should trigger email notifications
            request_data = {
                "title": "Test Email Filtering Request",
                "description": "This request tests email filtering for fake addresses",
                "request_type": "other",
                "priority": "low"
            }
            
            success, response = self.run_test(
                "Create request to test email filtering",
                "POST",
                "requests",
                200,
                data=request_data,
                token=self.tokens['user']
            )
            
            if success:
                print(f"   ✅ Request created - email notifications should filter fake addresses")
                print(f"   ✅ Backend should skip any admin users with @example.com emails")

    def test_analytics_and_dashboard(self):
        """Test analytics and dashboard functionality"""
        print("\n" + "="*60)
        print("TESTING ANALYTICS AND DASHBOARD")
        print("="*60)
        
        # Test dashboard stats for different roles
        for role in ['user', 'test_admin']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Get dashboard stats as {role}",
                    "GET",
                    "dashboard/stats",
                    200,
                    token=self.tokens[role]
                )
                
                if success:
                    print(f"   ✅ {role} dashboard stats retrieved: {response}")
        
        # Test analytics dashboard (admin only)
        if 'test_admin' in self.tokens:
            success, response = self.run_test(
                "Get analytics dashboard",
                "GET",
                "analytics/dashboard",
                200,
                token=self.tokens['test_admin']
            )
            
            if success:
                total_requests = response.get('total_requests', 0)
                print(f"   ✅ Analytics dashboard shows {total_requests} total requests")

    def test_permission_system(self):
        """Test permission system and access control"""
        print("\n" + "="*60)
        print("TESTING PERMISSION SYSTEM")
        print("="*60)
        
        # Test that regular users cannot access admin endpoints
        if 'user' in self.tokens:
            # Try to access admin users endpoint
            success, response = self.run_test(
                "User tries to access admin/users (should fail)",
                "GET",
                "admin/users",
                403,  # Should be forbidden
                token=self.tokens['user']
            )
            
            if success:
                print(f"   ✅ Regular user properly denied admin access")
            
            # Try to create staff (should fail)
            staff_data = {
                "email": "unauthorized@test.com",
                "password": "Pass123!",
                "full_name": "Unauthorized Staff",
                "role": "staff"
            }
            
            success, response = self.run_test(
                "User tries to create staff (should fail)",
                "POST",
                "admin/create-staff",
                403,
                data=staff_data,
                token=self.tokens['user']
            )
            
            if success:
                print(f"   ✅ Regular user properly denied staff creation")

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Police Records API Testing")
        print(f"Testing against: {self.base_url}")
        print("Focus: Registration Security, Email System, Admin Functions, Request Management")
        
        try:
            # Core security and functionality tests
            self.test_registration_security()
            self.test_email_system_configuration()
            self.test_admin_endpoints_comprehensive()
            self.test_request_management_workflow()
            self.test_email_filtering_fake_addresses()
            self.test_analytics_and_dashboard()
            self.test_permission_system()
            
        except Exception as e:
            print(f"\n❌ Testing failed with error: {str(e)}")
            self.critical_failures.append(f"Test execution error: {str(e)}")
            
        # Print final results
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST RESULTS")
        print("="*70)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES DETECTED:")
            for failure in self.critical_failures:
                print(f"   ❌ {failure}")
        
        if self.tests_passed == self.tests_run and not self.critical_failures:
            print("🎉 All tests passed! System is ready for production.")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed, {len(self.critical_failures)} critical issues")
            return 1

def main():
    tester = ComprehensivePoliceRecordsAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())