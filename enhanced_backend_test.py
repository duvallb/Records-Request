import requests
import sys
import json
import io
from datetime import datetime

class EnhancedPoliceRecordsAPITester:
    def __init__(self, base_url="https://request-hub-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.requests_created = []  # Store created request IDs
        self.file_ids = []  # Store uploaded file IDs
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {}
        
        if token:
            test_headers['Authorization'] = f'Bearer {token}'
        if headers:
            test_headers.update(headers)
        
        # Don't set Content-Type for file uploads
        if not files and 'Content-Type' not in test_headers:
            test_headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=test_headers)
                else:
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
                    return True, response.content if method == 'GET' and 'download' in endpoint else {}
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

    def test_file_upload_system(self):
        """Test file upload and download functionality"""
        print("\n" + "="*50)
        print("TESTING FILE UPLOAD & DOWNLOAD SYSTEM")
        print("="*50)
        
        if not self.requests_created:
            print("❌ No requests created to test file upload")
            return
            
        request_id = self.requests_created[0]
        
        # Create a test file
        test_file_content = b"This is a test file for police records request"
        test_file = io.BytesIO(test_file_content)
        
        # Test file upload
        files = {'file': ('test_document.txt', test_file, 'text/plain')}
        
        success, response = self.run_test(
            "Upload file to request",
            "POST",
            f"upload/{request_id}",
            200,
            files=files,
            token=self.tokens['user']
        )
        
        if success and 'file_id' in response:
            file_id = response['file_id']
            self.file_ids.append(file_id)
            print(f"   ✅ File uploaded with ID: {file_id}")
            
            # Test getting files for request
            success, files_response = self.run_test(
                "Get request files",
                "GET",
                f"files/{request_id}",
                200,
                token=self.tokens['user']
            )
            
            if success:
                print(f"   ✅ Retrieved {len(files_response)} files for request")
                
                # Test file download
                if files_response:
                    file_to_download = files_response[0]['id']
                    success, download_response = self.run_test(
                        "Download file",
                        "GET",
                        f"download/{file_to_download}",
                        200,
                        token=self.tokens['user']
                    )
                    
                    if success:
                        print(f"   ✅ File downloaded successfully")

    def test_analytics_dashboard(self):
        """Test analytics dashboard (admin only)"""
        print("\n" + "="*50)
        print("TESTING ANALYTICS DASHBOARD")
        print("="*50)
        
        if 'admin' not in self.tokens:
            print("❌ No admin token available for analytics testing")
            return
            
        # Test analytics access for admin
        success, response = self.run_test(
            "Get analytics dashboard (admin)",
            "GET",
            "analytics/dashboard",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Analytics data retrieved successfully")
            print(f"   📊 Total requests: {response.get('total_requests', 0)}")
            print(f"   📊 Requests by status: {response.get('requests_by_status', {})}")
            print(f"   📊 Average resolution time: {response.get('average_resolution_time', 0):.2f} hours")
        
        # Test analytics access denied for non-admin users
        for role in ['user', 'staff']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Get analytics dashboard ({role}) - should fail",
                    "GET",
                    "analytics/dashboard",
                    403,
                    token=self.tokens[role]
                )

    def test_export_functionality(self):
        """Test PDF and CSV export functionality"""
        print("\n" + "="*50)
        print("TESTING EXPORT FUNCTIONALITY")
        print("="*50)
        
        if not self.requests_created:
            print("❌ No requests created to test export")
            return
            
        request_id = self.requests_created[0]
        
        # Test PDF export for individual request
        success, pdf_response = self.run_test(
            "Export request as PDF",
            "GET",
            f"export/request/{request_id}/pdf",
            200,
            token=self.tokens['user']
        )
        
        if success:
            print(f"   ✅ PDF export successful")
        
        # Test CSV export for all requests (admin only)
        if 'admin' in self.tokens:
            success, csv_response = self.run_test(
                "Export all requests as CSV (admin)",
                "GET",
                "export/requests/csv",
                200,
                token=self.tokens['admin']
            )
            
            if success:
                print(f"   ✅ CSV export successful")
        
        # Test CSV export access denied for non-admin
        for role in ['user', 'staff']:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Export CSV ({role}) - should fail",
                    "GET",
                    "export/requests/csv",
                    403,
                    token=self.tokens[role]
                )

    def test_enhanced_request_management(self):
        """Test enhanced request management features"""
        print("\n" + "="*50)
        print("TESTING ENHANCED REQUEST MANAGEMENT")
        print("="*50)
        
        if not self.requests_created or 'admin' not in self.tokens or 'staff' not in self.tokens:
            print("❌ Missing requirements for request management testing")
            return
            
        request_id = self.requests_created[0]
        staff_id = self.users['staff']['id']
        
        # Test request assignment
        success, response = self.run_test(
            "Assign request to staff",
            "PUT",
            f"requests/{request_id}/assign?staff_id={staff_id}",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Request assigned to staff successfully")
            
            # Test status update by staff
            success, response = self.run_test(
                "Update request status (staff)",
                "PUT",
                f"requests/{request_id}/status?new_status=in_progress",
                200,
                token=self.tokens['staff']
            )
            
            if success:
                print(f"   ✅ Request status updated successfully")

    def test_messaging_system(self):
        """Test enhanced messaging system"""
        print("\n" + "="*50)
        print("TESTING ENHANCED MESSAGING SYSTEM")
        print("="*50)
        
        if not self.requests_created:
            print("❌ No requests created to test messaging")
            return
            
        request_id = self.requests_created[0]
        
        # Test creating messages from different roles
        message_tests = [
            ("user", "This is a message from the citizen"),
            ("staff", "This is a response from staff"),
            ("admin", "This is an admin message")
        ]
        
        for role, content in message_tests:
            if role in self.tokens:
                message_data = {
                    "request_id": request_id,
                    "content": content
                }
                
                success, response = self.run_test(
                    f"Create message ({role})",
                    "POST",
                    "messages",
                    200,
                    data=message_data,
                    token=self.tokens[role]
                )
        
        # Test retrieving messages
        success, messages = self.run_test(
            "Get all messages for request",
            "GET",
            f"messages/{request_id}",
            200,
            token=self.tokens['user']
        )
        
        if success:
            print(f"   ✅ Retrieved {len(messages)} messages")

    def test_notification_system(self):
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
                    
                    # Test marking notification as read if any exist
                    if response and len(response) > 0:
                        notification_id = response[0]['id']
                        success, mark_response = self.run_test(
                            f"Mark notification as read ({role})",
                            "PUT",
                            f"notifications/{notification_id}/read",
                            200,
                            token=self.tokens[role]
                        )

    def test_dashboard_stats(self):
        """Test enhanced dashboard statistics"""
        print("\n" + "="*50)
        print("TESTING ENHANCED DASHBOARD STATISTICS")
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

    def run_all_tests(self):
        """Run all enhanced tests in sequence"""
        print("🚀 Starting Enhanced Police Records API Testing")
        print(f"Testing against: {self.base_url}")
        
        try:
            # Core functionality tests
            self.test_user_registration()
            self.test_create_requests()
            
            # Enhanced feature tests
            self.test_file_upload_system()
            self.test_analytics_dashboard()
            self.test_export_functionality()
            self.test_enhanced_request_management()
            self.test_messaging_system()
            self.test_notification_system()
            self.test_dashboard_stats()
            
        except Exception as e:
            print(f"\n❌ Testing failed with error: {str(e)}")
            
        # Print final results
        print("\n" + "="*60)
        print("ENHANCED API TEST RESULTS")
        print("="*60)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All enhanced tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = EnhancedPoliceRecordsAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())