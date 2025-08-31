import asyncio
import aiosmtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@police.gov")

async def test_smtp_connection():
    """Test SMTP connection and email sending"""
    print("🔧 Testing SMTP Connection to Dreamhost")
    print("="*50)
    print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"Username: {SMTP_USERNAME}")
    print(f"From Email: {FROM_EMAIL}")
    
    try:
        # Create test email
        message = EmailMessage()
        message["From"] = FROM_EMAIL
        message["To"] = "test@example.com"  # Test email address
        message["Subject"] = "SMTP Connection Test - Police Records System"
        message.set_content("""
This is a test email to verify SMTP configuration for the Police Records Request System.

SMTP Configuration:
- Server: smtp.dreamhost.com
- Port: 587
- Username: request@shakerpd.com

If you receive this email, the SMTP configuration is working correctly.

Test performed at: """ + str(asyncio.get_event_loop().time()))
        
        print(f"\n📧 Attempting to send test email...")
        print(f"   To: test@example.com")
        print(f"   Subject: {message['Subject']}")
        
        # Attempt to send email
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD
        )
        
        print("✅ SMTP connection successful!")
        print("✅ Test email sent successfully!")
        print("🎉 Dreamhost SMTP configuration is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Provide specific error guidance
        if "authentication" in str(e).lower():
            print("   💡 This appears to be an authentication error.")
            print("   💡 Check SMTP username and password credentials.")
        elif "connection" in str(e).lower() or "timeout" in str(e).lower():
            print("   💡 This appears to be a connection error.")
            print("   💡 Check SMTP server and port settings.")
        elif "tls" in str(e).lower() or "ssl" in str(e).lower():
            print("   💡 This appears to be a TLS/SSL error.")
            print("   💡 Check TLS settings and port configuration.")
        
        return False

async def main():
    print("🚀 SMTP Connection Test for Police Records System")
    print("Testing Dreamhost SMTP Configuration")
    print("="*60)
    
    success = await test_smtp_connection()
    
    print("\n" + "="*60)
    if success:
        print("🎉 SMTP TEST RESULT: SUCCESS")
        print("✅ Email notifications should work correctly in the application")
    else:
        print("❌ SMTP TEST RESULT: FAILED")
        print("⚠️  Email notifications will not work until SMTP issues are resolved")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)