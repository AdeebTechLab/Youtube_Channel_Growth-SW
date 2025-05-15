import os
import json
import time
import sys
from playwright.sync_api import sync_playwright

os.makedirs("cookies", exist_ok=True)

def get_next_account_name():
    existing = [f for f in os.listdir("cookies") if f.startswith("account") and f.endswith(".json")]
    nums = [int(f.replace("account", "").replace(".json", "")) for f in existing if f.replace("account", "").replace(".json", "").isdigit()]
    next_num = max(nums) + 1 if nums else 1
    return f"account{next_num}"

def check_login_status(page):
    """Check if user is logged in by looking for avatar button"""
    try:
        return page.query_selector('ytd-topbar-menu-button-renderer.ytd-masthead') is not None
    except:
        return False

def main():
    """Main function to save cookies for a YouTube account"""
    # Check if batch mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        from batch_login import batch_login_accounts
        batch_login_accounts()
        return
        
    print("=" * 50)
    print("YouTube Account Cookie Saver")
    print("=" * 50)
    
    account_name = get_next_account_name()
    cookie_file = f"cookies/{account_name}.json"
    print(f"Creating new account: {account_name}")
    print("-" * 50)

    with sync_playwright() as p:
        # Launch with more browser arguments for better performance
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                '--disable-background-networking',
                '--disable-default-apps',
                '--no-default-browser-check',
                '--disable-translate',
                '--disable-sync',
                '--disable-site-isolation-trials',
                '--disable-features=TranslateUI,BlinkGenPropertyTrees'
            ]
        )
        
        # Set viewport size for better visibility
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # Navigate to YouTube sign-in page directly
        print("Opening YouTube login page...")
        page.goto("https://accounts.google.com/signin/v2/identifier?service=youtube")
        
        print("\nINSTRUCTIONS:")
        print("1. Log in to your YouTube/Google account in the browser window")
        print("2. Make sure you complete the entire login process")
        print("3. Once you see the YouTube homepage, press Enter here")
        print("\nWaiting for you to complete login...")
        input("Press Enter when login is complete > ")
        
        # Wait a moment after user presses Enter
        print("Checking login status...")
        time.sleep(3)
        
        # Navigate to YouTube to verify login
        page.goto("https://www.youtube.com")
        time.sleep(5)  # Give more time for the page to load completely
        
        # Check login status
        logged_in = False
        retry_count = 0
        max_retries = 3
        
        while not logged_in and retry_count < max_retries:
            cookies = context.cookies()
            logged_in = any("LOGIN_INFO" in cookie['name'] or "SID" in cookie['name'] for cookie in cookies)
            
            # Double-check by looking for avatar element
            if not logged_in:
                logged_in = check_login_status(page)
            
            if logged_in:
                break
                
            print(f"Login not detected (attempt {retry_count+1}/{max_retries}). Waiting a bit longer...")
            time.sleep(5)  # Wait longer before checking again
            retry_count += 1

        if logged_in:
            with open(cookie_file, "w") as f:
                json.dump(cookies, f)
            print(f"SUCCESS: Cookies saved as {cookie_file}")
            print("Window will close automatically in 3 seconds...")
            time.sleep(3)  # Give user time to see the success message
        else:
            print("ERROR: Login not detected. Cookies not saved.")
            print("   Please try again and make sure to complete the login process.")
            input("Press Enter to exit...")  # Only wait for input on failure

        browser.close()

if __name__ == "__main__":
    try:
        main()
        print("\nProcess completed.")
        # No need to wait for Enter here - the window will close automatically
        # after the login check is complete
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        input("Press Enter to exit...")
