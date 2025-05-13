import os
import json
import time
import random
from playwright.sync_api import sync_playwright
from proxy_rotator import load_proxies, get_proxy_rotation_choice, select_proxies, get_random_proxy

def subscribe_video(account_name, video_url, proxy=None):
    cookie_file = f"cookies/{account_name}.json"
    if not os.path.exists(cookie_file):
        print(f"Cookie file for {account_name} not found.")
        return False

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
            
            if proxy:
                browser_args["proxy"] = {"server": proxy}
                
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
                # Wait for video player to be visible
                page.wait_for_selector('#movie_player', timeout=15000)
                
                # Add some randomized human-like behavior
                wait_time = random.uniform(3, 6)
                print(f"Waiting for {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                
                # Scroll down a bit to make subscribe button visible
                page.evaluate("window.scrollBy(0, 200)")
                time.sleep(1)
                
                # Try multiple selectors for the subscribe button
                subscribe_selectors = [
                    '#subscribe-button-shape button',
                    '#subscribe-button button',
                    'ytd-subscribe-button-renderer button',
                    'button[aria-label*="Subscribe"]'
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
                    
                    # Wait longer after subscribing to verify
                    time.sleep(5)
                    
                    # Verify subscription was successful
                    for selector in subscribe_selectors:
                        try:
                            verify_button = page.query_selector(selector)
                            if verify_button and ("subscribed" in verify_button.inner_text().lower() or 
                                                "unsubscribe" in verify_button.inner_text().lower()):
                                print("Subscription verified!")
                                time.sleep(3)  # Keep browser open longer for verification
                                browser.close()
                                return True
                        except:
                            continue
                    
                    # If we couldn't verify, still return success but with a warning
                    print("Subscription action completed but couldn't verify status")
                    time.sleep(5)
                    browser.close()
                    return True
                else:
                    print("Subscribe button not found or already subscribed.")
                    # No screenshot needed
                    time.sleep(5)  # Keep browser open longer for debugging
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
