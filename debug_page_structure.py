#!/usr/bin/env python3
"""
Debug script to inspect page structure and find working selectors.
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def debug_page():
    """Inspect the Ducati homepage structure."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        page = await context.new_page()
        
        print("Navigating to https://www.ducati.com...")
        # Try different URLs
        urls_to_try = [
            "https://www.ducati.com",
            "https://www.ducati.com/us/en/home",
            "https://www.ducati.com/ca/en/home",
            "https://www.ducati.com/ww/en/home",
        ]
        
        for url in urls_to_try:
            print(f"\nTrying: {url}")
            try:
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                print(f"  Status: {response.status if response else 'None'}")
                await page.wait_for_timeout(3000)
                
                title = await page.title()
                current_url = page.url
                print(f"  Title: {title}")
                print(f"  Final URL: {current_url}")
                
                # Check if we got access denied
                if "Access Denied" in title or "access denied" in (await page.content()).lower():
                    print(f"  ❌ Access Denied on {url}")
                    continue
                else:
                    print(f"  ✅ Successfully loaded {url}")
                    break
            except Exception as e:
                print(f"  Error: {e}")
                continue
        
        # Take screenshot
        screenshot_path = Path("debug_screenshot.png")
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Check for cookie consent
        print("\n=== Checking for cookie consent ===")
        cookie_selectors = [
            "#onetrust-accept-btn-handler",
            "#accept-cookies",
            "button:has-text('Accept')",
            "button:has-text('Accept All')",
        ]
        for selector in cookie_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    visible = await element.is_visible()
                    print(f"  Found: {selector} (visible: {visible})")
                    if visible:
                        await element.click()
                        print(f"  Clicked: {selector}")
                        await page.wait_for_timeout(1000)
                        break
            except Exception as e:
                print(f"  Error with {selector}: {e}")
        
        await page.wait_for_timeout(2000)
        
        # Check for MODELS dropdown
        print("\n=== Checking for MODELS dropdown ===")
        models_selectors = [
            'a[data-js-shortcutnav=""]:has-text("MODELS")',
            'a:has-text("MODELS")',
            'button:has-text("MODELS")',
            '[class*="model"]',
            '[id*="model"]',
            'nav a',
        ]
        for selector in models_selectors:
            try:
                elements = await page.query_selector_all(selector)
                print(f"  {selector}: Found {len(elements)} elements")
                for i, elem in enumerate(elements[:5]):  # Show first 5
                    try:
                        text = await elem.inner_text()
                        href = await elem.get_attribute('href')
                        visible = await elem.is_visible()
                        print(f"    [{i}] text='{text[:50]}' href='{href}' visible={visible}")
                    except:
                        pass
            except Exception as e:
                print(f"  Error with {selector}: {e}")
        
        # Check for search button
        print("\n=== Checking for search button ===")
        search_selectors = [
            'button[aria-label*="search" i]',
            'a[href*="search"]',
            'button:has-text("Search")',
            '[class*="search"] button',
            '[id*="search"]',
        ]
        for selector in search_selectors:
            try:
                elements = await page.query_selector_all(selector)
                print(f"  {selector}: Found {len(elements)} elements")
                for i, elem in enumerate(elements[:3]):
                    try:
                        text = await elem.inner_text()
                        visible = await elem.is_visible()
                        print(f"    [{i}] text='{text[:50]}' visible={visible}")
                    except:
                        pass
            except Exception as e:
                print(f"  Error with {selector}: {e}")
        
        # Extract all links
        print("\n=== Extracting all links ===")
        links = await page.query_selector_all('a[href]')
        print(f"Found {len(links)} total links")
        
        # Filter for bike-related links
        bike_keywords = ['bike', 'model', 'heritage', 'motorcycle']
        bike_links = []
        for link in links:
            try:
                href = await link.get_attribute('href')
                text = await elem.inner_text() if (elem := link) else ""
                if href and any(kw in href.lower() for kw in bike_keywords):
                    bike_links.append((href, text[:50]))
            except:
                continue
        
        print(f"\nFound {len(bike_links)} bike-related links:")
        for href, text in bike_links[:20]:  # Show first 20
            print(f"  {href} - {text}")
        
        # Check page title and URL
        print(f"\n=== Page Info ===")
        print(f"Title: {await page.title()}")
        print(f"URL: {page.url}")
        
        # Get page HTML snippet
        print("\n=== Page HTML snippet (first 2000 chars) ===")
        html = await page.content()
        print(html[:2000])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())

