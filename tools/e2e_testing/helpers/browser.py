"""
Browser Automation Helpers
Common functions for Playwright browser operations
"""

from playwright.sync_api import sync_playwright, Page
import time
from typing import Optional, List


class BrowserHelper:
    """Helper class for browser automation with Playwright"""

    def __init__(self, headless: bool = False, base_url: str = "https://omicsintegrationsuite.onff.ru"):
        self.headless = headless
        self.base_url = base_url
        self.browser = None
        self.page = None
        self.playwright = None

    def __enter__(self):
        """Context manager entry - launch browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close browser"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def navigate_to_site(self, timeout: int = 60000):
        """Navigate to the main site"""
        print(f"🌐 Opening site: {self.base_url}...")
        self.page.goto(self.base_url, timeout=timeout)
        time.sleep(3)
        print("✅ Site opened")

    def select_module(self, module_name: str):
        """
        Select a module from sidebar

        Args:
            module_name: Module to select ('proteomics', 'genomics', 'mirna', etc.)
        """
        print(f"\n📍 Navigating to {module_name} module...")

        # Map module names to button names (matching Iteration 139b)
        module_map = {
            'proteomics': '🦠 Протеомика',
            'genomics': '🧬 Геномика',
            'mirna': '🧬 МикроРНК',
            'metabolomics': '🧪 Метаболомика',
            'transcriptomics': '📊 Транскриптомика'
        }

        module_text = module_map.get(module_name.lower(), module_name)

        # Use get_by_role('button') for more reliable selection
        button = self.page.get_by_role('button', name=module_text)
        button.click()
        time.sleep(3)
        self.page.wait_for_load_state("networkidle")
        print(f"✅ {module_name} module opened")

    def get_available_files(self) -> List[str]:
        """Get list of available files from the page"""
        print("\n📂 Checking available files...")
        page_text = self.page.content()

        # This is a simple implementation - can be improved
        # to actually parse the file list from the UI
        files = []
        # Add logic to extract file names from page_text

        print(f"Found {len(files)} files")
        return files

    def select_file(self, file_name: str):
        """
        Select a file by clicking its radio button

        Args:
            file_name: Name of the file to select
        """
        print(f"\n📂 Selecting file: {file_name}...")
        try:
            # Click radio button by file name
            self.page.locator("label").filter(has_text=file_name).first.click()
            time.sleep(2)
            print(f"✅ File selected: {file_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to select file: {e}")
            return False

    def switch_to_tab(self, tab_name: str):
        """
        Switch to a different tab (e.g., 'Обработка', 'Результаты')

        Args:
            tab_name: Tab to switch to (full text with emoji, e.g., '⚙️ Обработка')
        """
        print(f"\n⚙️ Switching to {tab_name} tab...")
        try:
            # Try get_by_text first (more reliable for Streamlit tabs)
            tab = self.page.get_by_text(tab_name, exact=False)
            if tab.count() > 0:
                tab.first.click()
                time.sleep(2)
                print(f"✅ {tab_name} tab opened")
                return True
            else:
                # Fallback to get_by_role
                tab = self.page.get_by_role("tab", name=tab_name)
                tab.click()
                time.sleep(2)
                print(f"✅ {tab_name} tab opened (role method)")
                return True
        except Exception as e:
            print(f"❌ Failed to switch to tab: {e}")
            return False

    def click_button(self, button_text: str, force: bool = True, scroll_to_view: bool = True):
        """
        Click a button by text

        Args:
            button_text: Text on the button (e.g., '🚀 Начать обработку')
            force: Force click even if not visible
            scroll_to_view: Scroll to button before clicking
        """
        print(f"\n🚀 Clicking '{button_text}' button...")
        try:
            # Try get_by_role first (more reliable for buttons)
            button = self.page.get_by_role('button', name=button_text)

            if button.count() == 0:
                # Fallback to get_by_text
                print("   ⚠️ Button not found by role, trying by text...")
                button = self.page.get_by_text(button_text, exact=False).first
            else:
                button = button.first

            # Scroll to view if needed
            if scroll_to_view:
                try:
                    button.scroll_into_view_if_needed(timeout=5000)
                    print("   ✅ Scrolled to button")
                    time.sleep(1)  # Wait for scroll animation
                except:
                    print("   ⚠️ Scroll failed, trying anyway")

            button.click(force=force)
            print("✅ Button clicked!")
            return True
        except Exception as e:
            print(f"❌ Failed to click button: {e}")
            return False

    def wait_for_processing(self, max_wait: int = 600, check_interval: int = 30):
        """
        Wait for processing to complete

        Args:
            max_wait: Maximum wait time in seconds
            check_interval: Check interval in seconds
        """
        print(f"\n⏳ Waiting for processing to complete (max {max_wait}s)...")
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(check_interval)
            elapsed += check_interval
            print(f"   ... {elapsed}s elapsed (max {max_wait}s)")

            # Check page for completion indicators
            page_text = self.page.content()
            if "завершена" in page_text or "Обработка завершена" in page_text:
                print("✅ Processing appears complete!")
                return True

        print("⚠️ Timeout reached")
        return False

    def get_page_content(self) -> str:
        """Get current page content as text"""
        return self.page.content()

    def wait_for_user_input(self):
        """Wait for user to press ENTER (for interactive debugging)"""
        print("\n💡 Press ENTER to close browser...")
        try:
            input()
        except EOFError:
            pass  # Running in background
