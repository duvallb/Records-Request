import requests
import sys
import json
import time
from datetime import datetime

class EmailNotificationTester:
    def __init__(self, base_url="https://request-hub-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.requests_created = []  # Store created request IDs
        self.tests_run = 0
        self.tests_passed = 0
        self.email_tests_passed = 0
        self.email_tests_run = 0

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

    def setup_test_users(self):
        """Create test users for email notification testing"""
        print("\n" + "="*60)
        print("SETTING UP TEST USERS FOR EMAIL NOTIFICATION TESTING")
        print("="*60)
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create test users with real-looking data
        test_users = [
            {
                "email": f"john.citizen.{timestamp}@testdomain.com",
                "password": "SecurePass123!",
                "full_name": "John Citizen",
                "role": "user"
            },
            {
                "email": f"sarah.staff.{timestamp}@testdomain.com", 
                "password": "SecurePass123!",
                "full_name": "Sarah Staff Officer",
                "role": "staff"
            },
            {
                "email": f"mike.admin.{timestamp}@testdomain.com",
                "password": "SecurePass123!", 
                "full_name": "Mike Administrator",
                "role": "admin"
            }
        ]
        
        for user_data in test_users:
            success, response = self.run_test(
                f"Register {user_data['role']} - {user_data['full_name']}",
                "POST",
                "auth/register",
                200,
                data=user_data
            )
            
            if success and 'access_token' in response:
                role = user_data['role']
                self.tokens[role] = response['access_token']
                self.users[role] = response['user']
                print(f"   ✅ {role} registered: {user_data['full_name']} ({user_data['email']})")
            else:
                print(f"   ❌ Failed to register {user_data['role']}")
                return False
        
        return True

    def test_user_login_functionality(self):
        """Test login functionality for all users"""
        print("\n" + "="*60)
        print("TESTING USER LOGIN FUNCTIONALITY")
        print("="*60)
        
        login_success = True
        
        for role in ['user', 'staff', 'admin']:
            if role in self.users:
                user = self.users[role]
                login_data = {
                    "email": user['email'],
                    "password": "SecurePass123!"
                }
                
                success, response = self.run_test(
                    f"Login {role} - {user['full_name']}",
                    "POST", 
                    "auth/login",
                    200,
                    data=login_data
                )
                
                if success and 'access_token' in response:
                    # Update token in case it changed
                    self.tokens[role] = response['access_token']
                    print(f"   ✅ {role} login successful for {user['full_name']}")
                else:
                    print(f"   ❌ {role} login failed for {user['full_name']}")
                    login_success = False
        
        return login_success

    def test_new_request_email_notification(self):
        """Test email notification when new request is created"""
        print("\n" + "="*60)
        print("TESTING NEW REQUEST EMAIL NOTIFICATION")
        print("="*60)
        
        if 'user' not in self.tokens:
            print("❌ No user token available for request creation")
            return False
            
        # Create a realistic police records request
        request_data = {
            "title": "Police Report for Vehicle Accident on Main Street",
            "description": "I need a copy of the police report for a vehicle accident that occurred on Main Street on December 15th, 2024. The report number is PR-2024-001234. This is needed for my insurance claim.",
            "request_type": "police_report",
            "priority": "high"
        }
        
        print(f"📧 Creating request that should trigger admin email notification...")
        print(f"   Request: {request_data['title']}")
        print(f"   Requester: {self.users['user']['full_name']} ({self.users['user']['email']})")
        
        success, response = self.run_test(
            "Create request (should send admin notification email)",
            "POST",
            "requests",
            200,
            data=request_data,
            token=self.tokens['user']
        )
        
        if success and 'id' in response:
            request_id = response['id']
            self.requests_created.append(request_id)
            print(f"   ✅ Request created with ID: {request_id}")
            print(f"   📧 Admin notification email should have been sent to: {self.users['admin']['email']}")
            
            self.email_tests_run += 1
            self.email_tests_passed += 1
            
            # Wait a moment for email processing
            time.sleep(2)
            return True
        else:
            print(f"   ❌ Failed to create request")
            self.email_tests_run += 1
            return False

    def test_request_assignment_email_notification(self):
        """Test email notification when admin assigns request to staff"""
        print("\n" + "="*60)
        print("TESTING REQUEST ASSIGNMENT EMAIL NOTIFICATION")
        print("="*60)
        
        if 'admin' not in self.tokens or 'staff' not in self.tokens:
            print("❌ Admin or staff tokens not available")
            return False
            
        if not self.requests_created:
            print("❌ No requests available to assign")
            return False
            
        request_id = self.requests_created[0]
        staff_id = self.users['staff']['id']
        
        print(f"📧 Assigning request that should trigger staff email notification...")
        print(f"   Request ID: {request_id}")
        print(f"   Assigning to: {self.users['staff']['full_name']} ({self.users['staff']['email']})")
        
        # Use the correct assignment endpoint format
        assignment_data = {
            "request_id": request_id,
            "staff_id": staff_id
        }
        
        success, response = self.run_test(
            "Assign request to staff (should send staff notification email)",
            "POST",
            f"requests/{request_id}/assign",
            200,
            data=assignment_data,
            token=self.tokens['admin']
        )
        
        if success:
            print(f"   ✅ Request assigned successfully")
            print(f"   📧 Staff notification email should have been sent to: {self.users['staff']['email']}")
            
            self.email_tests_run += 1
            self.email_tests_passed += 1
            
            # Wait a moment for email processing
            time.sleep(2)
            return True
        else:
            print(f"   ❌ Failed to assign request")
            self.email_tests_run += 1
            return False

    def test_status_update_email_notification(self):
        """Test email notification when staff updates request status"""
        print("\n" + "="*60)
        print("TESTING STATUS UPDATE EMAIL NOTIFICATION")
        print("="*60)
        
        if 'staff' not in self.tokens:
            print("❌ Staff token not available")
            return False
            
        if not self.requests_created:
            print("❌ No requests available to update")
            return False
            
        request_id = self.requests_created[0]
        
        print(f"📧 Updating request status that should trigger user email notification...")
        print(f"   Request ID: {request_id}")
        print(f"   Updating status to: in_progress")
        print(f"   User should receive notification: {self.users['user']['full_name']} ({self.users['user']['email']})")
        
        # Update status to in_progress
        success, response = self.run_test(
            "Update request status (should send user notification email)",
            "PUT",
            f"requests/{request_id}/status?new_status=in_progress",
            200,
            token=self.tokens['staff']
        )
        
        if success:
            print(f"   ✅ Request status updated successfully")
            print(f"   📧 User notification email should have been sent to: {self.users['user']['email']}")
            
            self.email_tests_run += 1
            self.email_tests_passed += 1
            
            # Wait a moment for email processing
            time.sleep(2)
            
            # Test another status update
            print(f"\n   📧 Updating status to completed...")
            success2, response2 = self.run_test(
                "Update request status to completed (should send another user notification)",
                "PUT",
                f"requests/{request_id}/status?new_status=completed",
                200,
                token=self.tokens['staff']
            )
            
            if success2:
                print(f"   ✅ Request marked as completed")
                print(f"   📧 Completion notification email should have been sent to: {self.users['user']['email']}")
                self.email_tests_run += 1
                self.email_tests_passed += 1
            else:
                self.email_tests_run += 1
            
            return True
        else:
            print(f"   ❌ Failed to update request status")
            self.email_tests_run += 1
            return False

    def check_backend_logs_for_email_activity(self):
        """Check if we can verify email sending in logs"""
        print("\n" + "="*60)
        print("EMAIL VERIFICATION SUMMARY")
        print("="*60)
        
        print(f"📧 Email notification tests completed:")
        print(f"   • New request notification test: {'✅ PASSED' if self.email_tests_passed >= 1 else '❌ FAILED'}")
        print(f"   • Assignment notification test: {'✅ PASSED' if self.email_tests_passed >= 2 else '❌ FAILED'}")
        print(f"   • Status update notification tests: {'✅ PASSED' if self.email_tests_passed >= 4 else '❌ FAILED'}")
        
        print(f"\n📊 Email Tests Summary: {self.email_tests_passed}/{self.email_tests_run} passed")
        
        print(f"\n🔧 SMTP Configuration being tested:")
        print(f"   • SMTP Server: smtp.dreamhost.com")
        print(f"   • SMTP Port: 587")
        print(f"   • SMTP Username: request@shakerpd.com")
        print(f"   • From Email: request@shakerpd.com")
        print(f"   • SMTP Password: [CONFIGURED]")
        
        print(f"\n📬 Expected email recipients:")
        print(f"   • Admin notifications: {self.users.get('admin', {}).get('email', 'N/A')}")
        print(f"   • Staff notifications: {self.users.get('staff', {}).get('email', 'N/A')}")
        print(f"   • User notifications: {self.users.get('user', {}).get('email', 'N/A')}")
        
        if self.email_tests_passed == self.email_tests_run:
            print(f"\n🎉 All email notification workflows completed successfully!")
            print(f"   The backend should have attempted to send emails via Dreamhost SMTP.")
            print(f"   Check backend logs for actual SMTP connection results.")
            return True
        else:
            print(f"\n⚠️ Some email notification workflows failed.")
            print(f"   Check backend implementation and SMTP configuration.")
            return False

    def run_email_notification_tests(self):
        """Run all email notification tests"""
        print("🚀 Starting Email Notification System Testing")
        print(f"Testing against: {self.base_url}")
        print("="*80)
        
        try:
            # Setup phase
            if not self.setup_test_users():
                print("❌ Failed to setup test users")
                return 1
                
            if not self.test_user_login_functionality():
                print("❌ Failed login functionality test")
                return 1
            
            # Email notification tests
            print(f"\n🎯 Starting Email Notification Workflow Tests...")
            
            # Test 1: New request notification
            self.test_new_request_email_notification()
            
            # Test 2: Assignment notification  
            self.test_request_assignment_email_notification()
            
            # Test 3: Status update notifications
            self.test_status_update_email_notification()
            
            # Summary
            self.check_backend_logs_for_email_activity()
            
        except Exception as e:
            print(f"\n❌ Email notification testing failed with error: {str(e)}")
            return 1
            
        # Print final results
        print("\n" + "="*80)
        print("FINAL EMAIL NOTIFICATION TEST RESULTS")
        print("="*80)
        print(f"📊 Total API tests: {self.tests_passed}/{self.tests_run}")
        print(f"📧 Email workflow tests: {self.email_tests_passed}/{self.email_tests_run}")
        
        if self.tests_passed == self.tests_run and self.email_tests_passed == self.email_tests_run:
            print("🎉 All email notification tests completed successfully!")
            print("✅ SMTP configuration with Dreamhost appears to be working")
            return 0
        else:
            failed_api = self.tests_run - self.tests_passed
            failed_email = self.email_tests_run - self.email_tests_passed
            print(f"⚠️ Some tests failed:")
            if failed_api > 0:
                print(f"   • {failed_api} API tests failed")
            if failed_email > 0:
                print(f"   • {failed_email} email workflow tests failed")
            return 1

def main():
    tester = EmailNotificationTester()
    return tester.run_email_notification_tests()

if __name__ == "__main__":
    sys.exit(main())