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
    if not os.path.exists("cookies"):
        os.makedirs("cookies")
        print("Created 'cookies' directory")
    
    cookie_file = f"cookies/{account_name}.json"
    if not os.path.exists(cookie_file):
        print(f"Cookie file for '{account_name}' not found.")
        return False

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
                ]
            }
            
            if proxy_settings:
                browser_args["proxy"] = proxy_settings
                
            browser = p.chromium.launch(**browser_args)
            
            # Set viewport size for better visibility
            context = browser.new_context(viewport={'width': 1280, 'height': 800})

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
            
            # Add user agent to appear more like a real browser
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
            })
            
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
                
                # Add some randomized human-like behavior
                wait_time = random.uniform(3, 5)
                print(f"Waiting for {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                
                # Scroll down a bit to make like button visible
                page.evaluate("window.scrollBy(0, 200)")
                time.sleep(1)
                
                print("Attempting to like the video...")
                
                # More reliable like button selector
                like_button_selectors = [
                    '#top-level-buttons-computed ytd-toggle-button-renderer:first-child button',
                    '#top-level-buttons-computed > segmented-like-dislike-button-view-model > yt-smartimation > div > div > like-button-view-model > toggle-button-view-model > button-view-model > button',
                    'ytd-menu-renderer.ytd-watch-metadata button[aria-label*="like"]',
                    'button[aria-label*="like this video"]',
                    'button[aria-label*="Like"]',
                    'ytd-toggle-button-renderer button'
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
                            
                            # Wait longer to verify the like was registered
                            time.sleep(5)
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {str(e)}")
                        continue
                
                if not liked:
                    # Try JavaScript approach as fallback
                    try:
                        page.evaluate("""
                            () => {
                                // Try multiple selectors
                                const selectors = [
                                    '#top-level-buttons-computed ytd-toggle-button-renderer:first-child button',
                                    '#top-level-buttons-computed > segmented-like-dislike-button-view-model > yt-smartimation > div > div > like-button-view-model > toggle-button-view-model > button-view-model > button',
                                    'ytd-menu-renderer.ytd-watch-metadata button[aria-label*="like"]',
                                    'button[aria-label*="like this video"]',
                                    'button[aria-label*="Like"]'
                                ];
                                
                                for (const selector of selectors) {
                                    const likeButton = document.querySelector(selector);
                                    if (likeButton) {
                                        likeButton.click();
                                        return true;
                                    }
                                }
                                return false;
                            }
                        """)
                        print(f"Attempted to like video using JavaScript fallback for account '{account_name}'")
                        liked = True
                    except Exception as e:
                        print(f"JavaScript fallback failed: {str(e)}")
                
                # No screenshot needed
                
                # Wait longer after liking to keep browser visible
                time.sleep(8)
                
                # Close browser and return result
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
