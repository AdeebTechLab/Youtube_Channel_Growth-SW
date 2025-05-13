import os
import sys
import threading
import time
import random
from functools import partial

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, ObjectProperty, BooleanProperty
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from kivy.config import Config

# Configure Kivy for better performance
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'maxfps', '60')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# Import existing functionality
import subprocess
from liker import like_video, process_multiple_likes
from subscriber import subscribe_video
from viewer import add_view, process_multiple_views
from proxy_rotator import add_proxies, load_proxies, get_proxy_rotation_choice, select_proxies, get_random_proxy

# Define color palette
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

# Load KV string with proper imports
kv = '''
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

<MainScreen>:
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
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            
            Widget:
                size_hint_x: 0.7
            
            RoundedButton:
                text: "Manage Account"
                size_hint_x: 0.15
                background_color: get_color_from_hex(app.colors['card'])
                color: get_color_from_hex(app.colors['primary'])
                bold: True
                on_release: root.manage_account()
            
            RoundedButton:
                text: "Exit"
                size_hint_x: 0.15
                background_color: get_color_from_hex(app.colors['card'])
                color: get_color_from_hex(app.colors['accent'])
                bold: True
                on_release: app.stop()
        
        Label:
            text: "YouTube Growth Hub"
            font_size: dp(28)
            color: get_color_from_hex(app.colors['accent'])
            size_hint_y: None
            height: dp(50)
            bold: True
        
        Label:
            text: "Boost your YouTube presence with our specialized tools"
            font_size: dp(16)
            color: get_color_from_hex(app.colors['text_secondary'])
            size_hint_y: None
            height: dp(30)
        
        Widget:
            size_hint_y: None
            height: dp(20)
        
        Label:
            text: "What do you need?"
            font_size: dp(18)
            color: get_color_from_hex(app.colors['text'])
            size_hint_y: None
            height: dp(40)
            bold: True
        
        BoxLayout:
            size_hint_y: None
            height: dp(100)
            spacing: dp(15)
            
            RoundedButton:
                text: "Subscribers"
                background_color: get_color_from_hex(app.colors['subscribers_active'] if root.current_mode == 'subscribers' else app.colors['subscribers'])
                color: get_color_from_hex(app.colors['text'] if root.current_mode != 'subscribers' else '#ffffff')
                font_size: dp(18)
                bold: True
                on_release: root.set_mode("subscribers")
            
            RoundedButton:
                text: "Likes"
                background_color: get_color_from_hex(app.colors['likes_active'] if root.current_mode == 'likes' else app.colors['likes'])
                color: get_color_from_hex(app.colors['text'] if root.current_mode != 'likes' else '#ffffff')
                font_size: dp(18)
                bold: True
                on_release: root.set_mode("likes")
            
            RoundedButton:
                text: "Views"
                background_color: get_color_from_hex(app.colors['views_active'] if root.current_mode == 'views' else app.colors['views'])
                color: get_color_from_hex(app.colors['text'] if root.current_mode != 'views' else '#ffffff')
                font_size: dp(18)
                bold: True
                on_release: root.set_mode("views")
        
        Widget:
            size_hint_y: None
            height: dp(20)
        
        Label:
            text: "Your YouTube URL"
            font_size: dp(18)
            color: get_color_from_hex(app.colors['text'])
            size_hint_y: None
            height: dp(30)
            bold: True
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            
            TextInput:
                id: url_input
                hint_text: "Enter YouTube URL to gain " + root.current_mode + "..."
                multiline: False
                padding: [dp(10), dp(10), dp(10), dp(10)]
                font_size: dp(16)
                background_color: get_color_from_hex(app.colors['card'])
                foreground_color: get_color_from_hex(app.colors['text'])
                cursor_color: get_color_from_hex(app.colors['primary'])
            
            RoundedButton:
                text: "Submit URL"
                size_hint_x: 0.3
                background_color: get_color_from_hex(app.colors['primary'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.submit_url()
        
        Widget:
            size_hint_y: 0.3
        
        Label:
            text: "Share your custom link to grow your YouTube channel faster"
            font_size: dp(14)
            color: get_color_from_hex(app.colors['text_secondary'])
            size_hint_y: None
            height: dp(30)

<CustomPopup>:
    background: ''
    background_color: 0, 0, 0, 0.5
    separator_color: get_color_from_hex(app.colors['primary'])
    title_color: 1, 1, 1, 1  # White title color
    title_size: dp(18)
    title_align: 'center'
    
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.5
        Rectangle:
            size: self._window.size if self._window else (0, 0)
            pos: 0, 0
        
        Color:
            rgba: get_color_from_hex(app.colors['primary_dark'])  # Darker background for better contrast
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(15)]

<CountPopup>:
    title: 'How many?'
    size_hint: 0.8, None
    height: dp(320)  # Reduced height since we removed a section
    auto_dismiss: False
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        
        Label:
            id: count_label
            text: root.count_text
            size_hint_y: None
            height: dp(30)
            color: 1, 1, 1, 1  # White text color
            font_size: dp(16)
            bold: True
            halign: 'center'
            valign: 'middle'
            text_size: self.width, None
        
        TextInput:
            id: count_input
            multiline: False
            input_filter: 'int'
            size_hint_y: None
            height: dp(50)
            padding: [dp(10), dp(15), dp(10), dp(15)]
            font_size: dp(16)
            background_color: get_color_from_hex(app.colors['card'])
            foreground_color: get_color_from_hex(app.colors['text'])
            cursor_color: get_color_from_hex(app.colors['primary'])
            hint_text: "Enter number"
        
        Label:
            text: "Available proxies will be used automatically"
            size_hint_y: None
            height: dp(30)
            color: 1, 1, 1, 1  # White text color
            font_size: dp(14)
            italic: True
            halign: 'center'
        
        Widget:
            size_hint_y: None
            height: dp(10)
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            
            RoundedButton:
                text: "Cancel"
                background_color: get_color_from_hex(app.colors['text_secondary'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.dismiss()
            
            RoundedButton:
                text: "Proceed"
                background_color: get_color_from_hex(app.colors['accent'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.proceed()

<ProxyRotationPopup>:
    title: 'Proxy Rotation'
    size_hint: 0.8, None
    height: dp(250)
    auto_dismiss: False
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        
        Label:
            text: "Do you want to use proxy rotation?"
            size_hint_y: None
            height: dp(40)
            color: 1, 1, 1, 1  # White text color
            font_size: dp(16)
            bold: True
            halign: 'center'
            valign: 'middle'
            text_size: self.width, None
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            
            RoundedButton:
                text: "Yes"
                background_color: get_color_from_hex(app.colors['primary'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.set_rotation(True)
            
            RoundedButton:
                text: "No"
                background_color: get_color_from_hex(app.colors['text_secondary'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.set_rotation(False)
        
        Widget:
            size_hint_y: None
            height: dp(10)
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            
            RoundedButton:
                text: "Cancel"
                background_color: get_color_from_hex(app.colors['text_secondary'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.dismiss()
            
            RoundedButton:
                text: "Proceed"
                background_color: get_color_from_hex(app.colors['accent'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.proceed()

<ProxySelectionPopup>:
    title: 'Select Proxies'
    size_hint: 0.8, None
    height: dp(250)
    auto_dismiss: False
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        
        Label:
            text: "How many proxies to use?"
            size_hint_y: None
            height: dp(40)
            color: 1, 1, 1, 1  # White text color
            font_size: dp(16)
            bold: True
            halign: 'center'
            valign: 'middle'
            text_size: self.width, None
        
        TextInput:
            id: proxy_count_input
            multiline: False
            input_filter: 'int'
            size_hint_y: None
            height: dp(50)
            padding: [dp(10), dp(15), dp(10), dp(15)]
            font_size: dp(16)
            background_color: get_color_from_hex(app.colors['card'])
            foreground_color: get_color_from_hex(app.colors['text'])
            cursor_color: get_color_from_hex(app.colors['primary'])
            hint_text: "Enter number of proxies"
        
        Widget:
            size_hint_y: None
            height: dp(10)
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            
            RoundedButton:
                text: "Cancel"
                background_color: get_color_from_hex(app.colors['text_secondary'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.dismiss()
            
            RoundedButton:
                text: "Select"
                background_color: get_color_from_hex(app.colors['accent'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.select_proxies()

<ProgressPopup>:
    title: 'Progress'
    size_hint: 0.8, None
    height: dp(250)
    auto_dismiss: False
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        
        Label:
            id: progress_label
            text: "Processing..."
            color: 1, 1, 1, 1  # White text color
            font_size: dp(16)
            bold: True
            halign: 'center'
            valign: 'middle'
            text_size: self.width, None
        
        Label:
            id: progress_count
            text: "0/0"
            color: 1, 1, 1, 0.8  # White text color with slight transparency
            font_size: dp(14)
            halign: 'center'
            valign: 'middle'
            text_size: self.width, None
        
        ProgressBar:
            id: progress_bar
            max: 100
            value: 0
            size_hint_y: None
            height: dp(20)
        
        Label:
            id: elapsed_time
            text: "Elapsed time: 00:00"
            color: 1, 1, 1, 0.8
            font_size: dp(14)
            halign: 'center'
            valign: 'middle'
            text_size: self.width, None
            size_hint_y: None
            height: dp(30)
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            
            RoundedButton:
                id: cancel_button
                text: "Cancel"
                size_hint_x: 0.5
                background_color: get_color_from_hex(app.colors['accent'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                on_release: root.cancel_operation()
            
            RoundedButton:
                id: close_button
                text: "Close"
                size_hint_x: 0.5
                background_color: get_color_from_hex(app.colors['primary'])
                color: 1, 1, 1, 1
                font_size: dp(16)
                bold: True
                disabled: not root.is_complete
                on_release: root.dismiss()
'''

class RoundedButton(Button):
    pass

class CustomPopup(Popup):
    pass

class MainScreen(Screen):
    current_mode = StringProperty("subscribers")
    
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        os.makedirs("cookies", exist_ok=True)
    
    def set_mode(self, mode):
        self.current_mode = mode
    
    def manage_account(self):
        # Launch the account manager UI
        print("Switching to account manager screen")
        self.manager.current = 'account_manager'
    
    def submit_url(self):
        url = self.ids.url_input.text.strip()
        if not url:
            self.show_error("Please enter a YouTube URL")
            return
        
        if self.current_mode == "subscribers":
            self.handle_subscribers(url)
        elif self.current_mode == "likes":
            self.handle_likes(url)
        elif self.current_mode == "views":
            self.handle_views(url)
    
    def handle_subscribers(self, url):
        available = self.count_accounts()
        if available == 0:
            self.show_error("No accounts available. Please add accounts first.")
            return
        
        popup = CountPopup(
            count_text=f"How many accounts to subscribe from? (Available: {available})",
            max_count=available,
            url=url,
            mode="subscribers",
            callback=self.process_subscribers
        )
        popup.open()
    
    def handle_likes(self, url):
        available = self.count_accounts()
        if available == 0:
            self.show_error("No accounts available. Please add accounts first.")
            return
        
        popup = CountPopup(
            count_text=f"How many accounts to like from? (Available: {available})",
            max_count=available,
            url=url,
            mode="likes",
            callback=self.process_likes
        )
        popup.open()
    
    def handle_views(self, url):
        popup = CountPopup(
            count_text="How many views to add?",
            max_count=1000,  # Arbitrary limit
            url=url,
            mode="views",
            callback=self.process_views
        )
        popup.open()
    
    def count_accounts(self):
        return len([f for f in os.listdir("cookies") if f.endswith(".json")])
    
    def get_account_name_by_index(self, i):
        return f"account{i+1}"
    
    def process_subscribers(self, count, url, use_proxies):
        proxies = []
        if use_proxies:
            proxies = load_proxies()
            if not proxies:
                self.show_error("No proxies available.")
                return
            
            # Handle proxy rotation
            rotation_popup = ProxyRotationPopup(callback=lambda rotation: self.handle_rotation(
                rotation, proxies, lambda selected_proxies: self.execute_subscribers(count, url, selected_proxies)
            ))
            rotation_popup.open()
        else:
            self.execute_subscribers(count, url, None)
    
    def process_likes(self, count, url, use_proxies):
        proxies = []
        if use_proxies:
            proxies = load_proxies()
            if not proxies:
                self.show_error("No proxies available.")
                return
            
            # Handle proxy rotation
            rotation_popup = ProxyRotationPopup(callback=lambda rotation: self.handle_rotation(
                rotation, proxies, lambda selected_proxies: self.execute_likes(count, url, selected_proxies)
            ))
            rotation_popup.open()
        else:
            self.execute_likes(count, url, None)
    
    def process_views(self, count, url, use_proxies):
        proxies = []
        if use_proxies:
            proxies = load_proxies()
            if not proxies:
                self.show_error("No proxies available.")
                return
            
            # Handle proxy rotation
            rotation_popup = ProxyRotationPopup(callback=lambda rotation: self.handle_rotation(
                rotation, proxies, lambda selected_proxies: self.execute_views(count, url, selected_proxies)
            ))
            rotation_popup.open()
        else:
            self.execute_views(count, url, None)
    
    def handle_rotation(self, use_rotation, proxies, callback):
        if use_rotation:
            selection_popup = ProxySelectionPopup(
                proxies=proxies,
                callback=callback
            )
            selection_popup.open()
        else:
            callback(proxies)
    
    def execute_subscribers(self, count, url, proxies):
        """Execute subscriber operations with improved UI feedback"""
        progress_popup = ProgressPopup()
        progress_popup.open()
        progress_popup.start_progress(count)
        
        # Create a list of account names
        accounts = [self.get_account_name_by_index(i) for i in range(count)]
        
        # Start a background thread for processing
        def process_thread():
            successes = 0
            results = []  # Store detailed results
            
            for i in range(count):
                if progress_popup.should_cancel:
                    break
                    
                account = accounts[i]
                proxy = get_random_proxy(proxies) if proxies else None
                
                # Update UI from the main thread
                Clock.schedule_once(
                    lambda dt, acc=account, px=proxy: progress_popup.update_progress(
                        i, f"Subscribing from {acc} {'using proxy ' + px if px else 'without proxy'}"
                    )
                )
                
                # Process subscription
                try:
                    result = subscribe_video(account, url, proxy)
                    
                    # Update UI with immediate feedback
                    status = "✓ Success" if result else "✗ Failed"
                    Clock.schedule_once(
                        lambda dt, acc=account, stat=status: progress_popup.update_progress(
                            i, f"Account {acc}: {stat}"
                        )
                    )
                    
                    if result:
                        successes += 1
                    
                    # Store result details
                    results.append({
                        "account": account,
                        "success": result,
                        "proxy": proxy
                    })
                    
                except Exception as e:
                    # Handle errors
                    Clock.schedule_once(
                        lambda dt, acc=account, err=str(e): progress_popup.update_progress(
                            i, f"Account {acc}: Error - {err[:30]}..."
                        )
                    )
                    results.append({
                        "account": account,
                        "success": False,
                        "error": str(e),
                        "proxy": proxy
                    })
                
                # Small delay to prevent UI freezing
                time.sleep(0.1)
            
            # Update UI with completion status
            Clock.schedule_once(
                lambda dt: self.show_operation_results(
                    "Subscribe", successes, count, results, progress_popup
                )
            )
        
        # Start the thread
        threading.Thread(target=process_thread, daemon=True).start()
    
    def show_operation_results(self, operation_type, successes, total, results, progress_popup):
        """Show detailed operation results"""
        # First update the progress popup
        progress_popup.complete(
            f"Completed {successes} out of {total} {operation_type.lower()} operations!"
        )
        
        # Create a detailed results popup
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # Add header
        header = Label(
            text=f"{operation_type} Operation Results",
            font_size=dp(18),
            bold=True,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(header)
        
        # Add summary
        summary = Label(
            text=f"Successfully completed {successes} out of {total} operations",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(summary)
        
        # Add scrollable results
        scroll = ScrollView(size_hint=(1, 1))
        results_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        results_grid.bind(minimum_height=results_grid.setter('height'))
        
        # Add each result
        for i, result in enumerate(results):
            # Handle different result formats for different operation types
            if operation_type.lower() == "view":
                # For views
                result_text = f"#{i+1}: View "
                if 'view_number' in result:
                    result_text = f"#{result['view_number']}: View "
            else:
                # For subscribers and likes
                result_text = f"#{i+1}: {result.get('account', 'Unknown')} - "
                
            # Add success/failure status
            result_text += "Success" if result.get('success', False) else "Failed"
            
            # Add error message if present
            if 'error' in result:
                result_text += f" ({result['error'][:30]}...)"
                
            # Add proxy info if present
            if 'proxy' in result and result['proxy']:
                result_text += f" (Proxy: {result['proxy']})"
                
            result_label = Label(
                text=result_text,
                font_size=dp(14),
                size_hint_y=None,
                height=dp(30),
                halign='left',
                text_size=(None, None)
            )
            results_grid.add_widget(result_label)
        
        scroll.add_widget(results_grid)
        content.add_widget(scroll)
        
        # Add close button
        close_btn = Button(
            text="Close",
            size_hint_y=None,
            height=dp(50)
        )
        content.add_widget(close_btn)
        
        # Create and show popup
        results_popup = Popup(
            title=f"{operation_type} Results",
            content=content,
            size_hint=(0.8, 0.8)
        )
        
        # Bind close button
        close_btn.bind(on_release=results_popup.dismiss)
        
        # Open the popup after a short delay to ensure the progress popup updates first
        Clock.schedule_once(lambda dt: results_popup.open(), 1)
    
    def execute_likes(self, count, url, proxies):
        """Execute like operations with improved UI feedback and parallel processing"""
        progress_popup = ProgressPopup()
        progress_popup.open()
        progress_popup.start_progress(count)
        
        # Create a list of account names
        accounts = [self.get_account_name_by_index(i) for i in range(count)]
        
        # Start a background thread for processing
        def process_thread():
            # Determine optimal number of parallel processes
            max_workers = min(count, 2)  # Limit to 2 parallel processes to avoid overloading
            
            # Process in batches for better UI responsiveness
            batch_size = max(1, count // 10)  # Process in batches of 10% of total
            
            completed = 0
            successes = 0
            results = []  # Store detailed results
            
            for i in range(0, count, batch_size):
                if progress_popup.should_cancel:
                    break
                    
                # Process a batch
                batch_accounts = accounts[i:i+batch_size]
                batch_size_actual = len(batch_accounts)
                
                # Update progress
                Clock.schedule_once(
                    lambda dt, start=i, size=batch_size_actual: progress_popup.update_progress(
                        start, f"Processing accounts {start+1}-{start+size}..."
                    )
                )
                
                # Process batch with parallel execution
                for j, account in enumerate(batch_accounts):
                    if progress_popup.should_cancel:
                        break
                        
                    idx = i + j
                    proxy = get_random_proxy(proxies) if proxies else None
                    
                    # Update UI
                    Clock.schedule_once(
                        lambda dt, acc=account, px=proxy, idx=idx: progress_popup.update_progress(
                            idx, f"Liking from {acc} {'using proxy ' + px if px else 'without proxy'}"
                        )
                    )
                    
                    # Process like
                    try:
                        result = like_video(account, url, proxy)
                        
                        # Update UI with immediate feedback
                        status = "✓ Success" if result else "✗ Failed"
                        Clock.schedule_once(
                            lambda dt, acc=account, stat=status, idx=idx: progress_popup.update_progress(
                                idx, f"Account {acc}: {stat}"
                            )
                        )
                        
                        # Update counters
                        completed += 1
                        if result:
                            successes += 1
                        
                        # Store result details
                        results.append({
                            "account": account,
                            "success": result,
                            "proxy": proxy
                        })
                        
                    except Exception as e:
                        # Handle errors
                        Clock.schedule_once(
                            lambda dt, acc=account, err=str(e), idx=idx: progress_popup.update_progress(
                                idx, f"Account {acc}: Error - {err[:30]}..."
                            )
                        )
                        results.append({
                            "account": account,
                            "success": False,
                            "error": str(e),
                            "proxy": proxy
                        })
                        completed += 1
                    
                    # Small delay to prevent UI freezing
                    time.sleep(0.1)
            
            # Update UI with completion status
            Clock.schedule_once(
                lambda dt: self.show_operation_results(
                    "Like", successes, completed, results, progress_popup
                )
            )
        
        # Start the thread
        threading.Thread(target=process_thread, daemon=True).start()
    
    def execute_views(self, count, url, proxies):
        """Execute view operations with improved UI feedback and parallel processing"""
        progress_popup = ProgressPopup()
        progress_popup.open()
        progress_popup.start_progress(count)
        
        # Create a cancellation check function that can be passed to the viewer
        def check_cancellation():
            return progress_popup.should_cancel
        
        # Start a background thread for processing
        def process_thread():
            # Determine optimal number of parallel processes
            max_workers = min(count, 2)  # Limit to 2 parallel processes to avoid overloading
            
            completed = 0
            successes = 0
            results = []  # Store detailed results
            
            # Update UI to show we're starting
            Clock.schedule_once(
                lambda dt: progress_popup.update_progress(
                    0, f"Starting view process for {count} views..."
                )
            )
            
            # Process views in a more controlled manner
            try:
                # Process one view at a time for better control and UI feedback
                for idx in range(count):
                    # Check if operation was cancelled
                    if progress_popup.should_cancel:
                        Clock.schedule_once(
                            lambda dt: progress_popup.update_progress(
                                idx, f"Operation cancelled at view {idx+1}/{count}"
                            )
                        )
                        break
                    
                    proxy = get_random_proxy(proxies) if proxies else None
                    
                    # Update UI
                    Clock.schedule_once(
                        lambda dt, idx=idx, px=proxy: progress_popup.update_progress(
                            idx, f"Adding view {idx+1}/{count} {'using proxy ' + px if px else 'without proxy'}"
                        )
                    )
                    
                    # Process view with custom duration for better performance
                    try:
                        watch_duration = random.randint(15, 30)  # Shorter duration for testing
                        
                        # Pass the cancellation check callback to add_view
                        result = add_view(url, proxy, watch_duration, cancel_check_callback=check_cancellation)
                        
                        # Check if operation was cancelled during view
                        if progress_popup.should_cancel:
                            Clock.schedule_once(
                                lambda dt: progress_popup.update_progress(
                                    idx, f"Operation cancelled during view {idx+1}/{count}"
                                )
                            )
                            break
                        
                        # Update UI with immediate feedback
                        status = "✓ Success" if result else "✗ Failed"
                        Clock.schedule_once(
                            lambda dt, stat=status, idx=idx: progress_popup.update_progress(
                                idx, f"View {idx+1}: {stat}"
                            )
                        )
                        
                        # Update counters
                        completed += 1
                        if result:
                            successes += 1
                        
                        # Store result details
                        results.append({
                            "view_number": idx + 1,
                            "success": result,
                            "proxy": proxy,
                            "duration": watch_duration
                        })
                        
                    except Exception as e:
                        # Handle errors
                        Clock.schedule_once(
                            lambda dt, err=str(e), idx=idx: progress_popup.update_progress(
                                idx, f"View {idx+1}: Error - {err[:30]}..."
                            )
                        )
                        results.append({
                            "view_number": idx + 1,
                            "success": False,
                            "error": str(e),
                            "proxy": proxy
                        })
                        completed += 1
                    
                    # Small delay to prevent UI freezing
                    time.sleep(0.1)
            
            except Exception as e:
                # Handle any unexpected errors in the main process
                print(f"Error in view processing thread: {str(e)}")
                Clock.schedule_once(
                    lambda dt, err=str(e): progress_popup.update_progress(
                        completed, f"Process error: {err[:50]}..."
                    )
                )
            
            finally:
                # Always update UI with completion status
                Clock.schedule_once(
                    lambda dt: self.show_operation_results(
                        "View", successes, completed, results, progress_popup
                    )
                )
        
        # Start the thread
        threading.Thread(target=process_thread, daemon=True).start()
    
    def show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class CountPopup(Popup):
    count_text = StringProperty("")
    
    def __init__(self, count_text, max_count, url, mode, callback, **kwargs):
        super(CountPopup, self).__init__(**kwargs)
        self.count_text = count_text
        self.max_count = max_count
        self.url = url
        self.mode = mode
        self.callback = callback
        self.use_proxies = False
    
    def set_proxy(self, use_proxies):
        self.use_proxies = use_proxies
    
    def proceed(self):
        try:
            count = int(self.ids.count_input.text)
            if count <= 0:
                return
            
            if count > self.max_count and self.mode != "views":
                popup = Popup(title='Error', content=Label(text=f"Only {self.max_count} accounts available."), size_hint=(0.8, 0.4))
                popup.open()
                return
            
            self.dismiss()
            self.callback(count, self.url, self.use_proxies)
        except ValueError:
            popup = Popup(title='Error', content=Label(text="Please enter a valid number."), size_hint=(0.8, 0.4))
            popup.open()

class ProxyRotationPopup(Popup):
    def __init__(self, callback, **kwargs):
        super(ProxyRotationPopup, self).__init__(**kwargs)
        self.callback = callback
        self.use_rotation = False
    
    def set_rotation(self, use_rotation):
        self.use_rotation = use_rotation
    
    def proceed(self):
        self.dismiss()
        self.callback(self.use_rotation)

class ProxySelectionPopup(Popup):
    def __init__(self, proxies, callback, **kwargs):
        super(ProxySelectionPopup, self).__init__(**kwargs)
        self.proxies = proxies
        self.callback = callback
    
    def select_proxies(self):
        try:
            count = int(self.ids.proxy_count_input.text)
            if count <= 0 or count > len(self.proxies):
                popup = Popup(title='Error', content=Label(text=f"Please enter a number between 1 and {len(self.proxies)}."), size_hint=(0.8, 0.4))
                popup.open()
                return
            
            selected_proxies = self.proxies[:count]
            self.dismiss()
            self.callback(selected_proxies)
        except ValueError:
            popup = Popup(title='Error', content=Label(text="Please enter a valid number."), size_hint=(0.8, 0.4))
            popup.open()

class ProgressPopup(Popup):
    is_complete = BooleanProperty(False)
    should_cancel = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super(ProgressPopup, self).__init__(**kwargs)
        self.start_time = time.time()
        self.update_event = None
        self.total_count = 0
        self.current_count = 0
        
    def start_progress(self, total_count):
        """Start the progress tracking"""
        self.total_count = total_count
        self.current_count = 0
        self.start_time = time.time()
        self.is_complete = False
        self.should_cancel = False
        self.ids.progress_bar.max = total_count
        self.ids.progress_bar.value = 0
        self.ids.progress_count.text = f"0/{total_count}"
        self.ids.close_button.disabled = True
        
        # Start the update timer
        self.update_event = Clock.schedule_interval(self.update_elapsed_time, 1)
    
    def update_elapsed_time(self, dt):
        """Update the elapsed time display"""
        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)
        
        if hours > 0:
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            time_str = f"{mins:02d}:{secs:02d}"
            
        self.ids.elapsed_time.text = f"Elapsed time: {time_str}"
    
    def update_progress(self, current, message=None):
        """Update the progress display"""
        self.current_count = current
        self.ids.progress_bar.value = current
        self.ids.progress_count.text = f"{current}/{self.total_count}"
        
        if message:
            self.ids.progress_label.text = message
    
    def complete(self, message=None):
        """Mark the operation as complete"""
        if self.update_event:
            self.update_event.cancel()
            
        self.is_complete = True
        self.ids.close_button.disabled = False
        self.ids.cancel_button.disabled = True
        
        if message:
            self.ids.progress_label.text = message
        else:
            self.ids.progress_label.text = f"Completed {self.total_count} operations!"
    
    def cancel_operation(self):
        """Cancel the current operation"""
        self.should_cancel = True
        self.ids.cancel_button.disabled = True
        self.ids.progress_label.text = "Cancelling operation..."

class YouTubeGrowthApp(App):
    colors = COLORS  # Add this line to make COLORS accessible in KV
    
    def __init__(self, **kwargs):
        super(YouTubeGrowthApp, self).__init__(**kwargs)
        # Pre-load the account manager to improve startup time
        from account_manageui import AccountManagerScreen, COLORS as ACCOUNT_COLORS
        
        # Make sure the account manager has access to the same colors
        global COLORS
        for key in COLORS:
            if key not in ACCOUNT_COLORS:
                ACCOUNT_COLORS[key] = COLORS[key]
        
        self.account_manager = AccountManagerScreen(name='account_manager')
    
    def on_start(self):
        """Called when the application starts"""
        # Ensure directories exist
        os.makedirs("cookies", exist_ok=True)
        
        # Check if playwright is installed
        try:
            import playwright
        except ImportError:
            # Show a popup about missing dependencies
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            content.add_widget(Label(
                text="Playwright is not installed. Some features may not work properly.",
                halign='center',
                valign='middle',
                text_size=(400, None)
            ))
            install_btn = Button(
                text="Install Now",
                size_hint_y=None,
                height=dp(50)
            )
            install_btn.bind(on_release=self.install_playwright)
            content.add_widget(install_btn)
            
            popup = Popup(
                title="Missing Dependencies",
                content=content,
                size_hint=(0.8, None),
                height=dp(200)
            )
            popup.open()
    
    def install_playwright(self, instance):
        """Install playwright dependencies"""
        try:
            subprocess.Popen([sys.executable, "-m", "pip", "install", "playwright"])
            subprocess.Popen([sys.executable, "-m", "playwright", "install", "chromium"])
            
            content = Label(text="Installation started in background.\nPlease restart the application when complete.")
            popup = Popup(
                title="Installing Dependencies",
                content=content,
                size_hint=(0.8, None),
                height=dp(150)
            )
            popup.open()
        except Exception as e:
            content = Label(text=f"Installation failed: {str(e)}\nPlease install manually.")
            popup = Popup(
                title="Installation Error",
                content=content,
                size_hint=(0.8, None),
                height=dp(150)
            )
            popup.open()
    
    def build(self):
        """Build the application UI"""
        # Load the KV string
        Builder.load_string(kv)
        
        # Configure window
        Window.size = (1000, 600)
        Window.clearcolor = (0.95, 0.95, 0.97, 1)
        Window.maximize()  # Maximize the window when the app starts
        
        # Create screen manager and add screens
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(self.account_manager)
        
        return sm

if __name__ == "__main__":
    YouTubeGrowthApp().run()








