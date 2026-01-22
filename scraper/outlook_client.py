import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

class OutlookClient:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        
        # Load state if exists
        state_path = "outlook_state.json"
        if os.path.exists(state_path):
            print(f"Loading session from {state_path}")
            self.context = await self.browser.new_context(storage_state=state_path)
        else:
            print("No session file found, starting fresh context.")
            self.context = await self.browser.new_context()
            
        self.page = await self.context.new_page()
        
    async def close(self):
        if self.browser:
            await self.browser.close()
            
    async def login(self, email=None, password=None):
        # email/password are optional now if we have session
        if not self.page:
            await self.start()
            
        print("Navigating to Outlook...")
        try:
             await self.page.goto("https://outlook.office.com/mail/", timeout=60000, wait_until="domcontentloaded")
        except:
             pass

        # Check if logged in (Inbox visible)
        try:
            print("Checking session validity...")
            # If logged in, we should see listbox or specific app element
            await self.page.wait_for_selector('div[role="listbox"], div[aria-label="Message list"]', timeout=20000)
            print("✅ Session valid! Already logged in.")
            return True
        except:
            print("⚠️ Session invalid or expired. Attempting re-login...")

        # Fallback to manual login if creds provided
        if not email or not password:
            print("Cannot re-login: No credentials provided.")
            return False
            
        # ... (Legacy login code if needed) ...

        
        # Smart Wait: Wait for either Email Input OR Inbox Element
        try:
            print("Checking state...")
            found = await self.page.wait_for_selector('input[type="email"], div[role="listbox"]', timeout=15000)
            
            tag_name = await found.evaluate("el => el.tagName")
            
            if tag_name == "DIV": 
                print("Already logged in (Inbox found).")
                return
        except Exception:
            print("State check timeout. Assuming login needed.")
        
        # 1. Email
        print("Entering email...")
        try:
            await self.page.fill('input[type="email"]', email)
            await self.page.click('input[type="submit"]')
        except:
             print("Email field not found. Maybe already on password page?")

        # 2. Password
        print("Entering password...")
        try:
             await self.page.wait_for_selector('input[type="password"]', timeout=10000)
             await self.page.fill('input[type="password"]', password)
             await self.page.click('input[type="submit"]') 
        except Exception as e:
             print(f"Password step skipped or failed: {e}")
        
        # 3. Stay signed in
        try:
            print("Handling 'Stay signed in'...")
            yes_btn = await self.page.wait_for_selector('#idSIButton9', timeout=5000)
            if yes_btn:
                await yes_btn.click()
        except:
            pass 
            
        # Wait for inbox
        print("Waiting for Inbox to load...")
        try:
            await self.page.wait_for_selector('div[role="listbox"]', timeout=60000)
            print("Inbox loaded!")
        except Exception as e:
            print(f"Inbox load timeout: {e}")
            await asyncio.sleep(5)

    async def check_recent_emails(self):
        # Scan for emails
        print("Scanning emails...")
        emails = []
        try:
            # Wait for message list items (div with role="option")
            await self.page.wait_for_selector('div[role="option"]', timeout=10000)
            items = await self.page.locator('div[role="option"]').all()
            
            for item in items:
                text = await item.text_content()
                if text:
                    # Return all emails found
                    # Clean up text (it contains sender, subject, preview...)
                    # Usually: "Sender\nSubject\nPreview"
                    lines = text.split('\n')
                    if len(lines) >= 2:
                        subject = lines[0].strip() + " - " + lines[1].strip() # Sender - Subject
                        emails.append(subject)
                    else:
                        emails.append(text.split('\n')[0].strip())
        except Exception as e:
            print(f"Error scanning emails: {e}")
            
        return emails

async def main():
    import sys
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    load_dotenv()
    email = "HoangNH.B22CN336@stu.ptit.edu.vn" 
    password = os.getenv("SCHOOL_PASSWORD") 
    
    if not password:
         password = "4mckAiL47LRni9p" 
         
    print("Starting Outlook Client...")
    
    max_retries = 3
    for i in range(max_retries):
        client = OutlookClient(headless=False) 
        try:
            await client.start()
            await client.login(email, password)
            emails = await client.check_recent_emails()
            print("Found emails:", emails)
            print("Closing in 10 seconds...")
            await asyncio.sleep(10)
            break 
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            if i < max_retries - 1:
                print("Retrying in 5 seconds...")
                await asyncio.sleep(5)
        finally:
            await client.close()

if __name__ == "__main__":
    asyncio.run(main())
