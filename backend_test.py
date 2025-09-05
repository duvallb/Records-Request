import requests
import sys
import json
from datetime import datetime

class PoliceRecordsAPITester:
    def __init__(self, base_url="https://pd-requests.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.requests_created = []  # Store created request IDs
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_user_registration(self):
        """Test user registration for different roles"""
        print("\n" + "="*50)
        print("TESTING USER REGISTRATION")
        print("="*50)
        
        # Test cases for different roles
        test_users = [
            {
                "email": f"citizen_{datetime.now().strftime('%H%M%S')}@test.com",
                "password": "TestPass123!",
                "full_name": "Test Citizen",
                "role": "user"
            },
            {
                "email": f"staff_{datetime.now().strftime('%H%M%S')}@test.com", 
                "password": "TestPass123!",
                "full_name": "Test Staff",
                "role": "staff"
            },
            {
                "email": f"admin_{datetime.now().strftime('%H%M%S')}@test.com",
                "password": "TestPass123!", 
                "full_name": "Test Admin",
                "role": "admin"
            }
        ]
        
        for user_data in test_users:
            success, response = self.run_test(
                f"Register {user_data['role']}",
                "POST",
                "auth/register",
                200,
                data=user_data
            )
            
            if success and 'access_token' in response:
                role = user_data['role']
                self.tokens[role] = response['access_token']
                self.users[role] = response['user']
                print(f"   ✅ {role} registered successfully with token")
            else:
                print(f"   ❌ Failed to register {user_data['role']}")

    def test_user_login(self):
        """Test login functionality"""
        print("\n" + "="*50)
        print("TESTING USER LOGIN")
        print("="*50)
        
        # Test login for each registered user
        for role in ['user', 'staff', 'admin']:
            if role in self.users:
                user = self.users[role]
                login_data = {
                    "email": user['email'],
                    "password": "TestPass123!"
                }
                
                success, response = self.run_test(
                    f"Login {role}",
                    "POST", 
                    "auth/login",
                    200,
                    data=login_data
                )
                
                if success and 'access_token' in response:
                    print(f"   ✅ {role} login successful")
                else:
                    print(f"   ❌ {role} login failed")

        # Test invalid login
        self.run_test(
            "Invalid login",
            "POST",
            "auth/login", 
            401,
            data={"email": "invalid@test.com", "password": "wrongpass"}
        )

    def test_dashboard_stats(self):
        """Test dashboard statistics for different roles"""
        print("\n" + "="*50)
        print("TESTING DASHBOARD STATISTICS")
        print("="*50)
        
        for role in ['user', 'staff', 'admin']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Dashboard stats for {role}",
                    "GET",
                    "dashboard/stats",
                    200,
                    token=self.tokens[role]
                )
                
                if success:
                    print(f"   ✅ {role} dashboard stats: {response}")

    def test_create_requests(self):
        """Test creating records requests with enhanced fields"""
        print("\n" + "="*50)
        print("TESTING REQUEST CREATION WITH ENHANCED FIELDS")
        print("="*50)
        
        if 'user' not in self.tokens:
            print("❌ No user token available for request creation")
            return
            
        # Test request with all enhanced fields
        enhanced_request = {
            "title": "Traffic Incident Police Report",
            "description": "Need police report for traffic incident involving multiple vehicles",
            "request_type": "police_report",
            "priority": "high",
            # Enhanced fields being tested
            "incident_date": "2024-01-15",
            "incident_time": "14:30",
            "incident_location": "123 Main Street, Shaker Heights, OH",
            "case_number": "PD-2024-001234",
            "officer_names": "Officer Smith, Officer Johnson",
            "vehicle_info": "Blue Honda Civic (License: ABC123), Red Ford F150 (License: XYZ789)",
            "additional_details": "Two-vehicle collision at intersection. No injuries reported. Both vehicles towed.",
            "contact_phone": "(216) 555-0123"
        }
        
        success, response = self.run_test(
            "Create request with enhanced fields",
            "POST",
            "requests",
            200,
            data=enhanced_request,
            token=self.tokens['user']
        )
        
        if success and 'id' in response:
            self.requests_created.append(response['id'])
            print(f"   ✅ Enhanced request created with ID: {response['id']}")
            
            # Verify enhanced fields are stored
            self.verify_enhanced_fields(response['id'], enhanced_request)
        else:
            print("   ❌ Failed to create enhanced request")
            
        # Test basic request without enhanced fields
        basic_request = {
            "title": "Basic Incident Report",
            "description": "Simple incident report request",
            "request_type": "incident_report",
            "priority": "medium"
        }
        
        success, response = self.run_test(
            "Create basic request",
            "POST",
            "requests",
            200,
            data=basic_request,
            token=self.tokens['user']
        )
        
        if success and 'id' in response:
            self.requests_created.append(response['id'])
            print(f"   ✅ Basic request created with ID: {response['id']}")

    def verify_enhanced_fields(self, request_id, original_data):
        """Verify that enhanced fields are properly stored and retrieved"""
        print(f"\n🔍 Verifying enhanced fields for request {request_id}...")
        
        success, response = self.run_test(
            "Get request with enhanced fields",
            "GET",
            f"requests/{request_id}",
            200,
            token=self.tokens['user']
        )
        
        if success:
            enhanced_fields = [
                'incident_date', 'incident_time', 'incident_location', 
                'case_number', 'officer_names', 'vehicle_info', 
                'additional_details', 'contact_phone'
            ]
            
            all_fields_present = True
            for field in enhanced_fields:
                if field in original_data:
                    if response.get(field) == original_data[field]:
                        print(f"   ✅ {field}: {response.get(field)}")
                    else:
                        print(f"   ❌ {field}: Expected '{original_data[field]}', got '{response.get(field)}'")
                        all_fields_present = False
                        
            if all_fields_present:
                print("   ✅ All enhanced fields verified successfully")
            else:
                print("   ❌ Some enhanced fields missing or incorrect")
        else:
            print("   ❌ Failed to retrieve request for verification")

    def test_get_requests(self):
        """Test retrieving requests with role-based access and filtering"""
        print("\n" + "="*50)
        print("TESTING REQUEST RETRIEVAL WITH ROLE-BASED FILTERING")
        print("="*50)
        
        # Test user access - should only see their own requests
        if 'user' in self.tokens:
            success, response = self.run_test(
                "Get requests as user (should see own requests only)",
                "GET",
                "requests",
                200,
                token=self.tokens['user']
            )
            
            if success:
                user_id = self.users['user']['id']
                user_requests = [req for req in response if req.get('user_id') == user_id]
                print(f"   ✅ User can see {len(response)} requests (all should be their own)")
                
                # Verify all requests belong to the user
                if all(req.get('user_id') == user_id for req in response):
                    print("   ✅ User filtering working correctly - only sees own requests")
                else:
                    print("   ❌ User filtering failed - seeing other users' requests")
        
        # Test staff access - should see assigned and unassigned requests
        if 'staff' in self.tokens:
            success, response = self.run_test(
                "Get requests as staff (should see assigned + unassigned)",
                "GET",
                "requests",
                200,
                token=self.tokens['staff']
            )
            
            if success:
                staff_id = self.users['staff']['id']
                assigned_to_staff = [req for req in response if req.get('assigned_staff_id') == staff_id]
                unassigned = [req for req in response if req.get('assigned_staff_id') is None]
                print(f"   ✅ Staff can see {len(response)} requests")
                print(f"   - Assigned to staff: {len(assigned_to_staff)}")
                print(f"   - Unassigned: {len(unassigned)}")
        
        # Test admin access - should see all requests
        if 'admin' in self.tokens:
            success, response = self.run_test(
                "Get requests as admin (should see all requests)",
                "GET",
                "requests",
                200,
                token=self.tokens['admin']
            )
            
            if success:
                print(f"   ✅ Admin can see {len(response)} requests (all requests)")
                
                # Verify enhanced fields are included in response
                if response and len(response) > 0:
                    first_request = response[0]
                    enhanced_fields = ['incident_date', 'incident_location', 'case_number', 'officer_names']
                    fields_present = [field for field in enhanced_fields if field in first_request]
                    print(f"   ✅ Enhanced fields present in response: {fields_present}")

    def test_get_specific_request(self):
        """Test getting specific request details"""
        print("\n" + "="*50)
        print("TESTING SPECIFIC REQUEST RETRIEVAL")
        print("="*50)
        
        if not self.requests_created:
            print("❌ No requests created to test")
            return
            
        request_id = self.requests_created[0]
        
        # Test access by different roles
        for role in ['user', 'staff', 'admin']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Get request {request_id} as {role}",
                    "GET",
                    f"requests/{request_id}",
                    200,
                    token=self.tokens[role]
                )

    def test_messaging_system(self):
        """Test messaging system"""
        print("\n" + "="*50)
        print("TESTING MESSAGING SYSTEM")
        print("="*50)
        
        if not self.requests_created:
            print("❌ No requests created to test messaging")
            return
            
        request_id = self.requests_created[0]
        
        # Test creating messages
        message_data = {
            "request_id": request_id,
            "content": "This is a test message from user"
        }
        
        success, response = self.run_test(
            "Create message",
            "POST",
            "messages",
            200,
            data=message_data,
            token=self.tokens['user']
        )
        
        # Test retrieving messages
        if success:
            self.run_test(
                "Get messages",
                "GET",
                f"messages/{request_id}",
                200,
                token=self.tokens['user']
            )

    def test_notifications(self):
        """Test notification system"""
        print("\n" + "="*50)
        print("TESTING NOTIFICATION SYSTEM")
        print("="*50)
        
        for role in ['user', 'staff', 'admin']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Get notifications for {role}",
                    "GET",
                    "notifications",
                    200,
                    token=self.tokens[role]
                )
                
                if success:
                    print(f"   ✅ {role} has {len(response)} notifications")

    def test_email_notification_system(self):
        """Test email notification system and SMTP configuration"""
        print("\n" + "="*50)
        print("TESTING EMAIL NOTIFICATION SYSTEM")
        print("="*50)
        
        # Test 1: Verify SMTP configuration by checking environment
        print("🔍 Testing SMTP Configuration...")
        
        # We can't directly test SMTP config, but we can test if emails are triggered
        # by creating a request and checking if the system processes it without errors
        
        if 'user' not in self.tokens:
            print("❌ No user token available for email testing")
            return
            
        # Create a request that should trigger email notifications
        email_test_request = {
            "title": "Email Notification Test Request",
            "description": "This request is created to test email notifications",
            "request_type": "police_report",
            "priority": "high",
            "incident_date": "2024-01-20",
            "incident_location": "456 Test Street, Shaker Heights, OH",
            "case_number": "EMAIL-TEST-001",
            "officer_names": "Officer Test",
            "contact_phone": "(216) 555-EMAIL"
        }
        
        success, response = self.run_test(
            "Create request to trigger email notification",
            "POST",
            "requests",
            200,
            data=email_test_request,
            token=self.tokens['user']
        )
        
        if success and 'id' in response:
            print("   ✅ Request created successfully - email notification should be triggered")
            self.requests_created.append(response['id'])
            
            # Test admin email template functionality if admin token exists
            if 'admin' in self.tokens:
                self.test_admin_email_templates()
        else:
            print("   ❌ Failed to create request for email testing")

    def test_admin_email_templates(self):
        """Test admin email template management"""
        print("\n🔍 Testing Admin Email Template Management...")
        
        if 'admin' not in self.tokens:
            print("❌ No admin token available for email template testing")
            return
            
        # Test getting email templates
        success, response = self.run_test(
            "Get email templates",
            "GET",
            "admin/email-templates",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Retrieved {len(response)} email templates")
            
        # Test creating a new email template
        new_template = {
            "name": "Test Template",
            "template_type": "new_request",
            "subject": "Test Subject: {{title}}",
            "content": "Test email content for {{requester_name}} - Request: {{title}}",
            "html_content": "<h1>Test HTML Content</h1><p>Request: {{title}}</p>"
        }
        
        success, response = self.run_test(
            "Create email template",
            "POST",
            "admin/email-templates",
            200,
            data=new_template,
            token=self.tokens['admin']
        )
        
        if success:
            print("   ✅ Email template created successfully")

    def test_admin_functions(self):
        """Test admin-specific functions"""
        print("\n" + "="*50)
        print("TESTING ADMIN FUNCTIONS")
        print("="*50)
        
        if 'admin' not in self.tokens or 'staff' not in self.tokens:
            print("❌ Admin or staff tokens not available")
            return
            
        if not self.requests_created:
            print("❌ No requests to assign")
            return
            
        # Test request assignment
        request_id = self.requests_created[0]
        staff_id = self.users['staff']['id']
        
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
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Request assigned successfully")
            
        # Test getting staff members
        success, response = self.run_test(
            "Get staff members",
            "GET",
            "admin/staff-members",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Retrieved {len(response)} staff members")
            
        # Test getting unassigned requests
        success, response = self.run_test(
            "Get unassigned requests",
            "GET",
            "admin/unassigned-requests",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Retrieved {len(response)} unassigned requests")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Police Records API Testing")
        print(f"Testing against: {self.base_url}")
        
        try:
            self.test_user_registration()
            self.test_user_login()
            self.test_dashboard_stats()
            self.test_create_requests()
            self.test_get_requests()
            self.test_get_specific_request()
            self.test_email_notification_system()
            self.test_messaging_system()
            self.test_notifications()
            self.test_admin_functions()
            
        except Exception as e:
            print(f"\n❌ Testing failed with error: {str(e)}")
            
        # Print final results
        print("\n" + "="*60)
        print("FINAL TEST RESULTS")
        print("="*60)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = PoliceRecordsAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())