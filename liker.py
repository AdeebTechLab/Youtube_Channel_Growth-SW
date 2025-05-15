import random
import json
import os
import time
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor

def load_proxies_from_file(file_path="proxies.txt"):
    proxies = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                proxy = line.strip()
                if proxy:
                    proxies.append(proxy)
        print(f"✅ Loaded {len(proxies)} proxies from {file_path}")
    except FileNotFoundError:
        print(f"❌ Proxy file '{file_path}' not found.")
    except Exception as e:
        print(f"❌ Error loading proxies: {str(e)}")
    
    return proxies

def like_video(account_name, video_url, proxy=None):
    """
    Optimized function to like a YouTube video
    """
    print(f"\n=== Starting like_video for account: {account_name} ===")
    
    if not os.path.exists("cookies"):
        os.makedirs("cookies")
        print("Created 'cookies' directory")
    
    cookie_file = f"cookies/{account_name}.json"
    if not os.path.exists(cookie_file):
        print(f"ERROR: Cookie file for '{account_name}' not found at {cookie_file}")
        print(f"Available cookie files: {os.listdir('cookies')}")
        return False
    else:
        print(f"Found cookie file: {cookie_file}")

    proxy_settings = None
    if proxy:
        print(f"Using proxy: {proxy}")
        proxy_settings = {"server": proxy}
    else:
        print("Proceeding without proxy.")

    try:
        with sync_playwright() as p:
            # Optimized browser launch arguments
            browser_args = {
                "headless": False,
                "args": [
                    '--disable-extensions',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-background-networking',
                    '--disable-default-apps',
                    '--no-default-browser-check',
                    '--disable-translate',
                    '--disable-sync',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ],
                "ignore_default_args": ["--enable-automation"]
            }
            
            if proxy_settings:
                browser_args["proxy"] = proxy_settings
                
            browser = p.chromium.launch(**browser_args)
            
            # Set viewport size for better visibility and add user agent
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            )
            
            # Bypass detection
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                // Overwrite the plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Overwrite the languages property
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'es']
                });
            """)

            # Load cookies
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
            except json.JSONDecodeError:
                print(f"Invalid cookie file for {account_name}. Please re-login.")
                time.sleep(5)  # Keep browser open longer for debugging
                browser.close()
                return False

            page = context.new_page()
            
            print(f"Navigating to: {video_url}")
            
            # Use page.goto with timeout and wait_until options
            try:
                page.goto(video_url, timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"Failed to load page: {e}")
                time.sleep(5)  # Keep browser open longer for debugging
                browser.close()
                return False
                
            # Wait for video page to load with more reliable method
            try:
                # Wait for video player to be visible with longer timeout
                page.wait_for_selector('#movie_player', timeout=15000)
                
                # Add some minimal wait time for page to load
                wait_time = random.uniform(2, 3)
                print(f"Waiting for {wait_time:.1f} seconds for page to load...")
                time.sleep(wait_time)
                
                # Scroll down a bit to make like button visible
                page.evaluate("window.scrollBy(0, 200)")
                time.sleep(0.5)
                
                # Try to dismiss any popups or overlays that might be blocking the like button
                try:
                    dismiss_buttons = page.query_selector_all('button[aria-label="Dismiss"], button[aria-label="No thanks"], .ytp-ad-skip-button')
                    for button in dismiss_buttons:
                        button.click()
                        time.sleep(1)
                except Exception as e:
                    print(f"Error dismissing popups: {e}")
                
                print("Attempting to like the video...")
                
                # More reliable like button selector
                like_button_selectors = [
                    '#top-level-buttons-computed ytd-toggle-button-renderer:first-child button',
                    '#top-level-buttons-computed > segmented-like-dislike-button-view-model > yt-smartimation > div > div > like-button-view-model > toggle-button-view-model > button-view-model > button',
                    'ytd-menu-renderer.ytd-watch-metadata button[aria-label*="like"]',
                    'button[aria-label*="like this video"]',
                    'button[aria-label*="Like"]',
                    'ytd-toggle-button-renderer button',
                    '#segmented-like-button button',
                    'like-button-view-model button',
                    'button[aria-pressed]',
                    'button.yt-spec-button-shape-next'
                ]
                
                liked = False
                for selector in like_button_selectors:
                    try:
                        # Wait for the selector with a short timeout
                        page.wait_for_selector(selector, timeout=3000)
                        like_button = page.query_selector(selector)
                        if like_button:
                            # Check if already liked
                            aria_label = like_button.get_attribute('aria-label') or ''
                            aria_pressed = like_button.get_attribute('aria-pressed')
                            
                            if aria_pressed == 'true' or 'liked' in aria_label.lower():
                                print(f"Video already liked by account '{account_name}'")
                                time.sleep(5)  # Keep browser open longer for verification
                                browser.close()
                                return True
                                
                            # Click the like button
                            like_button.click()
                            print(f"Liked video using account '{account_name}'" + 
                                  (f" with proxy {proxy}" if proxy_settings else " without proxy"))
                            liked = True
                            
                            # Brief wait to ensure the like is registered
                            time.sleep(1)
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {str(e)}")
                        continue
                
                if not liked:
                    # Try JavaScript approach as fallback
                    try:
                        result = page.evaluate("""
                            () => {
                                // Try multiple selectors with more comprehensive options
                                const selectors = [
                                    '#top-level-buttons-computed ytd-toggle-button-renderer:first-child button',
                                    '#top-level-buttons-computed > segmented-like-dislike-button-view-model > yt-smartimation > div > div > like-button-view-model > toggle-button-view-model > button-view-model > button',
                                    'ytd-menu-renderer.ytd-watch-metadata button[aria-label*="like"]',
                                    'button[aria-label*="like this video"]',
                                    'button[aria-label*="Like"]',
                                    '#segmented-like-button button',
                                    'like-button-view-model button',
                                    'button[aria-pressed]',
                                    'button.yt-spec-button-shape-next',
                                    // Try to find any button that looks like a like button
                                    'button:has(yt-icon), button:has(svg)'
                                ];
                                
                                // First check if already liked
                                for (const selector of selectors) {
                                    const button = document.querySelector(selector);
                                    if (button && (button.getAttribute('aria-pressed') === 'true' || 
                                                  button.getAttribute('aria-label')?.toLowerCase().includes('liked'))) {
                                        console.log('Already liked');
                                        return 'already-liked';
                                    }
                                }
                                
                                // Try clicking the like button
                                for (const selector of selectors) {
                                    const likeButton = document.querySelector(selector);
                                    if (likeButton) {
                                        // Try to determine if this is actually a like button
                                        const ariaLabel = likeButton.getAttribute('aria-label') || '';
                                        const innerText = likeButton.innerText || '';
                                        
                                        if (ariaLabel.toLowerCase().includes('like') || 
                                            innerText.toLowerCase().includes('like') ||
                                            selector.includes('like')) {
                                            console.log('Found like button, clicking...');
                                            likeButton.click();
                                            return true;
                                        }
                                    }
                                }
                                
                                // Last resort: try to find any button in the video controls area
                                const allButtons = document.querySelectorAll('#top-level-buttons-computed button, ytd-menu-renderer button');
                                if (allButtons.length > 0) {
                                    // Usually the first button is the like button
                                    allButtons[0].click();
                                    return 'clicked-first-button';
                                }
                                
                                return false;
                            }
                        """)
                        print(f"JavaScript fallback result: {result}")
                        if result == 'already-liked':
                            print(f"Video already liked by account '{account_name}'")
                            liked = True
                        elif result:
                            print(f"Liked video using JavaScript fallback for account '{account_name}'")
                            liked = True
                    except Exception as e:
                        print(f"JavaScript fallback failed: {str(e)}")
                
                # No screenshot needed
                
                # Close browser immediately after liking
                browser.close()
                return liked
                
            except Exception as e:
                print(f"Error liking video: {str(e)}")
                # No screenshot needed
                time.sleep(5)  # Keep browser open longer for debugging
                browser.close()
                return False
                
    except Exception as e:
        print(f"Error during operation: {str(e)}")
        return False

# Function to process multiple accounts in parallel
def process_multiple_likes(accounts, video_url, proxies=None, max_workers=2):
    """
    Process multiple accounts in parallel to like a video
    """
    results = []
    
    def process_account(account):
        proxy = random.choice(proxies) if proxies else None
        print(f"\n➡ Liking from {account} {'using proxy ' + proxy if proxy else 'without proxy'}")
        result = like_video(account, video_url, proxy)
        return (account, result)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_account, accounts))
    
    return results

# === CLI-style runner ===
if __name__ == "__main__":
    video_url = input("📺 Enter the YouTube video URL: ").strip()
    account_name = input("👤 Enter the account name (cookie file): ").strip()
    use_proxy_input = input("🌐 Do you want to use proxies? (yes/no): ").strip().lower()

    proxy = None
    if use_proxy_input == "yes":
        proxies = load_proxies_from_file("proxies.txt")
        if proxies:
            proxy = random.choice(proxies)
    
    like_video(account_name, video_url, proxy)
