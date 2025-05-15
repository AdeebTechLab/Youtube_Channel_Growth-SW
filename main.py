import os
import sys
import subprocess
import threading
import time
from liker import like_video, process_multiple_likes
from subscriber import subscribe_video
from viewer import add_view, process_multiple_views
from proxy_rotator import add_proxies, load_proxies, get_proxy_rotation_choice, select_proxies, get_random_proxy

def count_accounts():
    """Count available account cookie files"""
    if not os.path.exists("cookies"):
        os.makedirs("cookies", exist_ok=True)
        return 0
    return len([f for f in os.listdir("cookies") if f.endswith(".json")])

def get_account_name_by_index(i):
    """Get account name by index"""
    return f"account{i+1}"

def get_all_account_names(count):
    """Get all account names up to count"""
    return [get_account_name_by_index(i) for i in range(count)]

def add_account():
    """Launch the cookie saving process"""
    try:
        # Use Popen instead of run to avoid blocking the console
        subprocess.Popen(
            [sys.executable, "save_cookies.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except subprocess.CalledProcessError:
        print("❌ Error occurred while adding account.")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def show_progress(total, stop_event):
    """Show a simple progress animation"""
    chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    i = 0
    start_time = time.time()
    
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        timeformat = f"{mins:02d}:{secs:02d}"
        print(f"\r{chars[i]} Processing... Elapsed time: {timeformat}", end='', flush=True)
        i = (i + 1) % len(chars)
        time.sleep(0.1)
    
    print("\r✅ Processing complete!                      ")

def increase_likes():
    """Increase likes with optimized parallel processing"""
    video_url = input("📺 Enter the YouTube video URL: ").strip()
    available = count_accounts()
    
    if available == 0:
        print("❌ No accounts available. Please add accounts first.")
        return
        
    try:
        count = int(input(f"👍 How many accounts to like from? (Available: {available}): "))
        if count <= 0:
            print("❌ Please enter a positive number.")
            return
            
        if count > available:
            print(f"⚠️ Only {available} accounts available. Using all available accounts.")
            count = available

        use_proxies = input("🌐 Do you want to use proxies? (yes/no): ").strip().lower() == "yes"
        proxies = []
        if use_proxies:
            proxies = load_proxies()
            if not proxies:
                print("❌ No proxies available.")
                use_proxy_anyway = input("Continue without proxies? (yes/no): ").strip().lower()
                if use_proxy_anyway != "yes":
                    return
            elif get_proxy_rotation_choice():
                proxies = select_proxies(proxies)

        # Get account names
        accounts = get_all_account_names(count)
        
        # Determine optimal number of parallel processes
        max_workers = min(count, 2)  # Limit to 2 parallel processes to avoid overloading
        
        print(f"🚀 Starting like process with {max_workers} parallel workers...")
        
        # Create and start progress indicator
        stop_event = threading.Event()
        progress_thread = threading.Thread(target=show_progress, args=(count, stop_event))
        progress_thread.daemon = True
        progress_thread.start()
        
        # Process likes in parallel
        try:
            results = process_multiple_likes(accounts, video_url, proxies, max_workers)
            
            # Count successes
            successes = sum(1 for _, success in results if success)
            print(f"\n✅ Successfully liked with {successes} out of {count} accounts.")
            
        except Exception as e:
            print(f"\n❌ Error during processing: {str(e)}")
        finally:
            # Stop progress indicator
            stop_event.set()
            progress_thread.join(timeout=1.0)
            
    except ValueError:
        print("❌ Invalid number.")

def increase_subs():
    """Increase subscribers with optimized processing"""
    video_url = input("📺 Enter the YouTube video URL: ").strip()
    available = count_accounts()
    
    if available == 0:
        print("❌ No accounts available. Please add accounts first.")
        return
        
    try:
        count = int(input(f"👥 How many accounts to subscribe from? (Available: {available}): "))
        if count <= 0:
            print("❌ Please enter a positive number.")
            return
            
        if count > available:
            print(f"⚠️ Only {available} accounts available. Using all available accounts.")
            count = available

        use_proxies = input("🌐 Do you want to use proxies? (yes/no): ").strip().lower() == "yes"
        proxies = []
        if use_proxies:
            proxies = load_proxies()
            if not proxies:
                print("❌ No proxies available.")
                use_proxy_anyway = input("Continue without proxies? (yes/no): ").strip().lower()
                if use_proxy_anyway != "yes":
                    return
            elif get_proxy_rotation_choice():
                proxies = select_proxies(proxies)

        # Create and start progress indicator
        stop_event = threading.Event()
        progress_thread = threading.Thread(target=show_progress, args=(count, stop_event))
        progress_thread.daemon = True
        progress_thread.start()
        
        # Process subscriptions sequentially (more reliable)
        successes = 0
        try:
            for i in range(count):
                account = get_account_name_by_index(i)
                proxy = get_random_proxy(proxies) if proxies else None
                print(f"\n➡ Subscribing from {account} {'using proxy ' + proxy if proxy else 'without proxy'}")
                if subscribe_video(account, video_url, proxy):
                    successes += 1
                    
            print(f"\n✅ Successfully subscribed with {successes} out of {count} accounts.")
            
        except Exception as e:
            print(f"\n❌ Error during processing: {str(e)}")
        finally:
            # Stop progress indicator
            stop_event.set()
            progress_thread.join(timeout=1.0)
            
    except ValueError:
        print("❌ Invalid number.")

def add_views():
    """Add views with optimized parallel processing"""
    video_url = input("📺 Enter video URL: ").strip()
    try:
        count = int(input("👀 How many views to add?: "))
        if count <= 0:
            print("❌ Please enter a positive number.")
            return
            
        use_proxies = input("🌐 Do you want to use proxies? (yes/no): ").strip().lower() == "yes"
        proxies = []
        if use_proxies:
            proxies = load_proxies()
            if not proxies:
                print("❌ No proxies available.")
                use_proxy_anyway = input("Continue without proxies? (yes/no): ").strip().lower()
                if use_proxy_anyway != "yes":
                    return
            elif get_proxy_rotation_choice():
                proxies = select_proxies(proxies)

        # Determine optimal number of parallel processes
        max_workers = min(count, 2)  # Limit to 2 parallel processes to avoid overloading
        
        print(f"🚀 Starting view process with {max_workers} parallel workers...")
        
        # Create and start progress indicator
        stop_event = threading.Event()
        progress_thread = threading.Thread(target=show_progress, args=(count, stop_event))
        progress_thread.daemon = True
        progress_thread.start()
        
        # Process views in parallel
        try:
            results = process_multiple_views(video_url, count, proxies, max_workers)
            
            # Count successes
            successes = sum(1 for success in results if success)
            print(f"\n✅ Successfully added {successes} out of {count} views.")
            
        except Exception as e:
            print(f"\n❌ Error during processing: {str(e)}")
        finally:
            # Stop progress indicator
            stop_event.set()
            progress_thread.join(timeout=1.0)
            
    except ValueError:
        print("❌ Invalid number.")

def check_system():
    """Check system requirements and setup"""
    # Ensure cookies directory exists
    os.makedirs("cookies", exist_ok=True)
    
    # Check if playwright is installed
    try:
        import playwright
        print("✅ Playwright is installed.")
    except ImportError:
        print("❌ Playwright is not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            print("✅ Playwright installed successfully.")
        except Exception as e:
            print(f"❌ Failed to install Playwright: {str(e)}")
            print("Please install manually with: pip install playwright && playwright install chromium")
    
    # Check for proxies file
    if not os.path.exists("proxies.txt"):
        with open("proxies.txt", "w") as f:
            pass
        print("📁 Created empty proxies.txt file")

def main_menu():
    """Main application menu with improved UI"""
    check_system()
    
    while True:
        print("\n" + "="*50)
        print("📺 YouTube Automation Menu 📺".center(50))
        print("="*50)
        print("< - 1 - > Add YouTube Account (Manual Login)")
        print("< - 2 - > Batch Add Accounts (Email:Password List)")
        print("< - 3 - > Increase Likes")
        print("< - 4 - > Increase Subscribers")
        print("< - 5 - > Increase Views")
        print("< - 6 - > Add Proxies to File")
        print("< - 7 - > Configure Proxy API")
        print("< - 8 - > Exit")
        print("-"*50)
        
        accounts = count_accounts()
        proxies = len(load_proxies())
        print(f"ℹ️ Status: {accounts} accounts, {proxies} proxies available")
        print("-"*50)

        choice = input("Choose an option (1-8): ").strip()

        if choice == "1":
            add_account()
        elif choice == "2":
            batch_add_accounts()
        elif choice == "3":
            increase_likes()
        elif choice == "4":
            increase_subs()
        elif choice == "5":
            add_views()
        elif choice == "6":
            add_proxies()
        elif choice == "7":
            configure_proxy_api()
        elif choice == "8":
            print("👋 Exiting. Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select a number between 1 and 8.")

def batch_add_accounts():
    """Launch the batch account login process"""
    try:
        # Use Popen instead of run to avoid blocking the console
        subprocess.Popen(
            [sys.executable, "save_cookies.py", "--batch"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except subprocess.CalledProcessError:
        print("❌ Error occurred while launching batch account login.")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def configure_proxy_api():
    """Configure proxy API settings"""
    from proxy_rotator import save_proxy_api_config, fetch_proxies_from_api
    
    print("\n" + "="*50)
    print("🌐 Proxy API Configuration 🌐".center(50))
    print("="*50)
    
    api_url = input("Enter proxy API URL: ").strip()
    if not api_url:
        print("❌ API URL cannot be empty.")
        return
        
    api_key = input("Enter API key (optional, press Enter to skip): ").strip()
    
    # Save configuration
    save_proxy_api_config(api_url, api_key)
    
    # Test the API
    print("Testing API connection...")
    proxies = fetch_proxies_from_api()
    
    if proxies:
        print(f"✅ Successfully fetched {len(proxies)} proxies from API.")
    else:
        print("❌ Failed to fetch proxies from API. Please check your configuration.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
    finally:
        print("\nProgram completed. You can close this window.")
        input("Press Enter to exit...")
