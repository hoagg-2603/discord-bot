import imaplib
import os

EMAIL_USER = "HoangNH.B22CN336@stu.ptit.edu.vn" 
# Hardcoded password for testing (as requested)
EMAIL_PASS = "4mckAiL47LRni9p"

IMAP_SERVER = "outlook.office365.com"
IMAP_PORT = 993

def test_connection():
    print(f"Connecting to {IMAP_SERVER} as {EMAIL_USER}...")
    
    try:
        # Connect to server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        
        # Login
        mail.login(EMAIL_USER, EMAIL_PASS)
        print("✅ Login SUCCESS! IMAP access is enabled.")
        
        # List folders
        status, folders = mail.list()
        mail.logout()
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Login Failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
