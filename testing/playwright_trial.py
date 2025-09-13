"""
Simple Playwright test script for Purdue Brightspace
"""

from playwright.sync_api import sync_playwright
import time


def test_brightspace_access():
    """Test basic access to Purdue Brightspace"""
    
    with sync_playwright() as p:
        # Launch browser (keep visible for manual interaction)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to Purdue Brightspace
            print("Navigating to Purdue Brightspace...")
            page.goto("https://purdue.brightspace.com")
            
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            
            # Check if we can see the login form
            username_field = page.query_selector("#username")
            if username_field:
                print("✓ Found username field - login form is accessible")
            else:
                print("✗ Username field not found")
            
            # Take a screenshot for debugging
            page.screenshot(path="brightspace_login.png")
            print("Screenshot saved as brightspace_login.png")
            
            # Wait a bit to see the page
            time.sleep(3)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    test_brightspace_access()
