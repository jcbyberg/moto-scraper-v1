"""
Test script for navigating a specific motorcycle OEM website.
Handles cookie consent and model dropdown navigation.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
from src.utils.cookie_handler import CookieHandler, NavigationHandler
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def navigate_to_first_model(base_url: str):
    """
    Navigate to the first model on the motorcycle OEM site.
    
    Steps:
    1. Navigate to base URL
    2. Accept cookies
    3. Click MODELS dropdown
    4. Select first model
    5. Wait for page to load
    """
    async with async_playwright() as p:
        # Launch browser (headless=False for debugging)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            logger.info(f"Navigating to {base_url}")
            await page.goto(base_url, wait_until='domcontentloaded')
            
            # Initialize handlers
            cookie_handler = CookieHandler(page)
            nav_handler = NavigationHandler(page)
            
            # Step 1: Accept cookies
            logger.info("Attempting to accept cookies...")
            cookie_accepted = await cookie_handler.accept_cookies(
                custom_selector="#onetrust-accept-btn-handler"
            )
            
            if cookie_accepted:
                logger.info("✓ Cookies accepted")
            else:
                logger.warning("⚠ Cookie button not found, continuing...")
            
            # Wait a bit for page to settle
            await page.wait_for_timeout(1000)
            
            # Step 2: Click MODELS dropdown
            logger.info("Clicking MODELS dropdown...")
            models_dropdown_clicked = await nav_handler.click_dropdown(
                selector='a[data-js-shortcutnav=""]:has-text("MODELS")',
                wait_for_visible=True
            )
            
            if not models_dropdown_clicked:
                # Try alternative selector
                models_dropdown_clicked = await nav_handler.click_dropdown(
                    selector='a:has-text("MODELS")',
                    wait_for_visible=True
                )
            
            if not models_dropdown_clicked:
                logger.error("Could not find MODELS dropdown")
                return False
            
            logger.info("✓ MODELS dropdown clicked")
            
            # Wait for dropdown menu to appear
            await page.wait_for_timeout(500)
            
            # Step 3: Select first model
            logger.info("Selecting first model from dropdown...")
            
            # Try to find first model link in dropdown
            # Common patterns for dropdown menus
            model_selectors = [
                ".dropdown-menu a:first-child",
                "[role='menu'] a:first-child",
                ".nav-dropdown a:first-child",
                "ul.dropdown-menu > li:first-child > a",
                "a[href*='/motorcycles/']:first-of-type",
            ]
            
            model_selected = False
            for selector in model_selectors:
                try:
                    first_model = await page.query_selector(selector)
                    if first_model and await first_model.is_visible():
                        model_text = await first_model.inner_text()
                        model_href = await first_model.get_attribute('href')
                        logger.info(f"Found first model: {model_text} ({model_href})")
                        
                        await first_model.click()
                        model_selected = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not model_selected:
                # Fallback: try clicking first visible link in dropdown area
                try:
                    dropdown_area = await page.query_selector(
                        ".dropdown-menu, [role='menu'], .nav-dropdown"
                    )
                    if dropdown_area:
                        first_link = await dropdown_area.query_selector("a")
                        if first_link:
                            model_text = await first_link.inner_text()
                            await first_link.click()
                            logger.info(f"Selected first model (fallback): {model_text}")
                            model_selected = True
                except Exception as e:
                    logger.error(f"Fallback selection failed: {e}")
            
            if not model_selected:
                logger.error("Could not select first model")
                # Take screenshot for debugging
                await page.screenshot(path="debug_dropdown.png")
                logger.info("Screenshot saved to debug_dropdown.png")
                return False
            
            logger.info("✓ First model selected")
            
            # Step 4: Wait for navigation
            logger.info("Waiting for page to load...")
            await nav_handler.wait_for_navigation(timeout=10000)
            
            # Get final URL
            final_url = page.url
            logger.info(f"✓ Navigation complete: {final_url}")
            
            # Take screenshot of final page
            await page.screenshot(path="debug_final_page.png", full_page=True)
            logger.info("Screenshot saved to debug_final_page.png")
            
            # Wait a bit before closing
            await page.wait_for_timeout(2000)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during navigation: {e}", exc_info=True)
            await page.screenshot(path="debug_error.png")
            return False
            
        finally:
            await browser.close()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test navigation to first model on motorcycle OEM site"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Base URL of the motorcycle OEM website"
    )
    
    args = parser.parse_args()
    
    if not args.url:
        print("Please provide the website URL:")
        print("Usage: python scripts/test_site_navigation.py <URL>")
        print("\nExample:")
        print("  python scripts/test_site_navigation.py https://example-oem.com")
        url = input("\nOr enter URL now: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            return
    else:
        url = args.url
    
    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    success = await navigate_to_first_model(url)
    
    if success:
        print("\n✓ Navigation test completed successfully!")
    else:
        print("\n✗ Navigation test failed. Check logs and screenshots.")


if __name__ == "__main__":
    asyncio.run(main())


