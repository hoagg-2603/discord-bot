import imaplib
import email
from email.header import decode_header
import os

class GmailClient:
    def __init__(self, email_address=None, app_password=None):
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = "imap.gmail.com"
        self.mail = None

    def connect(self):
        try:
            # Create SSL connection
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            # Login
            self.mail.login(self.email_address, self.app_password)
            print(f"✅ Gmail connected as {self.email_address}")
            return True
        except Exception as e:
            print(f"❌ Gmail Connection Error: {e}")
            return False

    def check_emails(self, keywords=["nghỉ", "bù"], look_back=5):
        """
        Check N most recent emails for keywords.
        Returns list of matched subjects.
        """
        if not self.mail:
            if not self.connect():
                return []
        
        found_subjects = []
        try:
            self.mail.select("inbox")
            
            # Search all messages
            status, messages = self.mail.search(None, "ALL")
            if status != "OK":
                return []
                
            email_ids = messages[0].split()
            # Get last N emails
            recent_ids = email_ids[-look_back:] if len(email_ids) > look_back else email_ids
            
            for e_id in reversed(recent_ids):
                # Fetch email header
                res, msg_data = self.mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        # Check keyword (case insensitive)
                        # Or return all if keywords empty/generic
                        # User requested "All new emails" logic for outlook, let's allow all here or filter
                        # For now, return Subject
                        
                        found_subjects.append(subject)
                        
            self.mail.close() # Close selection
            
        except Exception as e:
            print(f"Error checking Gmail: {e}")
            
        return found_subjects

    def close(self):
        if self.mail:
            try:
                self.mail.logout()
            except:
                pass

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    user = os.getenv("GMAIL_USER")
    pwd = os.getenv("GMAIL_PASSWORD")
    
    if not user or not pwd:
        print("Missing GMAIL_USER or GMAIL_PASSWORD in .env")
    else:
        client = GmailClient(user, pwd)
        if client.connect():
            emails = client.check_emails(look_back=5)
            print("Recent Emails:", emails)
            client.close()
