#!/usr/bin/env python3
"""Test human-like navigation on Ducati site."""

import asyncio
from playwright.async_api import async_playwright

async def test_navigation():
    """Test hamburger menu navigation."""
    proxy = {
        'server': 'http://142.111.48.253:7030',
        'username': 'dwpatyix',
        'password': 'egi9npccxz3j'
    }
    
    async with async_playwright() as p:
        print("Launching browser with proxy...")
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Remove webdriver property
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        # Navigate to site
        print("\n=== Step 1: Navigating to site ===")
        try:
            url = "https://www.ducati.com/ca/en/home"
            print(f"Navigating to {url}...")
            response = await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(3)
            
            title = await page.title()
            print(f"Title: {title}")
            print(f"Status: {response.status if response else 'None'}")
            
            if "Access Denied" in title:
                print("❌ Still getting Access Denied")
                await browser.close()
                return
            
            print("✅ Page loaded successfully!")
            
            # Handle cookies
            print("\n=== Step 2: Handling cookies ===")
            cookie_selectors = [
                "#onetrust-accept-btn-handler",
                "#accept-cookies",
                "button:has-text('Accept')",
            ]
            for selector in cookie_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        await button.click()
                        print(f"✅ Clicked cookie button: {selector}")
                        await asyncio.sleep(1)
                        break
                except:
                    continue
            
            # Test hamburger menu
            print("\n=== Step 3: Testing hamburger menu ===")
            hamburger_selectors = [
                '.hamburger[data-js-navtoggle]',
                '[data-js-navtoggle]',
                '.hamburger',
            ]
            
            hamburger_found = False
            for selector in hamburger_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        visible = await element.is_visible()
                        print(f"Found hamburger: {selector} (visible: {visible})")
                        if visible:
                            box = await element.bounding_box()
                            if box:
                                await page.mouse.move(
                                    box['x'] + box['width'] / 2,
                                    box['y'] + box['height'] / 2
                                )
                                await asyncio.sleep(0.3)
                            
                            await element.click()
                            print(f"✅ Clicked hamburger menu")
                            hamburger_found = True
                            await asyncio.sleep(2)
                            break
                except Exception as e:
                    print(f"Error with {selector}: {e}")
                    continue
            
            if not hamburger_found:
                print("❌ Could not find hamburger menu")
                await browser.close()
                return
            
            # Test BIKES link
            print("\n=== Step 4: Testing BIKES link ===")
            bikes_selectors = [
                'a[data-js-navlv2-trigger]:has-text("BIKES")',
                'a:has-text("BIKES")',
                '[data-js-navlv2-trigger]:has-text("BIKES")',
            ]
            
            bikes_found = False
            for selector in bikes_selectors:
                try:
                    await asyncio.sleep(0.5)
                    element = await page.query_selector(selector)
                    if element:
                        visible = await element.is_visible()
                        print(f"Found BIKES: {selector} (visible: {visible})")
                        if visible:
                            await element.scroll_into_view_if_needed()
                            await asyncio.sleep(0.3)
                            
                            box = await element.bounding_box()
                            if box:
                                await page.mouse.move(
                                    box['x'] + box['width'] / 2,
                                    box['y'] + box['height'] / 2
                                )
                                await asyncio.sleep(0.2)
                            
                            await element.click()
                            print(f"✅ Clicked BIKES link")
                            bikes_found = True
                            await asyncio.sleep(2)
                            break
                except Exception as e:
                    print(f"Error with {selector}: {e}")
                    continue
            
            if not bikes_found:
                print("❌ Could not find BIKES link")
                # Take screenshot for debugging
                await page.screenshot(path="test_navigation_debug.png")
                print("Screenshot saved to test_navigation_debug.png")
            else:
                # Try to find bike links
                print("\n=== Step 5: Finding bike links ===")
                await asyncio.sleep(2)
                
                # Expand categories
                titles = await page.query_selector_all('div.title')
                print(f"Found {len(titles)} category titles")
                for title in titles[:5]:  # Test first 5
                    try:
                        class_attr = await title.get_attribute('class') or ''
                        if '-opened' not in class_attr:
                            text = await title.inner_text()
                            print(f"  Expanding: {text}")
                            await title.click()
                            await asyncio.sleep(1)
                    except:
                        continue
                
                # Find bike links
                bike_links = await page.query_selector_all('a[href*="/bikes/"]')
                print(f"\n✅ Found {len(bike_links)} bike links!")
                
                # Show first 10
                for i, link in enumerate(bike_links[:10]):
                    try:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        print(f"  [{i+1}] {href} - {text[:50]}")
                    except:
                        continue
            
            await browser.close()
            print("\n✅ Navigation test completed!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_navigation())


