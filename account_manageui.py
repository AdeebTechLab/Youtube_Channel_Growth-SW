import os
import sys

# Force Kivy to use PIL text provider instead of SDL2
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

# Import proxy functionality
from proxy_rotator import add_proxies, load_proxies

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
                size_hint_x: 0.4
            
            RoundedButton:
                text: "Add Account"
                size_hint_x: 0.3
                background_color: get_color_from_hex(app.colors['accent'])
                color: 1, 1, 1, 1
                bold: True
                on_release: root.add_account()
        
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
    
    Label:
        text: "Available Accounts"
        font_size: dp(18)
        color: get_color_from_hex(app.colors['primary'])
        size_hint_y: None
        height: dp(30)
        bold: True
    
    ScrollView:
        do_scroll_x: False
        
        GridLayout:
            id: accounts_grid
            cols: 1
            spacing: dp(8)
            padding: dp(5)
            size_hint_y: None
            height: self.minimum_height

<ProxiesTab>:
    orientation: 'vertical'
    spacing: dp(15)
    
    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(10)
        
        TextInput:
            id: proxy_input
            hint_text: "Enter proxy (http://ip:port)"
            multiline: False
            size_hint_x: 0.7
            padding: [dp(10), dp(10), dp(10), dp(10)]
            font_size: dp(16)
            background_color: get_color_from_hex(app.colors['card'])
            foreground_color: get_color_from_hex(app.colors['text'])
            cursor_color: get_color_from_hex(app.colors['primary'])
        
        RoundedButton:
            text: "Add Proxy"
            size_hint_x: 0.3
            background_color: get_color_from_hex(app.colors['primary'])
            color: 1, 1, 1, 1
            font_size: dp(16)
            bold: True
            on_release: root.add_proxy()
    
    Label:
        text: "Available Proxies"
        font_size: dp(18)
        color: get_color_from_hex(app.colors['primary'])
        size_hint_y: None
        height: dp(30)
        bold: True
    
    ScrollView:
        do_scroll_x: False
        
        GridLayout:
            id: proxies_grid
            cols: 1
            spacing: dp(8)
            padding: dp(5)
            size_hint_y: None
            height: self.minimum_height
"""

# Load the KV string when the module is imported
Builder.load_string(kv)


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
            elif tab_name == "proxies":
                content_area.add_widget(self.proxies_tab)

    def back_to_main(self):
        self.manager.current = "main"

    def add_account(self):
        try:
            # Use Popen instead of run to avoid blocking the UI
            # The /c flag tells cmd to execute the command and then terminate
            process = subprocess.Popen(
                [sys.executable, "save_cookies.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Schedule a check to reload accounts when the process is done
            def check_process(dt):
                if process.poll() is not None:
                    self.accounts_tab.load_accounts()
                    return False  # Stop the scheduling
                return True  # Continue checking
                
            Clock.schedule_interval(check_process, 1)
        except Exception as e:
            print(f"Error launching save_cookies.py: {str(e)}")
            # Show error popup
            content = Label(text=f"Error launching account creation: {str(e)}")
            popup = Popup(title='Error', content=content, size_hint=(0.8, 0.4))
            popup.open()
        
    def on_enter(self):
        # This is called when the screen is entered
        # Ensure tabs are properly initialized
        Clock.schedule_once(self._init_ui, 0)


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

        accounts = [
            f.replace(".json", "") for f in os.listdir("cookies") if f.endswith(".json")
        ]

        for i, account in enumerate(accounts):
            row = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10), padding=[dp(5), dp(5), dp(5), dp(5)])
            
            # Add a background to the row
            with row.canvas.before:
                Color(rgba=get_color_from_hex(COLORS["background"]))
                rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(5)])
            
            # Update rectangle position when the widget position changes
            def update_rect(instance, value):
                rect.pos = instance.pos
                rect.size = instance.size
            
            row.bind(pos=update_rect, size=update_rect)
            
            # Account name label with better styling
            label = Label(
                text=account,
                size_hint_x=0.7,
                color=get_color_from_hex(COLORS["text"]),
                font_size=dp(16),
                bold=True,
                halign='left',
                valign='middle',
                text_size=(None, None)
            )
            row.add_widget(label)

            # Delete button with rounded style
            from kivy.factory import Factory
            RoundedButton = Factory.RoundedButton
            delete_btn = RoundedButton(
                text="Delete",
                size_hint_x=0.3,
                background_color=get_color_from_hex(COLORS["accent"]),
                color=(1, 1, 1, 1),
                bold=True,
                font_size=dp(14)
            )
            delete_btn.account_name = account  # Store account name as attribute
            delete_btn.bind(on_release=self.delete_account)
            row.add_widget(delete_btn)

            accounts_grid.add_widget(row)

    def delete_account(self, instance):
        file_path = os.path.join("cookies", f"{instance.account_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            self.load_accounts()  # Refresh the list


class ProxiesTab(BoxLayout):
    def __init__(self, **kwargs):
        super(ProxiesTab, self).__init__(**kwargs)
        Clock.schedule_once(self._init_ui, 0)

    def _init_ui(self, dt):
        self.load_proxies()

    def load_proxies(self):
        if not hasattr(self, "ids") or "proxies_grid" not in self.ids:
            return

        proxies_grid = self.ids.proxies_grid
        proxies_grid.clear_widgets()

        if not os.path.exists("proxies.txt"):
            with open("proxies.txt", "w") as f:
                pass
            return

        with open("proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]

        for i, proxy in enumerate(proxies):
            row = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10), padding=[dp(5), dp(5), dp(5), dp(5)])
            
            # Add a background to the row
            with row.canvas.before:
                Color(rgba=get_color_from_hex(COLORS["background"]))
                rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(5)])
            
            # Update rectangle position when the widget position changes
            def update_rect(instance, value):
                rect.pos = instance.pos
                rect.size = instance.size
            
            row.bind(pos=update_rect, size=update_rect)
            
            # Proxy URL label with better styling
            label = Label(
                text=proxy,
                size_hint_x=0.7,
                color=get_color_from_hex(COLORS["text"]),
                font_size=dp(16),
                bold=True,
                halign='left',
                valign='middle',
                text_size=(None, None)
            )
            row.add_widget(label)

            # Delete button with rounded style
            from kivy.factory import Factory
            RoundedButton = Factory.RoundedButton
            delete_btn = RoundedButton(
                text="Delete",
                size_hint_x=0.3,
                background_color=get_color_from_hex(COLORS["accent"]),
                color=(1, 1, 1, 1),
                bold=True,
                font_size=dp(14)
            )
            delete_btn.proxy_url = proxy  # Store proxy URL as attribute
            delete_btn.bind(on_release=self.delete_proxy)
            row.add_widget(delete_btn)

            proxies_grid.add_widget(row)

    def add_proxy(self):
        if not hasattr(self, "ids") or "proxy_input" not in self.ids:
            return

        proxy = self.ids.proxy_input.text.strip()
        if not proxy:
            return

        # Add the proxy to the file
        with open("proxies.txt", "a") as f:
            f.write(proxy + "\n")

        self.ids.proxy_input.text = ""  # Clear the input
        self.load_proxies()  # Refresh the list

    def delete_proxy(self, instance):
        # Read all proxies
        with open("proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]

        # Remove the selected proxy
        if instance.proxy_url in proxies:
            proxies.remove(instance.proxy_url)

        # Write back the remaining proxies
        with open("proxies.txt", "w") as f:
            for proxy in proxies:
                f.write(proxy + "\n")

        self.load_proxies()  # Refresh the list


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

