import asyncio
from playwright.async_api import async_playwright

async def manual_login_and_save():
    print("Starting Browser for manual login...")
    print("Please login to your Outlook account when the browser opens.")
    print("When you see your Inbox, verify successful login.")
    print("Then checking terminal to save state...")
    
    async with async_playwright() as p:
        # Launch persistent context or normal browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://outlook.office.com/mail/")
        
        print("🔴 ACTION REQUIRED: Please log in manually in the browser window!")
        print("Waiting for you to reach the Inbox (Checking for 'Inbox' text or listbox)...")
        
        # Poll for inbox element (timeout 5 minutes)
        try:
            # Wait for listbox with a very long timeout
            await page.wait_for_selector('div[role="listbox"]', timeout=300000)
            print("✅ Inbox detected!")
            
            # Save state
            await context.storage_state(path="outlook_state.json")
            print("✅ Session saved to 'outlook_state.json'")
            print("You can now close the browser.")
            
        except Exception as e:
            print(f"❌ Timed out waiting for Inbox (5 mins). Did you log in? Error: {e}")
            
        await asyncio.sleep(5) 
        await browser.close()

if __name__ == "__main__":
    asyncio.run(manual_login_and_save())
