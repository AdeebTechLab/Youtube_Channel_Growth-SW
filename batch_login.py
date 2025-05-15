import os
import json
import time
import random
from playwright.sync_api import sync_playwright
from proxy_rotator import load_proxies, get_random_proxy

# Create cookies directory if it doesn't exist
os.makedirs("cookies", exist_ok=True)

def parse_accounts(accounts_text):
    """Parse a list of accounts in the format email:password or email,password"""
    accounts = []
    for line in accounts_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Support both colon and comma as separators
        if ':' in line:
            email, password = line.split(':', 1)
        elif ',' in line:
            email, password = line.split(',', 1)
        else:
            print(f"⚠️ Skipping invalid format: {line}")
            continue
            
        accounts.append({
            'email': email.strip(),
            'password': password.strip()
        })
    
    return accounts

def get_next_account_number():
    """Get the next available account number"""
    existing = [f for f in os.listdir("cookies") if f.startswith("account") and f.endswith(".json")]
    nums = [int(f.replace("account", "").replace(".json", "")) for f in existing if f.replace("account", "").replace(".json", "").isdigit()]
    return max(nums) + 1 if nums else 1

def check_login_status(page):
    """Check if user is logged in by looking for avatar button"""
    try:
        return page.query_selector('ytd-topbar-menu-button-renderer.ytd-masthead') is not None
    except:
        return False

def login_account(email, password, proxy=None, account_number=None):
    """Login to a Google account and save cookies"""
    if account_number is None:
        account_number = get_next_account_number()
        
    account_name = f"account{account_number}"
    cookie_file = f"cookies/{account_name}.json"
    
    print(f"\n{'='*50}")
    print(f"Processing account {account_number}: {email}")
    print(f"{'='*50}")
    
    if proxy:
        print(f"Using proxy: {proxy}")
    
    try:
        with sync_playwright() as p:
            # Configure browser launch options
            browser_args = {
                "headless": False,  # Set to True for production
                "args": [
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
            }
            
            # Add proxy if provided
            if proxy:
                browser_args["proxy"] = {"server": proxy}
            
            # Launch browser
            browser = p.chromium.launch(**browser_args)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # Navigate to Google sign-in
            print("Opening Google login page...")
            page.goto("https://accounts.google.com/signin/v2/identifier?service=youtube")
            
            # Enter email
            print(f"Entering email: {email}")
            page.fill('input[type="email"]', email)
            page.click('button:has-text("Next")')
            
            # Wait for password field and enter password
            try:
                page.wait_for_selector('input[type="password"]', timeout=10000)
                print("Entering password...")
                page.fill('input[type="password"]', password)
                page.click('button:has-text("Next")')
            except Exception as e:
                print(f"❌ Error entering password: {str(e)}")
                browser.close()
                return False
            
            # Wait for potential security verification
            print("Waiting for login process to complete...")
            
            # Check for common verification screens
            try:
                # Check for "Verify it's you" screen
                verify_selector = page.query_selector('h1:has-text("Verify it\'s you")')
                if verify_selector:
                    print("⚠️ Security verification required. Please complete it manually.")
                    input("Press Enter when verification is complete > ")
            except:
                pass
                
            # Wait for login to complete
            max_wait = 60  # Maximum wait time in seconds
            start_time = time.time()
            logged_in = False
            
            while time.time() - start_time < max_wait:
                try:
                    # Navigate to YouTube to verify login
                    page.goto("https://www.youtube.com")
                    time.sleep(5)  # Give time for the page to load
                    
                    # Check login status
                    cookies = context.cookies()
                    logged_in = any("LOGIN_INFO" in cookie['name'] or "SID" in cookie['name'] for cookie in cookies)
                    
                    # Double-check by looking for avatar element
                    if not logged_in:
                        logged_in = check_login_status(page)
                        
                    if logged_in:
                        break
                        
                    print("Login not detected yet. Waiting...")
                    time.sleep(5)
                except Exception as e:
                    print(f"Error checking login status: {str(e)}")
                    time.sleep(5)
            
            if logged_in:
                # Save cookies
                cookies = context.cookies()
                with open(cookie_file, "w") as f:
                    json.dump(cookies, f)
                print(f"✅ SUCCESS: Cookies saved as {cookie_file}")
                browser.close()
                return True
            else:
                print("❌ ERROR: Login failed or timed out.")
                browser.close()
                return False
                
    except Exception as e:
        print(f"❌ Error during login process: {str(e)}")
        return False

def batch_login_accounts():
    """Process multiple accounts from a list"""
    print("\n" + "="*50)
    print("Batch Account Login".center(50))
    print("="*50)
    
    print("Enter your Gmail accounts in the format email:password or email,password")
    print("One account per line. Press Ctrl+D (Unix) or Ctrl+Z (Windows) when finished.")
    print("-"*50)
    
    # Collect account list
    accounts_text = ""
    try:
        while True:
            line = input()
            accounts_text += line + "\n"
    except EOFError:
        pass
    
    # Parse accounts
    accounts = parse_accounts(accounts_text)
    if not accounts:
        print("❌ No valid accounts provided.")
        return
        
    print(f"✅ Parsed {len(accounts)} accounts.")
    
    # Ask about using proxies
    use_proxies = input("Do you want to use proxies? (yes/no): ").strip().lower() == "yes"
    proxies = []
    
    if use_proxies:
        proxies = load_proxies()
        if not proxies:
            print("❌ No proxies available.")
            use_anyway = input("Continue without proxies? (yes/no): ").strip().lower()
            if use_anyway != "yes":
                return
    
    # Start processing accounts
    start_account_number = get_next_account_number()
    success_count = 0
    
    for i, account in enumerate(accounts):
        account_number = start_account_number + i
        proxy = get_random_proxy(proxies) if proxies else None
        
        print(f"\nProcessing account {i+1}/{len(accounts)}: {account['email']}")
        
        if login_account(account['email'], account['password'], proxy, account_number):
            success_count += 1
            
        # Add a delay between accounts to avoid triggering security measures
        if i < len(accounts) - 1:
            delay = random.randint(5, 15)
            print(f"Waiting {delay} seconds before next account...")
            time.sleep(delay)
    
    print("\n" + "="*50)
    print(f"Batch processing complete: {success_count}/{len(accounts)} successful")
    print("="*50)

if __name__ == "__main__":
    batch_login_accounts()