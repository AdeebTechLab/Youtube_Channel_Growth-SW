import os
import sys

os.environ["KIVY_TEXT"] = "pil"

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import subprocess
from kivy.clock import Clock
import threading
import time
import random
import json
import os
from proxy_rotator import load_proxies, get_random_proxy

# Add this to the existing imports at the top

# Define color palette (same as main_ui.py for consistency)
COLORS = {
    'primary': '#4a6cd4',
    'primary_light': '#7b9ff7',
    'primary_dark': '#1a40a2',
    'accent': '#ff5252',
    'accent_light': '#ff867f',
    'accent_dark': '#c50e29',
    'background': '#f5f5f7',
    'card': '#ffffff',
    'text': '#212121',
    'text_secondary': '#757575',
    'subscribers': '#ffcdd2',
    'subscribers_active': '#f44336',
    'likes': '#bbdefb',
    'likes_active': '#2196f3',
    'views': '#c8e6c9',
    'views_active': '#4caf50',
}

# KV string with consistent styling from main UI
kv = """
#:import get_color_from_hex kivy.utils.get_color_from_hex
#:import dp kivy.metrics.dp

<RoundedButton>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: self.background_color if self.background_color else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]

<AccountManagerScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: get_color_from_hex(app.colors['background'])
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Top navigation bar
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            
            RoundedButton:
                text: "Back to Bot"
                size_hint_x: 0.3
                background_color: get_color_from_hex(app.colors['primary'])
                color: 1, 1, 1, 1
                bold: True
                on_release: root.back_to_main()
            
            Widget:
                size_hint_x: 0.7
            
            RoundedButton:
                text: "Add Accounts"
                size_hint_x: 0.3
                background_color: get_color_from_hex(app.colors['accent'])
                color: 1, 1, 1, 1
                bold: True
                on_release: root.add_accounts()
        
        # Heading
        Label:
            text: "Account & Proxy Management"
            font_size: dp(28)
            color: get_color_from_hex(app.colors['accent'])
            size_hint_y: None
            height: dp(50)
            bold: True
            
        Label:
            text: "Manage your YouTube accounts and proxies"
            font_size: dp(16)
            color: get_color_from_hex(app.colors['text_secondary'])
            size_hint_y: None
            height: dp(30)
            
        # Count display area
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            spacing: dp(20)
            
            Label:
                id: accounts_count_label
                text: "Total Accounts: 0"
                font_size: dp(14)
                color: get_color_from_hex(app.colors['primary'])
                bold: True
                size_hint_x: 0.5
                halign: 'left'
                text_size: self.size
                
            Label:
                id: proxies_count_label
                text: "Total Proxies: 0"
                font_size: dp(14)
                color: get_color_from_hex(app.colors['primary'])
                bold: True
                size_hint_x: 0.5
                halign: 'right'
                text_size: self.size
            
        # Tabs for Accounts and Proxies
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            
            RoundedButton:
                text: "Accounts"
                background_color: get_color_from_hex(app.colors['primary_dark'] if root.current_tab == 'accounts' else app.colors['card'])
                color: (1, 1, 1, 1) if root.current_tab == 'accounts' else get_color_from_hex(app.colors['primary'])
                font_size: dp(18)
                bold: True
                on_release: root.switch_tab('accounts')

            RoundedButton:
                text: "Proxies"
                background_color: get_color_from_hex(app.colors['primary_dark'] if root.current_tab == 'proxies' else app.colors['card'])
                color: (1, 1, 1, 1) if root.current_tab == 'proxies' else get_color_from_hex(app.colors['primary'])
                font_size: dp(18)
                bold: True
                on_release: root.switch_tab('proxies')
        
        # Content area
        BoxLayout:
            id: content_area
            orientation: 'vertical'
            padding: dp(15)
            canvas.before:
                Color:
                    rgba: get_color_from_hex(app.colors['card'])
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(10)]

<AccountsTab>:
    orientation: 'vertical'
    spacing: dp(15)
    
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(10)
        
        Label:
            text: "Available Accounts"
            font_size: dp(18)
            color: get_color_from_hex(app.colors['primary'])
            size_hint_x: 0.7
            bold: True
            halign: 'left'
            text_size: self.size
        
        RoundedButton:
            text: "Delete All"
            size_hint_x: 0.3
            background_color: get_color_from_hex(app.colors['accent_dark'])
            color: 1, 1, 1, 1
            font_size: dp(14)
            bold: True
            on_release: root.delete_all_accounts()
    
    ScrollView:
        do_scroll_x: False
        effect_cls: 'ScrollEffect'  # Smoother scrolling
        bar_width: dp(10)
        
        GridLayout:
            id: accounts_grid
            cols: 1
            spacing: dp(4)
            padding: dp(5)
            size_hint_y: None
            height: self.minimum_height

<ProxiesTab>:
    orientation: 'vertical'
    spacing: dp(15)
    
    TabbedPanel:
        do_default_tab: False
        tab_width: self.width / 2
        background_color: get_color_from_hex(app.colors['background'])
        
        TabbedPanelItem:
            text: "Manual Proxies"
            background_color: get_color_from_hex(app.colors['primary'])
            color: 1, 1, 1, 1
            
            BoxLayout:
                orientation: 'vertical'
                spacing: dp(15)
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: get_color_from_hex(app.colors['card'])
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(10)
                    
                    TextInput:
                        id: proxy_input
                        hint_text: "Enter proxy (http://ip:port)"
                        multiline: False
                        size_hint_x: 0.5
                        padding: [dp(10), dp(10), dp(10), dp(10)]
                        font_size: dp(16)
                        background_color: get_color_from_hex(app.colors['background'])
                        foreground_color: get_color_from_hex(app.colors['text'])
                        cursor_color: get_color_from_hex(app.colors['primary'])
                    
                    RoundedButton:
                        text: "Add Proxy"
                        size_hint_x: 0.25
                        background_color: get_color_from_hex(app.colors['primary'])
                        color: 1, 1, 1, 1
                        font_size: dp(16)
                        bold: True
                        on_release: root.add_proxy()
                    
                    RoundedButton:
                        text: "Bulk Add"
                        size_hint_x: 0.25
                        background_color: get_color_from_hex(app.colors['accent'])
                        color: 1, 1, 1, 1
                        font_size: dp(16)
                        bold: True
                        on_release: root.add_bulk_proxies()
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    spacing: dp(10)
                    
                    Label:
                        text: "Available Proxies"
                        font_size: dp(18)
                        color: get_color_from_hex(app.colors['primary'])
                        size_hint_x: 0.7
                        bold: True
                        halign: 'left'
                        text_size: self.size
                    
                    RoundedButton:
                        text: "Delete All"
                        size_hint_x: 0.3
                        background_color: get_color_from_hex(app.colors['accent_dark'])
                        color: 1, 1, 1, 1
                        font_size: dp(14)
                        bold: True
                        on_release: root.delete_all_proxies()
                
                ScrollView:
                    do_scroll_x: False
                    effect_cls: 'ScrollEffect'  # Smoother scrolling
                    bar_width: dp(10)
                    
                    GridLayout:
                        id: proxies_grid
                        cols: 1
                        spacing: dp(4)
                        padding: dp(5)
                        size_hint_y: None
                        height: self.minimum_height
        
        TabbedPanelItem:
            text: "Proxy API"
            background_color: get_color_from_hex(app.colors['primary'])
            color: 1, 1, 1, 1
            
            BoxLayout:
                orientation: 'vertical'
                spacing: dp(15)
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: get_color_from_hex(app.colors['card'])
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                Label:
                    text: "Proxy API Configuration"
                    font_size: dp(18)
                    color: get_color_from_hex(app.colors['primary'])
                    size_hint_y: None
                    height: dp(30)
                    bold: True
                
                Label:
                    text: "Configure an API endpoint to automatically fetch proxies"
                    font_size: dp(14)
                    color: get_color_from_hex(app.colors['text_secondary'])
                    size_hint_y: None
                    height: dp(30)
                    italic: True
                
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(160)
                    spacing: dp(10)
                    
                    Label:
                        text: "API URL"
                        size_hint_y: None
                        height: dp(20)
                        halign: 'left'
                        text_size: self.size
                        color: get_color_from_hex(app.colors['text'])
                    
                    TextInput:
                        id: api_url_input
                        hint_text: "Enter proxy API URL (e.g., https://example.com/api/proxies)"
                        multiline: False
                        size_hint_y: None
                        height: dp(50)
                        padding: [dp(10), dp(10), dp(10), dp(10)]
                        font_size: dp(16)
                        background_color: get_color_from_hex(app.colors['background'])
                        foreground_color: get_color_from_hex(app.colors['text'])
                        cursor_color: get_color_from_hex(app.colors['primary'])
                    
                    Label:
                        text: "API Key (Optional)"
                        size_hint_y: None
                        height: dp(20)
                        halign: 'left'
                        text_size: self.size
                        color: get_color_from_hex(app.colors['text'])
                    
                    TextInput:
                        id: api_key_input
                        hint_text: "Enter API key if required"
                        multiline: False
                        size_hint_y: None
                        height: dp(50)
                        padding: [dp(10), dp(10), dp(10), dp(10)]
                        font_size: dp(16)
                        background_color: get_color_from_hex(app.colors['background'])
                        foreground_color: get_color_from_hex(app.colors['text'])
                        cursor_color: get_color_from_hex(app.colors['primary'])
                        password: True
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(10)
                    
                    RoundedButton:
                        text: "Save Configuration"
                        size_hint_x: 0.33
                        background_color: get_color_from_hex(app.colors['primary'])
                        color: 1, 1, 1, 1
                        font_size: dp(16)
                        bold: True
                        on_release: root.save_api_config()
                    
                    RoundedButton:
                        text: "Test API"
                        size_hint_x: 0.33
                        background_color: get_color_from_hex(app.colors['accent'])
                        color: 1, 1, 1, 1
                        font_size: dp(16)
                        bold: True
                        on_release: root.test_api()
                        
                    RoundedButton:
                        text: "Remove API"
                        size_hint_x: 0.33
                        background_color: get_color_from_hex(app.colors['accent_dark'])
                        color: 1, 1, 1, 1
                        font_size: dp(16)
                        bold: True
                        on_release: root.remove_api_config()
"""

# Load the KV string when the module is imported
Builder.load_string(kv)


class BulkAccountPopup(Popup):
    def __init__(self, callback, **kwargs):
        self.callback = callback
        
        # Create content layout
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        # Add instructions
        instructions = Label(
            text="Paste your Gmail accounts below (one per line)\nFormat: email:password or email,password",
            size_hint_y=None,
            height=dp(40),
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        content.add_widget(instructions)
        
        # Add text input for accounts with larger height for bulk pasting
        self.accounts_input = TextInput(
            hint_text="Paste accounts here...",
            multiline=True,
            size_hint=(1, 1),  # Take all available space
            font_size=dp(14)
        )
        content.add_widget(self.accounts_input)
        
        # Add buttons
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = Button(
            text="Cancel",
            size_hint_x=0.5,
            background_color=get_color_from_hex(COLORS['text_secondary']),
            color=(1, 1, 1, 1)
        )
        cancel_btn.bind(on_release=self.dismiss)
        
        process_btn = Button(
            text="Add Accounts",
            size_hint_x=0.5,
            background_color=get_color_from_hex(COLORS['accent']),
            color=(1, 1, 1, 1)
        )
        process_btn.bind(on_release=self.process_accounts)
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(process_btn)
        content.add_widget(buttons)
        
        # Configure popup
        super(BulkAccountPopup, self).__init__(
            title="Add Bulk Accounts",
            content=content,
            size_hint=(0.9, 0.8),  # Make it larger for bulk pasting
            auto_dismiss=False,
            **kwargs
        )
    
    def process_accounts(self, instance):
        accounts_text = self.accounts_input.text.strip()
        if not accounts_text:
            error_popup = Popup(
                title="Error",
                content=Label(text="Please paste at least one account"),
                size_hint=(0.6, None),
                height=dp(200)
            )
            error_popup.open()
            return
        
        # Parse accounts
        accounts = []
        for line in accounts_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Support both colon and comma as separators
            if ':' in line:
                email, password = line.split(':', 1)
            elif ',' in line:
                email, password = line.split(',', 1)
            else:
                continue
                
            accounts.append({
                'email': email.strip(),
                'password': password.strip()
            })
        
        if not accounts:
            error_popup = Popup(
                title="Error",
                content=Label(text="No valid accounts found. Use format email:password"),
                size_hint=(0.6, None),
                height=dp(200)
            )
            error_popup.open()
            return
        
        # Close this popup
        self.dismiss()
        
        # Start the bulk processing with progress popup
        self.callback(accounts)

class BulkProgressPopup(Popup):
    def __init__(self, accounts, callback, **kwargs):
        self.accounts = accounts
        self.callback = callback
        self.should_cancel = False
        
        # Create content layout
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        # Add status label
        self.status_label = Label(
            text=f"Processing 0/{len(accounts)} accounts...",
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(self.status_label)
        
        # Add current account label
        self.current_label = Label(
            text="",
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(self.current_label)
        
        # Add scrollable log
        scroll = ScrollView(do_scroll_x=False)
        self.log_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(5)
        )
        self.log_container.bind(minimum_height=self.log_container.setter('height'))
        scroll.add_widget(self.log_container)
        content.add_widget(scroll)
        
        # Add buttons
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        self.cancel_btn = Button(
            text="Cancel",
            size_hint_x=0.5,
            background_color=get_color_from_hex(COLORS['accent']),
            color=(1, 1, 1, 1)
        )
        self.cancel_btn.bind(on_release=self.cancel_operation)
        
        self.close_btn = Button(
            text="Close",
            size_hint_x=0.5,
            background_color=get_color_from_hex(COLORS['primary']),
            color=(1, 1, 1, 1),
            disabled=True
        )
        self.close_btn.bind(on_release=self.dismiss)
        
        buttons.add_widget(self.cancel_btn)
        buttons.add_widget(self.close_btn)
        content.add_widget(buttons)
        
        # Configure popup
        super(BulkProgressPopup, self).__init__(
            title="Processing Accounts",
            content=content,
            size_hint=(0.8, 0.8),
            auto_dismiss=False,
            **kwargs
        )
        
        # Start processing in a background thread
        self.success_count = 0
        self.skipped_count = 0
        self.thread = threading.Thread(target=self.process_accounts)
        self.thread.daemon = True
        self.thread.start()
    
    def add_log(self, message, success=None):
        def _add_log(dt):
            log_entry = BoxLayout(
                size_hint_y=None,
                height=dp(30),
                padding=[dp(5), dp(2)]
            )
            
            # Add color indicator based on success status
            if success is not None:
                color = COLORS['views_active'] if success else COLORS['accent']
                with log_entry.canvas.before:
                    Color(rgba=get_color_from_hex(color))
                    Rectangle(pos=(log_entry.x, log_entry.y), size=(dp(5), log_entry.height))
            
            # Add message label
            label = Label(
                text=message,
                halign='left',
                valign='middle',
                text_size=(None, None)
            )
            log_entry.add_widget(label)
            
            self.log_container.add_widget(log_entry)
        
        Clock.schedule_once(_add_log)
    
    def update_status(self, index, total, message=""):
        def _update(dt):
            self.status_label.text = f"Processing {index+1}/{total} accounts..."
            if message:
                self.current_label.text = message
        
        Clock.schedule_once(_update)
    
    def cancel_operation(self, instance=None):
        self.should_cancel = True
        self.cancel_btn.disabled = True
        self.cancel_btn.text = "Cancelling..."
        self.add_log("Cancelling operation... (will complete current account)")
    
    def complete(self):
        def _complete(dt):
            self.status_label.text = f"Completed: {self.success_count} added, {self.skipped_count} skipped, {len(self.accounts) - self.success_count - self.skipped_count} failed"
            self.current_label.text = "Operation complete"
            self.cancel_btn.disabled = True
            self.close_btn.disabled = False
            # Call the callback to refresh the account list
            self.callback()
        
        Clock.schedule_once(_complete)
    
    def process_accounts(self):
        """Process accounts in a background thread"""
        from playwright.sync_api import sync_playwright
        
        # Get existing accounts to check for duplicates
        existing_accounts = []
        if os.path.exists("account_emails.txt"):
            with open("account_emails.txt", "r") as f:
                existing_accounts = [line.strip() for line in f if line.strip()]
        
        # Create account_emails.txt if it doesn't exist
        if not os.path.exists("account_emails.txt"):
            with open("account_emails.txt", "w") as f:
                pass
        
        # Create a log file for this batch
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_dir = "account_logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"bulk_accounts_{timestamp}.txt")
        
        with open(log_file, "w") as f:
            f.write(f"Bulk Account Processing - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total accounts to process: {len(self.accounts)}\n")
            f.write("-" * 50 + "\n\n")
        
        for i, account in enumerate(self.accounts):
            if self.should_cancel:
                break
            
            email = account['email']
            
            # Check if account already exists
            if email in existing_accounts:
                self.add_log(f"Skipping {email} - already exists", None)
                with open(log_file, "a") as f:
                    f.write(f"Account {i+1}/{len(self.accounts)}: {email} - SKIPPED (already exists)\n\n")
                self.skipped_count += 1
                continue
            
            # Get username from email (part before @)
            username = email.split('@')[0]
            # Replace any invalid characters for filenames
            username = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in username)
            account_name = username
            
            # Check if this username already exists as a file
            if os.path.exists(f"cookies/{account_name}.json"):
                # If it exists, append a number
                count = 1
                while os.path.exists(f"cookies/{account_name}_{count}.json"):
                    count += 1
                account_name = f"{username}_{count}"
            
            cookie_file = f"cookies/{account_name}.json"
            
            # Update status
            self.update_status(i, len(self.accounts), f"Processing: {email}")
            
            # Add log entry
            self.add_log(f"Starting login for {email}")
            
            # Log to file
            with open(log_file, "a") as f:
                f.write(f"Account {i+1}/{len(self.accounts)}: {email}\n")
            
            try:
                with sync_playwright() as p:
                    # Configure browser launch options
                    browser_args = {
                        "headless": True,  # Run headless for UI integration
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
                    
                    # Launch browser
                    browser = p.chromium.launch(**browser_args)
                    context = browser.new_context(viewport={'width': 1280, 'height': 800})
                    page = context.new_page()
                    
                    # Navigate to Google sign-in
                    self.add_log(f"Opening Google login page for {email}")
                    page.goto("https://accounts.google.com/signin/v2/identifier?service=youtube")
                    
                    # Enter email
                    self.add_log(f"Entering email for {email}")
                    page.fill('input[type="email"]', email)
                    page.click('button:has-text("Next")')
                    
                    # Wait for password field and enter password
                    try:
                        page.wait_for_selector('input[type="password"]', timeout=10000)
                        self.add_log(f"Entering password for {email}")
                        page.fill('input[type="password"]', account['password'])
                        page.click('button:has-text("Next")')
                    except Exception as e:
                        error_msg = f"Error entering password: {str(e)}"
                        self.add_log(error_msg, False)
                        with open(log_file, "a") as f:
                            f.write(f"  FAILED: {error_msg}\n\n")
                        browser.close()
                        continue
                    
                    # Wait for login to complete
                    max_wait = 30  # Maximum wait time in seconds
                    start_time = time.time()
                    logged_in = False
                    
                    while time.time() - start_time < max_wait:
                        try:
                            # Navigate to YouTube to verify login
                            page.goto("https://www.youtube.com")
                            time.sleep(3)  # Give time for the page to load
                            
                            # Check login status
                            cookies = context.cookies()
                            logged_in = any("LOGIN_INFO" in cookie['name'] or "SID" in cookie['name'] for cookie in cookies)
                            
                            # Double-check by looking for avatar element
                            if not logged_in:
                                logged_in = page.query_selector('ytd-topbar-menu-button-renderer.ytd-masthead') is not None
                                
                            if logged_in:
                                break
                                
                            self.add_log(f"Login not detected yet for {email}. Waiting...")
                            time.sleep(3)
                        except Exception as e:
                            self.add_log(f"Error checking login status: {str(e)}")
                            time.sleep(3)
                    
                    if logged_in:
                        # Save cookies
                        cookies = context.cookies()
                        with open(cookie_file, "w") as f:
                            json.dump(cookies, f)
                        
                        # Add email to existing accounts list
                        with open("account_emails.txt", "a") as f:
                            f.write(email + "\n")
                        
                        # Add to existing accounts list in memory
                        existing_accounts.append(email)
                        
                        success_msg = f"SUCCESS: Cookies saved for {email} as {account_name}"
                        self.add_log(success_msg, True)
                        with open(log_file, "a") as f:
                            f.write(f"  SUCCESS: Saved as {account_name}\n\n")
                        self.success_count += 1
                    else:
                        error_msg = f"ERROR: Login failed for {email}"
                        self.add_log(error_msg, False)
                        with open(log_file, "a") as f:
                            f.write(f"  FAILED: Login failed\n\n")
                    
                    browser.close()
                    
            except Exception as e:
                error_msg = f"Error processing {email}: {str(e)}"
                self.add_log(error_msg, False)
                with open(log_file, "a") as f:
                    f.write(f"  FAILED: {error_msg}\n\n")
            
            # Add a delay between accounts to avoid triggering security measures
            if i < len(self.accounts) - 1 and not self.should_cancel:
                delay = random.randint(1, 3)  # Shorter delay for bulk processing
                self.add_log(f"Waiting {delay} seconds before next account...")
                time.sleep(delay)
        
        # Write summary to log file
        with open(log_file, "a") as f:
            f.write("\n" + "-" * 50 + "\n")
            f.write(f"Processing completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Successfully processed: {self.success_count}/{len(self.accounts)} accounts\n")
            f.write(f"Skipped (already exist): {self.skipped_count}/{len(self.accounts)} accounts\n")
            if self.should_cancel:
                f.write("Operation was cancelled by user\n")
        
        # Complete the operation
        self.complete()

class AccountManagerScreen(Screen):
    current_tab = StringProperty("accounts")

    def __init__(self, **kwargs):
        super(AccountManagerScreen, self).__init__(**kwargs)
        self.accounts_tab = AccountsTab()
        self.proxies_tab = ProxiesTab()
        Clock.schedule_once(self._init_ui, 0)

    def _init_ui(self, dt):
        if hasattr(self, "ids") and "content_area" in self.ids:
            self.switch_tab("accounts")
        else:
            # If the widget is not yet ready, try again after a short delay
            Clock.schedule_once(self._init_ui, 0.1)

    def switch_tab(self, tab_name):
        self.current_tab = tab_name
        if hasattr(self, "ids") and "content_area" in self.ids:
            content_area = self.ids.content_area
            content_area.clear_widgets()

            if tab_name == "accounts":
                content_area.add_widget(self.accounts_tab)
                # Update account count
                if os.path.exists("cookies"):
                    account_count = len([f for f in os.listdir("cookies") if f.endswith(".json")])
                    if hasattr(self, "ids") and "accounts_count_label" in self.ids:
                        self.ids.accounts_count_label.text = f"Total Accounts: {account_count}"
                        print(f"Updated account count on tab switch: {account_count}")
            elif tab_name == "proxies":
                content_area.add_widget(self.proxies_tab)
                # Update proxy count
                if os.path.exists("proxies.txt"):
                    try:
                        with open("proxies.txt", "r") as f:
                            lines = f.readlines()
                            proxy_count = sum(1 for line in lines if line.strip())
                            if hasattr(self, "ids") and "proxies_count_label" in self.ids:
                                self.ids.proxies_count_label.text = f"Total Proxies: {proxy_count}"
                                print(f"Updated proxy count on tab switch: {proxy_count}")
                    except Exception as e:
                        print(f"Error counting proxies on tab switch: {e}")

    def back_to_main(self):
        self.manager.current = "main"

    def add_accounts(self):
        # Open the bulk account popup
        popup = BulkAccountPopup(callback=self.start_bulk_processing)
        popup.open()
    
    def start_bulk_processing(self, accounts):
        # Start the bulk processing with progress popup
        progress_popup = BulkProgressPopup(
            accounts=accounts,
            callback=self.accounts_tab.load_accounts
        )
        progress_popup.open()
        
    def on_enter(self):
        # This is called when the screen is entered
        # Ensure tabs are properly initialized
        Clock.schedule_once(self._init_ui, 0)
        
        # Update the count displays
        Clock.schedule_once(self._update_counts, 0.5)
        
    def _update_counts(self, dt):
        try:
            # Update account count
            account_count = 0
            if os.path.exists("cookies"):
                account_count = len([f for f in os.listdir("cookies") if f.endswith(".json")])
            
            if hasattr(self, "ids") and "accounts_count_label" in self.ids:
                self.ids.accounts_count_label.text = f"Total Accounts: {account_count}"
                
            # Update proxy count - direct approach
            proxy_count = 0
            if os.path.exists("proxies.txt"):
                try:
                    with open("proxies.txt", "r") as f:
                        lines = f.readlines()
                        proxy_count = sum(1 for line in lines if line.strip())
                except Exception as e:
                    print(f"Error counting proxies: {e}")
                    
            # Make sure to update the label
            if hasattr(self, "ids") and "proxies_count_label" in self.ids:
                self.ids.proxies_count_label.text = f"Total Proxies: {proxy_count}"
                
            print(f"Updated counts - Accounts: {account_count}, Proxies: {proxy_count}")
        except Exception as e:
            print(f"Error in _update_counts: {e}")
            import traceback
            traceback.print_exc()


class AccountsTab(BoxLayout):
    def __init__(self, **kwargs):
        super(AccountsTab, self).__init__(**kwargs)
        Clock.schedule_once(self._init_ui, 0)

    def _init_ui(self, dt):
        self.load_accounts()

    def load_accounts(self):
        if not hasattr(self, "ids") or "accounts_grid" not in self.ids:
            return

        accounts_grid = self.ids.accounts_grid
        accounts_grid.clear_widgets()

        if not os.path.exists("cookies"):
            os.makedirs("cookies", exist_ok=True)
            return

        # Load accounts directly without threading or loading indicators
        self._load_accounts_direct()
        
    def _load_accounts_direct(self):
        try:
            if not hasattr(self, "ids") or "accounts_grid" not in self.ids:
                return
                
            accounts_grid = self.ids.accounts_grid
            
            # Get all account files
            account_files = [f for f in os.listdir("cookies") if f.endswith(".json")]
            total_accounts = len(account_files)
            
            # Update the count display immediately
            if hasattr(self, "parent") and hasattr(self.parent, "ids") and "accounts_count_label" in self.parent.ids:
                self.parent.ids.accounts_count_label.text = f"Total Accounts: {total_accounts}"
            
            # If no accounts, show a message
            if not account_files:
                no_accounts_label = Label(
                    text="No accounts available. Add some using the 'Add Accounts' button.",
                    color=get_color_from_hex(COLORS['text_secondary']),
                    size_hint_y=None,
                    height=dp(50)
                )
                accounts_grid.add_widget(no_accounts_label)
                return
            
            # Load email mapping if available - do this once outside the loop
            email_mapping = {}
            if os.path.exists("account_emails.txt"):
                try:
                    with open("account_emails.txt", "r") as f:
                        for line in f:
                            line = line.strip()
                            if '@' in line:
                                username = line.split('@')[0]
                                username = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in username)
                                email_mapping[username] = line
                except Exception as e:
                    print(f"Error loading email mapping: {e}")
            
            # Pre-create the Factory reference outside the loop
            from kivy.factory import Factory
            RoundedButton = Factory.RoundedButton
            
            # Create a simplified grid layout with just text and buttons
            for account_file in account_files:
                account_name = account_file.replace(".json", "")
                
                # Get email if available, otherwise use account name
                display_text = account_name
                
                # Try to match with email mapping - simplified lookup
                base_username = account_name.split('_')[0] if '_' in account_name else account_name
                if base_username in email_mapping:
                    display_text = email_mapping[base_username]
                
                # Limit display text length to prevent overflow
                if len(display_text) > 20:
                    display_text = display_text[:17] + "..."
                
                # Create a simpler layout for each account
                card = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(5)
                )
                
                # Account name label
                label = Label(
                    text=display_text,
                    size_hint_x=0.7,
                    color=get_color_from_hex(COLORS["text"]),
                    font_size=dp(12),
                    halign='left',
                    text_size=(None, None)
                )
                card.add_widget(label)

                # Delete button
                delete_btn = Button(
                    text="Delete",
                    size_hint_x=0.3,
                    background_color=get_color_from_hex(COLORS["accent"]),
                    color=(1, 1, 1, 1),
                    font_size=dp(12)
                )
                delete_btn.account_name = account_name  # Store account name as attribute
                delete_btn.bind(on_release=self.delete_account)
                card.add_widget(delete_btn)
                
                accounts_grid.add_widget(card)
            
        except Exception as e:
            print(f"Error loading accounts: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_account_count(self, count):
        """Update the account count display"""
        try:
            # Try to find the count label in the parent screen
            if hasattr(self, "parent") and hasattr(self.parent, "ids"):
                if "accounts_count_label" in self.parent.ids:
                    self.parent.ids.accounts_count_label.text = f"Total Accounts: {count}"
                    return
                    
            # If not found in parent, try to find it in the screen manager
            for widget in Window.children:
                if hasattr(widget, 'walk'):
                    for child in widget.walk():
                        if isinstance(child, Label) and hasattr(child, "id") and child.id == "accounts_count_label":
                            child.text = f"Total Accounts: {count}"
                            return
        except Exception as e:
            print(f"Error updating account count: {e}")
            
    def delete_all_accounts(self):
        # Create confirmation popup
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        content.add_widget(Label(
            text="Are you sure you want to delete ALL accounts?",
            color=get_color_from_hex(COLORS['text']),
            size_hint_y=None,
            height=dp(40)
        ))
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        # Cancel button
        cancel_btn = Button(
            text="Cancel",
            background_color=get_color_from_hex(COLORS['text_secondary']),
            color=(1, 1, 1, 1)
        )
        
        # Confirm button
        confirm_btn = Button(
            text="Delete All",
            background_color=get_color_from_hex(COLORS['accent']),
            color=(1, 1, 1, 1)
        )
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(confirm_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Confirm Deletion',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        
        # Set up button actions
        cancel_btn.bind(on_release=popup.dismiss)
        
        def on_confirm(instance):
            try:
                # Delete all account files
                if os.path.exists("cookies"):
                    for file in os.listdir("cookies"):
                        if file.endswith(".json"):
                            os.remove(os.path.join("cookies", file))
                
                # Clear email mapping file
                if os.path.exists("account_emails.txt"):
                    with open("account_emails.txt", "w") as f:
                        pass
                
                # Update the count display to zero
                Clock.schedule_once(lambda dt: self._update_account_count(0), 0)
                
                popup.dismiss()
                
                # Clear the grid directly instead of reloading
                if hasattr(self, "ids") and "accounts_grid" in self.ids:
                    self.ids.accounts_grid.clear_widgets()
                    
                    # Add a "No accounts" message
                    no_accounts_label = Label(
                        text="No accounts available. Add some using the 'Add Accounts' button.",
                        color=get_color_from_hex(COLORS['text_secondary']),
                        size_hint_y=None,
                        height=dp(50)
                    )
                    self.ids.accounts_grid.add_widget(no_accounts_label)
                else:
                    # Fallback to full reload
                    self.load_accounts()
                
                # Show confirmation
                result_content = Label(
                    text="All accounts have been deleted.",
                    color=get_color_from_hex(COLORS['text'])
                )
                
                result_popup = Popup(
                    title="Success",
                    content=result_content,
                    size_hint=(0.8, 0.4),
                    background_color=get_color_from_hex(COLORS['card']),
                    title_color=get_color_from_hex(COLORS['primary'])
                )
                result_popup.open()
            except Exception as e:
                print(f"Error deleting all accounts: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to full reload
                self.load_accounts()
        
        confirm_btn.bind(on_release=on_confirm)
        popup.open()

    def delete_account(self, instance):
        try:
            file_path = os.path.join("cookies", f"{instance.account_name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # Also remove from account_emails.txt if possible
                if os.path.exists("account_emails.txt"):
                    try:
                        # Read all emails
                        with open("account_emails.txt", "r") as f:
                            emails = [line.strip() for line in f if line.strip()]
                        
                        # Find the email associated with this account
                        email_to_remove = None
                        for email in emails:
                            if '@' in email:
                                username = email.split('@')[0]
                                username = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in username)
                                if instance.account_name == username or instance.account_name.startswith(f"{username}_"):
                                    email_to_remove = email
                                    break
                        
                        # Remove the email if found
                        if email_to_remove and email_to_remove in emails:
                            emails.remove(email_to_remove)
                            
                            # Write back the remaining emails
                            with open("account_emails.txt", "w") as f:
                                for email in emails:
                                    f.write(email + "\n")
                    except Exception as e:
                        print(f"Error updating email file: {e}")
                
                # Get remaining account count
                remaining_count = 0
                if os.path.exists("cookies"):
                    remaining_count = len([f for f in os.listdir("cookies") if f.endswith(".json")])
                
                # Update the count display immediately
                if hasattr(self, "parent") and hasattr(self.parent, "ids") and "accounts_count_label" in self.parent.ids:
                    self.parent.ids.accounts_count_label.text = f"Total Accounts: {remaining_count}"
                
                # Find and remove the parent widget of the button
                parent_widget = instance.parent
                if parent_widget and hasattr(self, "ids") and "accounts_grid" in self.ids:
                    self.ids.accounts_grid.remove_widget(parent_widget)
                    
                    # If no accounts left, show a message
                    if remaining_count == 0:
                        no_accounts_label = Label(
                            text="No accounts available. Add some using the 'Add Accounts' button.",
                            color=get_color_from_hex(COLORS['text_secondary']),
                            size_hint_y=None,
                            height=dp(50)
                        )
                        self.ids.accounts_grid.add_widget(no_accounts_label)
                else:
                    # If we couldn't find the widget, reload everything
                    self.load_accounts()
        except Exception as e:
            print(f"Error deleting account: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to full reload
            self.load_accounts()


class ProxiesTab(BoxLayout):
    def __init__(self, **kwargs):
        super(ProxiesTab, self).__init__(**kwargs)
        Clock.schedule_once(self._init_ui, 0)

    def _init_ui(self, dt):
        self.load_proxies()
        self.load_api_config()

    def add_bulk_proxies(self):
        # Open the bulk proxy popup
        popup = BulkProxyPopup(callback=self.load_proxies)
        popup.open()

    def load_api_config(self):
        # Load API configuration if it exists
        from proxy_rotator import load_proxy_api_config
        config = load_proxy_api_config()
        if config and hasattr(self, "ids"):
            if "api_url_input" in self.ids:
                self.ids.api_url_input.text = config.get("api_url", "")
            if "api_key_input" in self.ids:
                self.ids.api_key_input.text = config.get("api_key", "")

    def save_api_config(self):
        if not hasattr(self, "ids"):
            return
            
        from proxy_rotator import save_proxy_api_config
        api_url = self.ids.api_url_input.text.strip()
        api_key = self.ids.api_key_input.text.strip()
        
        if not api_url:
            content = Label(
                text="Please enter a valid API URL",
                color=get_color_from_hex(COLORS['text'])
            )
            popup = Popup(
                title='Error', 
                content=content, 
                size_hint=(0.8, 0.4),
                background_color=get_color_from_hex(COLORS['card']),
                title_color=get_color_from_hex(COLORS['accent'])
            )
            popup.open()
            return
            
        save_proxy_api_config(api_url, api_key)
        
        # Show confirmation
        content = Label(
            text="API configuration saved successfully",
            color=get_color_from_hex(COLORS['text'])
        )
        popup = Popup(
            title='Success', 
            content=content, 
            size_hint=(0.8, 0.4),
            background_color=get_color_from_hex(COLORS['card']),
            title_color=get_color_from_hex(COLORS['primary'])
        )
        popup.open()

    def test_api(self):
        if not hasattr(self, "ids"):
            return
            
        from proxy_rotator import fetch_proxies_from_api
        
        # Save current config first
        self.save_api_config()
        
        # Try to fetch proxies
        proxies = fetch_proxies_from_api()
        
        if proxies:
            content = Label(
                text=f"Successfully fetched {len(proxies)} proxies from API",
                color=get_color_from_hex(COLORS['text'])
            )
            popup = Popup(
                title='Success', 
                content=content, 
                size_hint=(0.8, 0.4),
                background_color=get_color_from_hex(COLORS['card']),
                title_color=get_color_from_hex(COLORS['primary'])
            )
            popup.open()
        else:
            content = Label(
                text="Failed to fetch proxies from API. Check your configuration.",
                color=get_color_from_hex(COLORS['text'])
            )
            popup = Popup(
                title='Error', 
                content=content, 
                size_hint=(0.8, 0.4),
                background_color=get_color_from_hex(COLORS['card']),
                title_color=get_color_from_hex(COLORS['accent'])
            )
            popup.open()
            
    def remove_api_config(self):
        from proxy_rotator import remove_proxy_api_config
        
        # Create confirmation popup
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        content.add_widget(Label(
            text="Are you sure you want to remove the API configuration?",
            color=get_color_from_hex(COLORS['text']),
            size_hint_y=None,
            height=dp(40)
        ))
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        # Cancel button
        cancel_btn = Button(
            text="Cancel",
            background_color=get_color_from_hex(COLORS['text_secondary']),
            color=(1, 1, 1, 1)
        )
        
        # Confirm button
        confirm_btn = Button(
            text="Remove",
            background_color=get_color_from_hex(COLORS['accent']),
            color=(1, 1, 1, 1)
        )
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(confirm_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Confirm Removal',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        
        # Set up button actions
        cancel_btn.bind(on_release=popup.dismiss)
        
        def on_confirm(instance):
            result = remove_proxy_api_config()
            popup.dismiss()
            
            # Clear the input fields
            if hasattr(self, "ids"):
                if "api_url_input" in self.ids:
                    self.ids.api_url_input.text = ""
                if "api_key_input" in self.ids:
                    self.ids.api_key_input.text = ""
            
            # Show result popup
            result_text = "API configuration removed successfully." if result else "Failed to remove API configuration."
            result_title = "Success" if result else "Error"
            title_color = get_color_from_hex(COLORS['primary'] if result else COLORS['accent'])
            
            result_content = Label(
                text=result_text,
                color=get_color_from_hex(COLORS['text'])
            )
            
            result_popup = Popup(
                title=result_title,
                content=result_content,
                size_hint=(0.8, 0.4),
                background_color=get_color_from_hex(COLORS['card']),
                title_color=title_color
            )
            result_popup.open()
        
        confirm_btn.bind(on_release=on_confirm)
        popup.open()

    def load_proxies(self):
        if not hasattr(self, "ids") or "proxies_grid" not in self.ids:
            return

        proxies_grid = self.ids.proxies_grid
        proxies_grid.clear_widgets()

        if not os.path.exists("proxies.txt"):
            with open("proxies.txt", "w") as f:
                pass
            return
            
        # Load proxies directly without threading or loading indicators
        self._load_proxies_direct()
        
    def _load_proxies_direct(self):
        try:
            if not hasattr(self, "ids") or "proxies_grid" not in self.ids:
                return
                
            proxies_grid = self.ids.proxies_grid
            
            # Load proxies in a more efficient way
            proxies = []
            try:
                with open("proxies.txt", "r") as f:
                    lines = f.readlines()
                    proxies = [line.strip() for line in lines if line.strip()]
            except Exception as e:
                print(f"Error reading proxies.txt: {e}")
                
            total_proxies = len(proxies)
            print(f"Loaded {total_proxies} proxies")
            
            # Update the count display immediately - try multiple approaches
            # 1. Try direct parent
            if hasattr(self, "parent") and hasattr(self.parent, "ids") and "proxies_count_label" in self.parent.ids:
                self.parent.ids.proxies_count_label.text = f"Total Proxies: {total_proxies}"
                print(f"Updated count via parent: {total_proxies}")
            
            # 2. Try screen manager
            for widget in Window.children:
                if hasattr(widget, 'walk'):
                    for child in widget.walk():
                        if isinstance(child, Label) and hasattr(child, "id") and child.id == "proxies_count_label":
                            child.text = f"Total Proxies: {total_proxies}"
                            print(f"Updated count via walk: {total_proxies}")
                            break
            
            # If no proxies, show a message
            if not proxies:
                no_proxies_label = Label(
                    text="No proxies available. Add some using the form above.",
                    color=get_color_from_hex(COLORS['text_secondary']),
                    size_hint_y=None,
                    height=dp(50)
                )
                proxies_grid.add_widget(no_proxies_label)
                return
            
            # Create a simplified grid layout with just text and buttons
            for proxy in proxies:
                # Limit proxy text length to prevent overflow
                display_text = proxy
                if len(display_text) > 25:
                    display_text = display_text[:22] + "..."
                
                # Create a simpler layout for each proxy
                card = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(5)
                )
                
                # Proxy URL label
                label = Label(
                    text=display_text,
                    size_hint_x=0.7,
                    color=get_color_from_hex(COLORS["text"]),
                    font_size=dp(12),
                    halign='left',
                    text_size=(None, None)
                )
                card.add_widget(label)

                # Delete button
                delete_btn = Button(
                    text="Delete",
                    size_hint_x=0.3,
                    background_color=get_color_from_hex(COLORS["accent"]),
                    color=(1, 1, 1, 1),
                    font_size=dp(12)
                )
                delete_btn.proxy_url = proxy  # Store proxy URL as attribute
                delete_btn.bind(on_release=self.delete_proxy)
                card.add_widget(delete_btn)
                
                proxies_grid.add_widget(card)
            
        except Exception as e:
            print(f"Error loading proxies: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_proxy_count(self, count):
        """Update the proxy count display"""
        try:
            # Try to find the count label in the parent screen
            if hasattr(self, "parent") and hasattr(self.parent, "ids"):
                if "proxies_count_label" in self.parent.ids:
                    self.parent.ids.proxies_count_label.text = f"Total Proxies: {count}"
                    return
                    
            # If not found in parent, try to find it in the screen manager
            for widget in Window.children:
                if hasattr(widget, 'walk'):
                    for child in widget.walk():
                        if isinstance(child, Label) and hasattr(child, "id") and child.id == "proxies_count_label":
                            child.text = f"Total Proxies: {count}"
                            return
        except Exception as e:
            print(f"Error updating proxy count: {e}")
            
    def delete_all_proxies(self):
        # Create confirmation popup
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        content.add_widget(Label(
            text="Are you sure you want to delete ALL proxies?",
            color=get_color_from_hex(COLORS['text']),
            size_hint_y=None,
            height=dp(40)
        ))
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        # Cancel button
        cancel_btn = Button(
            text="Cancel",
            background_color=get_color_from_hex(COLORS['text_secondary']),
            color=(1, 1, 1, 1)
        )
        
        # Confirm button
        confirm_btn = Button(
            text="Delete All",
            background_color=get_color_from_hex(COLORS['accent']),
            color=(1, 1, 1, 1)
        )
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(confirm_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Confirm Deletion',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        
        # Set up button actions
        cancel_btn.bind(on_release=popup.dismiss)
        
        def on_confirm(instance):
            try:
                # Clear the proxies file
                if os.path.exists("proxies.txt"):
                    with open("proxies.txt", "w") as f:
                        pass
                
                # Update the count display to zero
                Clock.schedule_once(lambda dt: self._update_proxy_count(0), 0)
                
                popup.dismiss()
                
                # Clear the grid directly instead of reloading
                if hasattr(self, "ids") and "proxies_grid" in self.ids:
                    self.ids.proxies_grid.clear_widgets()
                    
                    # Add a "No proxies" message
                    no_proxies_label = Label(
                        text="No proxies available. Add some using the form above.",
                        color=get_color_from_hex(COLORS['text_secondary']),
                        size_hint_y=None,
                        height=dp(50)
                    )
                    self.ids.proxies_grid.add_widget(no_proxies_label)
                else:
                    # Fallback to full reload
                    self.load_proxies()
                
                # Show confirmation
                result_content = Label(
                    text="All proxies have been deleted.",
                    color=get_color_from_hex(COLORS['text'])
                )
                
                result_popup = Popup(
                    title="Success",
                    content=result_content,
                    size_hint=(0.8, 0.4),
                    background_color=get_color_from_hex(COLORS['card']),
                    title_color=get_color_from_hex(COLORS['primary'])
                )
                result_popup.open()
            except Exception as e:
                print(f"Error deleting all proxies: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to full reload
                self.load_proxies()
        
        confirm_btn.bind(on_release=on_confirm)
        popup.open()

    def add_proxy(self):
        if not hasattr(self, "ids") or "proxy_input" not in self.ids:
            return

        proxy = self.ids.proxy_input.text.strip()
        if not proxy:
            return

        # Add the proxy to the file
        with open("proxies.txt", "a") as f:
            f.write(proxy + "\n")

        # Get the new count
        try:
            with open("proxies.txt", "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
                proxy_count = len(proxies)
                
            # Update the count display immediately
            if hasattr(self, "parent") and hasattr(self.parent, "ids") and "proxies_count_label" in self.parent.ids:
                self.parent.ids.proxies_count_label.text = f"Total Proxies: {proxy_count}"
        except Exception as e:
            print(f"Error updating proxy count: {e}")

        self.ids.proxy_input.text = ""  # Clear the input
        self.load_proxies()  # Refresh the list

    def delete_proxy(self, instance):
        try:
            # Read all proxies
            proxies = []
            try:
                with open("proxies.txt", "r") as f:
                    proxies = [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"Error reading proxies: {e}")
                return

            # Remove the selected proxy
            if instance.proxy_url in proxies:
                proxies.remove(instance.proxy_url)

            # Write back the remaining proxies
            with open("proxies.txt", "w") as f:
                for proxy in proxies:
                    f.write(proxy + "\n")
                    
            # Update the count display immediately
            remaining_count = len(proxies)
            if hasattr(self, "parent") and hasattr(self.parent, "ids") and "proxies_count_label" in self.parent.ids:
                self.parent.ids.proxies_count_label.text = f"Total Proxies: {remaining_count}"
            
            # Find and remove the parent widget of the button
            parent_widget = instance.parent
            if parent_widget and hasattr(self, "ids") and "proxies_grid" in self.ids:
                self.ids.proxies_grid.remove_widget(parent_widget)
                
                # If no proxies left, show a message
                if remaining_count == 0:
                    no_proxies_label = Label(
                        text="No proxies available. Add some using the form above.",
                        color=get_color_from_hex(COLORS['text_secondary']),
                        size_hint_y=None,
                        height=dp(50)
                    )
                    self.ids.proxies_grid.add_widget(no_proxies_label)
            else:
                # If we couldn't find the widget, reload everything
                self.load_proxies()
        except Exception as e:
            print(f"Error deleting proxy: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to full reload
            self.load_proxies()


class AccountManagerApp(App):
    colors = COLORS

    def build(self):
        Builder.load_string(kv)
        Window.size = (800, 600)
        Window.maximize()  # Maximize the window when the app starts

        sm = ScreenManager()
        sm.add_widget(AccountManagerScreen(name="manager"))
        return sm


if __name__ == "__main__":
    AccountManagerApp().run()


















class BulkProxyPopup(Popup):
    def __init__(self, callback, **kwargs):
        self.callback = callback
        
        # Create content layout
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        # Add instructions
        instructions = Label(
            text="Paste your proxies below (one per line)\nFormat: http://ip:port or ip:port",
            size_hint_y=None,
            height=dp(40),
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        content.add_widget(instructions)
        
        # Add text input for proxies with larger height for bulk pasting
        self.proxies_input = TextInput(
            hint_text="Paste proxies here...",
            multiline=True,
            size_hint=(1, 1),  # Take all available space
            font_size=dp(14)
        )
        content.add_widget(self.proxies_input)
        
        # Add buttons
        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        cancel_btn = Button(
            text="Cancel",
            size_hint_x=0.5
        )
        cancel_btn.bind(on_release=self.dismiss)
        
        process_btn = Button(
            text="Add Proxies",
            size_hint_x=0.5,
            background_color=get_color_from_hex(COLORS['primary'])
        )
        process_btn.bind(on_release=self.process_proxies)
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(process_btn)
        content.add_widget(buttons)
        
        # Configure popup
        super(BulkProxyPopup, self).__init__(
            title="Add Bulk Proxies",
            content=content,
            size_hint=(0.9, 0.8),  # Make it larger for bulk pasting
            auto_dismiss=False,
            **kwargs
        )
    
    def process_proxies(self, instance):
        proxies_text = self.proxies_input.text.strip()
        if not proxies_text:
            error_popup = Popup(
                title="Error",
                content=Label(text="Please paste at least one proxy"),
                size_hint=(0.6, None),
                height=dp(200)
            )
            error_popup.open()
            return
        
        # Parse proxies
        proxies = []
        for line in proxies_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Add http:// prefix if not present
            if not line.startswith('http://') and not line.startswith('https://'):
                line = 'http://' + line
                
            proxies.append(line)
        
        if not proxies:
            error_popup = Popup(
                title="Error",
                content=Label(text="No valid proxies found"),
                size_hint=(0.6, None),
                height=dp(200)
            )
            error_popup.open()
            return
        
        # Add proxies to file
        with open("proxies.txt", "a") as f:
            for proxy in proxies:
                f.write(proxy + "\n")
        
        # Get total proxy count for display
        total_proxies = 0
        try:
            with open("proxies.txt", "r") as f:
                lines = f.readlines()
                total_proxies = sum(1 for line in lines if line.strip())
        except Exception as e:
            print(f"Error counting proxies: {e}")
        
        # Update the count display directly
        for widget in Window.children:
            if hasattr(widget, 'walk'):
                for child in widget.walk():
                    if isinstance(child, Label) and hasattr(child, "id") and child.id == "proxies_count_label":
                        child.text = f"Total Proxies: {total_proxies}"
                        print(f"Updated count in bulk add: {total_proxies}")
                        break
        
        # Close this popup
        self.dismiss()
        
        # Call the callback to refresh the proxy list
        self.callback()
        
        # Show success message
        success_popup = Popup(
            title="Success",
            content=Label(text=f"Added {len(proxies)} proxies successfully\nTotal proxies: {total_proxies}"),
            size_hint=(0.6, None),
            height=dp(200)
        )
        success_popup.open()






