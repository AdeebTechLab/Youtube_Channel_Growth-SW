import time
import random
from playwright.sync_api import sync_playwright
from proxy_rotator import load_proxies, get_proxy_rotation_choice, select_proxies, get_random_proxy
from concurrent.futures import ThreadPoolExecutor

def add_view(video_url, proxy=None, watch_duration=None, cancel_check_callback=None):
    """
    Optimized function to add a view to a YouTube video
    
    Args:
        video_url: URL of the YouTube video
        proxy: Optional proxy server to use
        watch_duration: Optional custom watch duration in seconds
        cancel_check_callback: Optional callback function to check if operation should be cancelled
    """
    browser = None
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
                    '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                    '--disable-site-isolation-trials'
                ]
            }
            
            if proxy:
                browser_args["proxy"] = {"server": proxy}
                
            browser = p.chromium.launch(**browser_args)
            
            # Set viewport size for better visibility
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # Add user agent to appear more like a real browser
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
            })
            
            print(f"Watching video: {video_url} {'with proxy ' + proxy if proxy else 'without proxy'}.")
            
            # Check for cancellation
            if cancel_check_callback and cancel_check_callback():
                print("Operation cancelled before loading page")
                browser.close()
                return False
            
            # Use page.goto with timeout and wait_until options for initial load
            try:
                print("Loading page...")
                page.goto(video_url, timeout=60000, wait_until="domcontentloaded")
                
                # Wait for video player to be visible
                print("Waiting for video player to load...")
                page.wait_for_selector('#movie_player', timeout=15000)
                
                # Reload the page to ensure fresh content and proper view counting
                print("Reloading page for proper view counting...")
                page.reload(timeout=60000, wait_until="networkidle")
                
                # Wait again for video player after reload
                page.wait_for_selector('#movie_player', timeout=15000)
                
            except Exception as e:
                print(f"Failed to load page: {e}")
                time.sleep(5)  # Keep browser open longer for debugging
                browser.close()
                return False
                
            # Check for cancellation after page load
            if cancel_check_callback and cancel_check_callback():
                print("Operation cancelled after page load")
                browser.close()
                return False
                
            try:
                # Simulate human-like behavior
                
                # 1. Sometimes adjust volume
                if random.random() > 0.7:  # 30% chance
                    volume_level = random.randint(30, 100)
                    page.evaluate(f"document.querySelector('video').volume = {volume_level/100}")
                
                # 2. Determine watch duration - more realistic
                if watch_duration is None:
                    # Get video duration if possible
                    try:
                        video_duration = page.evaluate("""
                            () => {
                                const video = document.querySelector('video');
                                return video ? video.duration : 0;
                            }
                        """)
                        
                        if video_duration > 0:
                            # Watch between 30% and 90% of the video
                            watch_percentage = random.uniform(0.3, 0.9)
                            watch_duration = int(video_duration * watch_percentage)
                            # Cap at 5 minutes for very long videos
                            watch_duration = min(watch_duration, 300)
                        else:
                            # Fallback if duration can't be determined
                            watch_duration = random.randint(15, 45)
                    except:
                        # Fallback if JavaScript fails
                        watch_duration = random.randint(15, 45)
                
                # For testing purposes, limit watch duration to make testing faster
                watch_duration = min(watch_duration, 30)
                
                # 3. Auto-scroll after page loads
                print("Auto-scrolling page...")
                # First scroll down to show comments
                page.evaluate("window.scrollBy(0, 600)")
                time.sleep(random.uniform(1, 3))
                
                # Then scroll back up to video
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(random.uniform(1, 2))
                
                # 4. Watch the video
                print(f"Watching for {watch_duration} seconds...")
                
                # Display progress during watching
                watch_start = time.time()
                progress_interval = max(1, watch_duration // 5)  # Show progress 5 times
                next_progress = progress_interval
                
                # Instead of just sleeping, check periodically if video is still playing
                while time.time() - watch_start < watch_duration:
                    # Check for cancellation during watching
                    if cancel_check_callback and cancel_check_callback():
                        print("Operation cancelled during watching")
                        browser.close()
                        return False
                        
                    elapsed = time.time() - watch_start
                    
                    # Show progress
                    if elapsed >= next_progress:
                        percent_complete = int((elapsed / watch_duration) * 100)
                        print(f"Watching progress: {percent_complete}% complete ({int(elapsed)}/{watch_duration} seconds)")
                        next_progress += progress_interval
                    
                    # Check if video is still playing every 5 seconds
                    if elapsed % 5 < 0.1:
                        try:
                            is_playing = page.evaluate("""
                                () => {
                                    const video = document.querySelector('video');
                                    return video && !video.paused && !video.ended && video.readyState > 2;
                                }
                            """)
                            
                            if not is_playing:
                                # Try to play if paused
                                page.evaluate("""
                                    () => {
                                        const video = document.querySelector('video');
                                        if (video && video.paused) video.play();
                                        
                                        // Also try clicking on the video player
                                        const player = document.querySelector('#movie_player');
                                        if (player) player.click();
                                    }
                                """)
                                print("Detected paused video - attempting to resume playback")
                        except Exception as e:
                            print(f"Error checking video playback: {str(e)}")
                    
                    # Sleep a short time
                    time.sleep(0.5)
                
                # No screenshot needed
                
                print("View simulated successfully.")
                
                # Keep browser open a bit longer so user can see it completed
                time.sleep(5)
                browser.close()
                return True
                
            except Exception as e:
                print(f"Error during view simulation: {str(e)}")
                # No screenshot needed
                time.sleep(5)  # Keep browser open longer for debugging
                if browser:
                    browser.close()
                return False
                
    except Exception as e:
        print(f"Error during operation: {str(e)}")
        if browser:
            try:
                browser.close()
            except:
                pass
        return False

# Function to process multiple views in parallel
def process_multiple_views(video_url, count, proxies=None, max_workers=2, cancel_check_callback=None):
    """
    Process multiple views in parallel
    
    Args:
        video_url: URL of the YouTube video
        count: Number of views to add
        proxies: Optional list of proxies to use
        max_workers: Maximum number of parallel workers
        cancel_check_callback: Optional callback function to check if operation should be cancelled
    """
    results = []
    
    def process_view(i):
        # Check for cancellation before starting this view
        if cancel_check_callback and cancel_check_callback():
            print(f"View {i+1}/{count} cancelled before starting")
            return False
            
        proxy = random.choice(proxies) if proxies else None
        print(f"\n➡ Adding view {i+1}/{count} {'using proxy ' + proxy if proxy else 'without proxy'}")
        
        # Pass the cancellation callback to add_view
        result = add_view(video_url, proxy, cancel_check_callback=cancel_check_callback)
        return result
    
    # Use a more controlled approach instead of executor.map to better handle cancellation
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_idx = {executor.submit(process_view, i): i for i in range(count)}
        
        # Process as they complete
        for future in future_to_idx:
            try:
                # Check for cancellation before waiting for result
                if cancel_check_callback and cancel_check_callback():
                    # Cancel any pending futures
                    for f in future_to_idx:
                        if not f.done():
                            f.cancel()
                    break
                
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing view: {str(e)}")
                results.append(False)
    
    return results

# CLI runner if script is executed directly
if __name__ == "__main__":
    video_url = input("📺 Enter the YouTube video URL: ").strip()
    use_proxy_input = input("🌐 Do you want to use a proxy? (yes/no): ").strip().lower()
    
    proxy = None
    if use_proxy_input == "yes":
        proxies = load_proxies()
        if proxies:
            proxy = get_random_proxy(proxies)
    
    add_view(video_url, proxy)
