#!/usr/bin/env python3
"""
Test crawler in visible browser mode so you can watch what's happening.
Takes screenshots at key steps.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.crawler.discovery import PageDiscoveryEngine
from src.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

async def test_visible_browser():
    """Test crawler with visible browser."""
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Initialize discovery engine
    discovery = PageDiscoveryEngine(
        base_url="https://www.ducati.com",
        rate_limit_seconds=4.0
    )
    
    # Configure proxy
    proxy = {
        'server': 'http://142.111.48.253:7030',
        'username': 'dwpatyix',
        'password': 'egi9npccxz3j'
    }
    
    print("=" * 80)
    print("Starting visible browser test...")
    print("You should see a browser window open.")
    print("=" * 80)
    
    try:
        # Initialize browser in VISIBLE mode (headless=False)
        print("\n[1/6] Initializing browser (visible mode)...")
        await discovery.initialize_browser(headless=False, proxy=proxy)
        print("✅ Browser initialized")
        
        # Take screenshot
        screenshot_dir = Path("test_screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        await discovery.page.screenshot(path=str(screenshot_dir / "01_initial.png"))
        print(f"📸 Screenshot saved: test_screenshots/01_initial.png")
        
        # Navigate to site
        print("\n[2/6] Navigating to Ducati website...")
        url = "https://www.ducati.com/ca/en/home"
        await discovery.page.goto(url, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(3)
        
        title = await discovery.page.title()
        print(f"📄 Page title: {title}")
        
        if "Access Denied" in title:
            print("❌ Still getting Access Denied - proxy may be blocked")
            await discovery.page.screenshot(path=str(screenshot_dir / "02_access_denied.png"))
            print(f"📸 Screenshot saved: test_screenshots/02_access_denied.png")
            return
        
        await discovery.page.screenshot(path=str(screenshot_dir / "02_page_loaded.png"))
        print(f"📸 Screenshot saved: test_screenshots/02_page_loaded.png")
        print("✅ Page loaded successfully!")
        
        # Handle cookies
        print("\n[3/6] Handling cookie consent...")
        cookie_accepted = await discovery.cookie_handler.accept_cookies(
            custom_selector="#onetrust-accept-btn-handler"
        )
        if cookie_accepted:
            print("✅ Cookies accepted")
        else:
            print("⚠️  No cookie button found (may already be accepted)")
        await asyncio.sleep(2)
        await discovery.page.screenshot(path=str(screenshot_dir / "03_cookies_handled.png"))
        print(f"📸 Screenshot saved: test_screenshots/03_cookies_handled.png")
        
        # Test hamburger menu
        print("\n[4/6] Testing hamburger menu navigation...")
        print("   Looking for hamburger menu...")
        
        hamburger_selectors = [
            '.hamburger[data-js-navtoggle]',
            '[data-js-navtoggle]',
            '.hamburger',
        ]
        
        hamburger_found = False
        for selector in hamburger_selectors:
            try:
                element = await discovery.page.query_selector(selector)
                if element:
                    visible = await element.is_visible()
                    print(f"   Found: {selector} (visible: {visible})")
                    if visible:
                        # Move mouse to element
                        box = await element.bounding_box()
                        if box:
                            await discovery.page.mouse.move(
                                box['x'] + box['width'] / 2,
                                box['y'] + box['height'] / 2
                            )
                            await asyncio.sleep(0.5)
                        
                        await element.click()
                        print("   ✅ Clicked hamburger menu")
                        hamburger_found = True
                        await asyncio.sleep(2)
                        await discovery.page.screenshot(path=str(screenshot_dir / "04_hamburger_opened.png"))
                        print(f"   📸 Screenshot saved: test_screenshots/04_hamburger_opened.png")
                        break
            except Exception as e:
                print(f"   Error with {selector}: {e}")
                continue
        
        if not hamburger_found:
            print("   ❌ Could not find hamburger menu")
            await discovery.page.screenshot(path=str(screenshot_dir / "04_hamburger_not_found.png"))
            return
        
        # Test BIKES link
        print("\n[5/6] Testing BIKES link...")
        bikes_selectors = [
            'a[data-js-navlv2-trigger]:has-text("BIKES")',
            'a:has-text("BIKES")',
            '[data-js-navlv2-trigger]:has-text("BIKES")',
        ]
        
        bikes_found = False
        for selector in bikes_selectors:
            try:
                await asyncio.sleep(0.5)
                element = await discovery.page.query_selector(selector)
                if element:
                    visible = await element.is_visible()
                    print(f"   Found: {selector} (visible: {visible})")
                    if visible:
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        
                        box = await element.bounding_box()
                        if box:
                            await discovery.page.mouse.move(
                                box['x'] + box['width'] / 2,
                                box['y'] + box['height'] / 2
                            )
                            await asyncio.sleep(0.2)
                        
                        await element.click()
                        print("   ✅ Clicked BIKES link")
                        bikes_found = True
                        await asyncio.sleep(2)
                        await discovery.page.screenshot(path=str(screenshot_dir / "05_bikes_opened.png"))
                        print(f"   📸 Screenshot saved: test_screenshots/05_bikes_opened.png")
                        break
            except Exception as e:
                print(f"   Error with {selector}: {e}")
                continue
        
        if not bikes_found:
            print("   ❌ Could not find BIKES link")
            await discovery.page.screenshot(path=str(screenshot_dir / "05_bikes_not_found.png"))
            return
        
        # Expand categories and collect links
        print("\n[6/6] Expanding categories and collecting links...")
        await asyncio.sleep(1)
        
        # Expand first few categories
        titles = await discovery.page.query_selector_all('div.title')
        print(f"   Found {len(titles)} category titles")
        
        for i, title in enumerate(titles[:5]):  # Expand first 5
            try:
                class_attr = await title.get_attribute('class') or ''
                if '-opened' not in class_attr:
                    text = await title.inner_text()
                    print(f"   Expanding: {text}")
                    await title.click()
                    await asyncio.sleep(1.5)
            except Exception as e:
                print(f"   Error expanding category: {e}")
        
        await discovery.page.screenshot(path=str(screenshot_dir / "06_categories_expanded.png"))
        print(f"   📸 Screenshot saved: test_screenshots/06_categories_expanded.png")
        
        # Find bike links
        bike_links = await discovery.page.query_selector_all('a[href*="/bikes/"]')
        print(f"\n✅ Found {len(bike_links)} bike links!")
        
        # Show first 10 links
        print("\nFirst 10 bike links found:")
        for i, link in enumerate(bike_links[:10]):
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                print(f"   [{i+1}] {href} - {text[:50]}")
            except:
                pass
        
        # Final screenshot
        await discovery.page.screenshot(path=str(screenshot_dir / "07_final.png"))
        print(f"\n📸 Final screenshot saved: test_screenshots/07_final.png")
        
        print("\n" + "=" * 80)
        print("✅ Test complete! Check the browser window and screenshots.")
        print("=" * 80)
        print("\nScreenshots saved in: test_screenshots/")
        print("\nPress Enter in the terminal to close the browser...")
        
        # Keep browser open for 30 seconds so user can see
        await asyncio.sleep(30)
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        await discovery.page.screenshot(path=str(screenshot_dir / "error.png"))
        print(f"❌ Error occurred. Screenshot saved: test_screenshots/error.png")
    finally:
        print("\nClosing browser...")
        await discovery.close_browser()
        print("✅ Browser closed")

if __name__ == "__main__":
    asyncio.run(test_visible_browser())


