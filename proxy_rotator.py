import os
import random

PROXY_FILE = "proxies.txt"

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

def load_proxies():
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
    return random.choice(proxies)
