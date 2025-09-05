import requests
import sys
import json
from datetime import datetime

class PoliceRecordsAPITester:
    def __init__(self, base_url="https://request-hub-6.preview.emergentagent.com/api"):
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
        """Test creating records requests"""
        print("\n" + "="*50)
        print("TESTING REQUEST CREATION")
        print("="*50)
        
        if 'user' not in self.tokens:
            print("❌ No user token available for request creation")
            return
            
        # Test different types of requests
        request_types = [
            {
                "title": "Police Report Request",
                "description": "Need police report for insurance claim",
                "request_type": "police_report",
                "priority": "high"
            },
            {
                "title": "Incident Report Request", 
                "description": "Request for incident report from last week",
                "request_type": "incident_report",
                "priority": "medium"
            },
            {
                "title": "Body Cam Footage Request",
                "description": "Need body cam footage for legal case",
                "request_type": "body_cam_footage", 
                "priority": "high"
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
                print(f"   ✅ Request created with ID: {response['id']}")

    def test_get_requests(self):
        """Test retrieving requests with role-based access"""
        print("\n" + "="*50)
        print("TESTING REQUEST RETRIEVAL")
        print("="*50)
        
        for role in ['user', 'staff', 'admin']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Get requests as {role}",
                    "GET",
                    "requests",
                    200,
                    token=self.tokens[role]
                )
                
                if success:
                    print(f"   ✅ {role} can see {len(response)} requests")

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