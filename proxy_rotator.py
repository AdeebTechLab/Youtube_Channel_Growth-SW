import os
import random
import requests
import json

PROXY_FILE = "proxies.txt"
PROXY_API_CONFIG = "proxy_api_config.json"

def add_proxies():
    print("Enter proxies in the format 'http://ip:port'. Type 'done' when finished.")
    with open(PROXY_FILE, "a") as f:
        while True:
            proxy = input("Enter proxy: ").strip()
            if proxy.lower() == "done":
                break
            if proxy:
                f.write(proxy + "\n")
    print("✅ Proxies added successfully.")

def save_proxy_api_config(api_url, api_key=None, params=None):
    """Save proxy API configuration to a file"""
    config = {
        "api_url": api_url,
        "api_key": api_key,
        "params": params or {}
    }
    with open(PROXY_API_CONFIG, "w") as f:
        json.dump(config, f, indent=4)
    print("✅ Proxy API configuration saved successfully.")

def load_proxy_api_config():
    """Load proxy API configuration from file"""
    if not os.path.exists(PROXY_API_CONFIG):
        return None
    try:
        with open(PROXY_API_CONFIG, "r") as f:
            return json.load(f)
    except:
        return None
        
def remove_proxy_api_config():
    """Remove proxy API configuration file"""
    if os.path.exists(PROXY_API_CONFIG):
        try:
            os.remove(PROXY_API_CONFIG)
            print("✅ Proxy API configuration removed successfully.")
            return True
        except Exception as e:
            print(f"❌ Error removing proxy API configuration: {str(e)}")
            return False
    else:
        print("❌ No proxy API configuration found.")
        return False

def fetch_proxies_from_api():
    """Fetch proxies from the configured API"""
    config = load_proxy_api_config()
    if not config or not config.get("api_url"):
        print("❌ No proxy API configured.")
        return []
    
    try:
        headers = {}
        if config.get("api_key"):
            headers["Authorization"] = f"Bearer {config['api_key']}"
        
        response = requests.get(
            config["api_url"], 
            headers=headers,
            params=config.get("params", {})
        )
        
        if response.status_code != 200:
            print(f"❌ API request failed with status code {response.status_code}")
            return []
        
        # Try to parse the response as JSON
        try:
            data = response.json()
            # Extract proxies from the response - adjust this based on your API's response format
            proxies = []
            if isinstance(data, list):
                # If the API returns a list of proxies directly
                proxies = [f"http://{p}" if not p.startswith('http') else p for p in data]
            elif isinstance(data, dict) and "proxies" in data:
                # If the API returns a dict with a "proxies" key
                proxy_list = data["proxies"]
                if isinstance(proxy_list, list):
                    proxies = [f"http://{p}" if not p.startswith('http') else p for p in proxy_list]
            
            print(f"✅ Fetched {len(proxies)} proxies from API.")
            return proxies
        except:
            # If JSON parsing fails, try to parse as text (one proxy per line)
            proxies = [line.strip() for line in response.text.split('\n') if line.strip()]
            proxies = [f"http://{p}" if not p.startswith('http') else p for p in proxies]
            print(f"✅ Fetched {len(proxies)} proxies from API.")
            return proxies
    except Exception as e:
        print(f"❌ Error fetching proxies from API: {str(e)}")
        return []

def load_proxies():
    """Load proxies from file or API based on configuration"""
    # First try to load from API
    api_config = load_proxy_api_config()
    if api_config and api_config.get("api_url"):
        api_proxies = fetch_proxies_from_api()
        if api_proxies:
            return api_proxies
    
    # Fall back to file if API fails or not configured
    if not os.path.exists(PROXY_FILE):
        print("❌ No proxies found. Please add proxies first.")
        return []
    with open(PROXY_FILE, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies

def get_proxy_rotation_choice():
    while True:
        choice = input("Do you want to use proxy rotation? (yes/no): ").strip().lower()
        if choice in ["yes", "no"]:
            return choice == "yes"
        print("Please enter 'yes' or 'no'.")

def select_proxies(proxies):
    print(f"Available proxies ({len(proxies)}):")
    for idx, proxy in enumerate(proxies, 1):
        print(f"{idx}. {proxy}")
    while True:
        count = input(f"How many proxies do you want to use? (1-{len(proxies)}): ").strip()
        if count.isdigit() and 1 <= int(count) <= len(proxies):
            return proxies[:int(count)]
        print("Invalid input. Please enter a valid number.")

def get_random_proxy(proxies):
    return random.choice(proxies) if proxies else None
