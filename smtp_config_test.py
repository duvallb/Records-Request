import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

print("🔧 SMTP Configuration Check:")
print("="*50)

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@police.gov")

print(f"SMTP_SERVER: {SMTP_SERVER}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SMTP_USERNAME: {SMTP_USERNAME}")
print(f"SMTP_PASSWORD: {'[CONFIGURED]' if SMTP_PASSWORD else '[EMPTY]'}")
print(f"FROM_EMAIL: {FROM_EMAIL}")

print(f"\nCondition check:")
print(f"not SMTP_USERNAME: {not SMTP_USERNAME}")
print(f"not SMTP_PASSWORD: {not SMTP_PASSWORD}")
print(f"Will skip email sending: {not SMTP_USERNAME or not SMTP_PASSWORD}")

if SMTP_USERNAME and SMTP_PASSWORD:
    print("\n✅ SMTP credentials are configured - emails should be sent via Dreamhost")
else:
    print("\n❌ SMTP credentials missing - emails will only be logged to console")