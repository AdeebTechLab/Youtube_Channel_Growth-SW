import os
import json
import time
import random
from playwright.sync_api import sync_playwright
from proxy_rotator import load_proxies, get_proxy_rotation_choice, select_proxies, get_random_proxy

def subscribe_video(account_name, video_url, proxy=None):
    print(f"\n=== Starting subscribe_video for account: {account_name} ===")
    
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
            
            if proxy:
                browser_args["proxy"] = {"server": proxy}
                
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
                # Wait for video player to be visible
                page.wait_for_selector('#movie_player', timeout=15000)
                
                # Add minimal wait time for page to load
                wait_time = random.uniform(2, 3)
                print(f"Waiting for {wait_time:.1f} seconds for page to load...")
                time.sleep(wait_time)
                
                # Scroll down a bit to make subscribe button visible
                page.evaluate("window.scrollBy(0, 200)")
                time.sleep(0.5)
                
                # Try to dismiss any popups or overlays that might be blocking the subscribe button
                try:
                    dismiss_buttons = page.query_selector_all('button[aria-label="Dismiss"], button[aria-label="No thanks"], .ytp-ad-skip-button')
                    for button in dismiss_buttons:
                        button.click()
                        time.sleep(1)
                except Exception as e:
                    print(f"Error dismissing popups: {e}")
                
                # Try multiple selectors for the subscribe button
                subscribe_selectors = [
                    '#subscribe-button-shape button',
                    '#subscribe-button button',
                    'ytd-subscribe-button-renderer button',
                    'button[aria-label*="Subscribe"]',
                    '#subscribe-button',
                    'ytd-subscribe-button-renderer',
                    '#owner-subscribe-button',
                    'paper-button.ytd-subscribe-button-renderer',
                    'tp-yt-paper-button.ytd-subscribe-button-renderer'
                ]
                
                subscribe_button = None
                for selector in subscribe_selectors:
                    try:
                        # Wait for the selector with a short timeout
                        page.wait_for_selector(selector, timeout=3000)
                        subscribe_button = page.query_selector(selector)
                        if subscribe_button:
                            print(f"Found subscribe button with selector: {selector}")
                            break
                    except:
                        continue
                
                if subscribe_button:
                    # Check if already subscribed
                    button_text = subscribe_button.inner_text().lower()
                    if "subscribed" in button_text or "unsubscribe" in button_text:
                        print(f"Already subscribed with account {account_name}")
                        time.sleep(5)  # Keep browser open longer for verification
                        browser.close()
                        return True
                    
                    # Click the subscribe button
                    subscribe_button.click()
                    print(f"Subscribed using account {account_name} {'with proxy ' + proxy if proxy else 'without proxy'}.")
                    
                    # Brief wait to ensure the subscription is registered
                    time.sleep(1)
                    
                    # Quick verification of subscription
                    for selector in subscribe_selectors:
                        try:
                            verify_button = page.query_selector(selector)
                            if verify_button and ("subscribed" in verify_button.inner_text().lower() or 
                                                "unsubscribe" in verify_button.inner_text().lower()):
                                print("Subscription verified!")
                                # Close browser immediately after subscribing
                                browser.close()
                                return True
                        except:
                            continue
                    
                    # If we couldn't verify, still return success but with a warning
                    print("Subscription action completed but couldn't verify status")
                    browser.close()
                    return True
                else:
                    # Try JavaScript approach as fallback
                    try:
                        print("Trying JavaScript fallback for subscribe...")
                        result = page.evaluate("""
                            () => {
                                // Try multiple selectors with more comprehensive options
                                const selectors = [
                                    '#subscribe-button-shape button',
                                    '#subscribe-button button',
                                    'ytd-subscribe-button-renderer button',
                                    'button[aria-label*="Subscribe"]',
                                    '#subscribe-button',
                                    'ytd-subscribe-button-renderer',
                                    '#owner-subscribe-button',
                                    'paper-button.ytd-subscribe-button-renderer',
                                    'tp-yt-paper-button.ytd-subscribe-button-renderer'
                                ];
                                
                                // First check if already subscribed
                                for (const selector of selectors) {
                                    const button = document.querySelector(selector);
                                    if (button) {
                                        const text = button.innerText.toLowerCase();
                                        const ariaLabel = button.getAttribute('aria-label')?.toLowerCase() || '';
                                        
                                        if (text.includes('subscribed') || text.includes('unsubscribe') || 
                                            ariaLabel.includes('subscribed') || ariaLabel.includes('unsubscribe')) {
                                            console.log('Already subscribed');
                                            return 'already-subscribed';
                                        }
                                    }
                                }
                                
                                // Try clicking the subscribe button
                                for (const selector of selectors) {
                                    const subscribeButton = document.querySelector(selector);
                                    if (subscribeButton) {
                                        console.log('Found subscribe button, clicking...');
                                        subscribeButton.click();
                                        return true;
                                    }
                                }
                                
                                // Last resort: try to find any button in the channel info area
                                const channelButtons = document.querySelectorAll('#channel-info button, #owner button');
                                for (const button of channelButtons) {
                                    const text = button.innerText.toLowerCase();
                                    const ariaLabel = button.getAttribute('aria-label')?.toLowerCase() || '';
                                    
                                    if (text.includes('subscribe') || ariaLabel.includes('subscribe')) {
                                        button.click();
                                        return 'clicked-channel-button';
                                    }
                                }
                                
                                return false;
                            }
                        """)
                        print(f"JavaScript fallback result: {result}")
                        
                        if result == 'already-subscribed':
                            print(f"Already subscribed with account {account_name}")
                            browser.close()
                            return True
                        elif result:
                            print(f"Subscribed using JavaScript fallback with account {account_name}")
                            browser.close()
                            return True
                        else:
                            print("Subscribe button not found or already subscribed.")
                            browser.close()
                            return False
                    except Exception as e:
                        print(f"JavaScript fallback failed: {e}")
                        browser.close()
                        return False
                    
            except Exception as e:
                print(f"Failed to subscribe: {e}")
                # No screenshot needed
                time.sleep(5)  # Keep browser open longer for debugging
                browser.close()
                return False
                
    except Exception as e:
        print(f"Error during operation: {str(e)}")
        return False
