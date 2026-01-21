import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext
import os

class PTITClient:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Token capture listener
        self.auth_token = None
        async def capture_token(request):
            # print(f"Request: {request.url}") # verbose
            if "authorization" in request.headers:
                auth = request.headers["authorization"]
                # print(f"Auth header found: {auth[:20]}...")
                if not self.auth_token and "Bearer" in auth:
                    self.auth_token = auth
                    print(f"Auth token captured from {request.url}!")
        
        self.page.on("request", capture_token)

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self, username, password):
        if not self.page:
            await self.start()
        
        print(f"Navigating to login page...")
        await self.page.goto("https://qldt.ptit.edu.vn/#/")
        
        # Wait for username input
        await self.page.wait_for_selector("input[formcontrolname='username']")
        
        print("Filling credentials...")
        await self.page.fill("input[formcontrolname='username']", username)
        await self.page.fill("input[formcontrolname='password']", password)
        
        # Submit via Enter key (usually more robust)
        print("Submitting login form via Enter key...")
        await self.page.press("input[formcontrolname='password']", "Enter")
        
        # Fallback to button if needed (commented out or used if Enter fails?)
        # Let's just trust Enter for now, or click button if URL doesn't change?
        # Simpler is better.
        # login_btn = self.page.locator("button:has-text('Đăng nhập')")
        # if await login_btn.count() > 0:
        #     await login_btn.first.click()

        print("Waiting for navigation...")
        # Wait for some indicator of success, e.g. URL change or 'Đăng xuất' button
        # Wait for either home URL or "Đăng xuất" element
        # We use a race to check success vs failure
        try:
            # Wait for successful login API or student info load
            # w-locsinhvieninfo is called when logged in
            print("Waiting for post-login API calls...")
            await self.page.wait_for_response(lambda r: "w-locsinhvieninfo" in r.url and r.status == 200, timeout=30000)
            print("Login success: Student info loaded")
            await self.page.wait_for_load_state("networkidle")
            
            # Ensure we have the token
            if not self.auth_token:
                print("Warning: Auth token not yet captured. Waiting a bit more...")
                await self.page.wait_for_timeout(2000)
                 
        except:
             print("Login verification warning: API not detected or timeout.")
             # Check error
             if await self.page.locator(".toast-error").count() > 0:
                 text = await self.page.locator(".toast-error").text_content()
                 raise Exception(f"Login failed: {text}")
             
             # Fail only if we are definitely on login page (and no redirect happening)
             if await self.page.locator("input[formcontrolname='username']").count() > 0:
                  # one last check if maybe we are already logged in?
                  if "login" in self.page.url:
                      raise Exception("Login failed: Still on login input page")
             print("Assuming success...")

        # Return page content for debugging next steps
        return await self.page.title()

    async def get_schedule(self):
        if not self.page:
            raise Exception("Client not started or logged in")
            
        if not self.auth_token:
             raise Exception("Auth token not available")

        print("Fetching semester info...")
        # Execute fetch in page context passing the token
        semesters_json = await self.page.evaluate("""async (token) => {
            const response = await fetch('/public/api/sch/w-locdshockytkbuser', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': token
                },
                body: JSON.stringify({filter: {}, additional: {paging: {limit: 100, page: 1}, ordering: [{name: null, order_type: null}]}})
            });
            return await response.json();
        }""", self.auth_token)
        
        if not semesters_json.get('result'):
             raise Exception("Failed to fetch semesters")
             
        # Assume first or current semester.
    async def get_schedule(self):
        if not self.page:
            raise Exception("Client not started or logged in")
            
        print("Navigating to Schedule for interception...")
        # Navigate to schedule page
        await self.page.goto("https://qldt.ptit.edu.vn/public/#/tkb-tuan")
        
        try:
            print("Waiting for schedule API response...")
            # Wait for the specific API call that returns schedule data
            # Note: We match the specific endpoint we found earlier
            async with self.page.expect_response(lambda r: "w-locdstkbtuanusertheohocky" in r.url and r.status == 200, timeout=20000) as response_info:
                # We need to trigger the request if it hasn't happened, but goto should trigger it.
                # However, expect_response context manager should be set up BEFORE the action that triggers it?
                # Actually, if the request happens immediately after goto, we might miss it if we await goto first.
                # But wait_for_response (which expect_response is similar to) works if we set it up in parallel or if we use the promise pattern.
                pass
                
            # Actually, let's use the simpler pattern:
            # We already navigated. If the request is pending, wait_for_response works.
            # If we missed it, we might need to reload.
            # But standard pattern is:
            # async with page.expect_response(...) as response_info:
            #      await page.goto(...)
            
            # Let's retry properly with reload if needed, or just define it better.
        except:
             print("Initial navigation might have missed the event. Reloading...")
        
        # Robust pattern:
        print("Triggering schedule load...")
        async with self.page.expect_response(lambda r: "w-locdstkbtuanusertheohocky" in r.url and r.status == 200, timeout=15000) as response_info:
             # Force reload to ensure request fires while we are listening
             await self.page.reload()
        
        response = await response_info.value
        print("Schedule API intercepted!")
        json_data = await response.json()
        
        if not json_data.get('result'):
             raise Exception("Failed to fetch schedule data")
             
        return json_data['data']
