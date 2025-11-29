#!/usr/bin/env python3
"""
Test crawler with click tracking - logs all clicks and mouse movements.
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

async def test_with_click_tracking():
    """Test crawler with visible browser and click tracking."""
    
    setup_logging(level="INFO")
    
    # Configure proxy
    proxy = {
        'server': 'http://142.111.48.253:7030',
        'username': 'dwpatyix',
        'password': 'egi9npccxz3j'
    }
    
    # Pass proxy to PageDiscoveryEngine constructor
    discovery = PageDiscoveryEngine(
        base_url="https://www.ducati.com",
        rate_limit_seconds=4.0,
        proxy=proxy
    )
    
    print("=" * 80)
    print("Starting test with CLICK TRACKING")
    print("All clicks and mouse movements will be logged")
    print("=" * 80)
    
    try:
        # Run in headless mode (server doesn't have X server)
        # But we'll still track all clicks and take screenshots
        await discovery.initialize_browser(headless=True)
        
        # Set up click tracking
        await discovery.page.evaluate("""
            // Track all clicks
            document.addEventListener('click', function(e) {
                const target = e.target;
                const info = {
                    tag: target.tagName,
                    id: target.id || '',
                    class: target.className || '',
                    text: target.innerText?.substring(0, 50) || '',
                    href: target.href || '',
                    x: e.clientX,
                    y: e.clientY,
                    timestamp: Date.now()
                };
                console.log('CLICK TRACKED:', JSON.stringify(info));
            }, true);
            
            // Track mouse movements (throttled)
            let lastMoveLog = 0;
            document.addEventListener('mousemove', function(e) {
                const now = Date.now();
                if (now - lastMoveLog > 500) { // Log every 500ms
                    console.log('MOUSE MOVE:', e.clientX, e.clientY);
                    lastMoveLog = now;
                }
            });
            
            // Track scrolling (throttled)
            let lastScrollLog = 0;
            window.addEventListener('scroll', function(e) {
                const now = Date.now();
                if (now - lastScrollLog > 300) { // Log every 300ms
                    const scrollInfo = {
                        scrollX: window.scrollX || window.pageXOffset,
                        scrollY: window.scrollY || window.pageYOffset,
                        documentHeight: document.documentElement.scrollHeight,
                        viewportHeight: window.innerHeight,
                        timestamp: Date.now()
                    };
                    console.log('SCROLL TRACKED:', JSON.stringify(scrollInfo));
                    lastScrollLog = now;
                }
            }, { passive: true });
            
            // Track programmatic scrolling (window.scrollTo, element.scrollIntoView, etc.)
            const originalScrollTo = window.scrollTo;
            window.scrollTo = function(...args) {
                console.log('SCROLL TO CALLED:', JSON.stringify(args));
                return originalScrollTo.apply(this, args);
            };
            
            const originalScrollBy = window.scrollBy;
            window.scrollBy = function(...args) {
                console.log('SCROLL BY CALLED:', JSON.stringify(args));
                return originalScrollBy.apply(this, args);
            };
        """)
        
        print("\n✅ Click, mouse movement, and scroll tracking enabled - all events will be logged")
        
        # Set up console listener BEFORE navigation
        event_log = []
        
        def handle_console(msg):
            text = msg.text
            if any(keyword in text for keyword in ['CLICK TRACKED', 'MOUSE MOVE', 'SCROLL TRACKED', 'SCROLL TO', 'SCROLL BY']):
                event_log.append(text)
                # Color code different event types
                if 'CLICK' in text:
                    print(f"🖱️  {text}")
                elif 'MOUSE MOVE' in text:
                    print(f"🖱️  {text}")
                elif 'SCROLL' in text:
                    print(f"📜 {text}")
        
        discovery.page.on("console", handle_console)
        
        # Navigate
        url = "https://www.ducati.com/ca/en/home"
        print(f"\n[1] Navigating to {url}...")
        response = await discovery.page.goto(url, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(3)
        
        title = await discovery.page.title()
        print(f"   Page title: {title}")
        if response:
            print(f"   Status: {response.status}")
        
        if "Access Denied" in title:
            print("   ❌ Still getting Access Denied")
            return
        
        print("\n[2] Page loaded. Now testing automated navigation...")
        
        # Test automated clicks - click hamburger menu
        print("\n[3] Testing hamburger menu click...")
        hamburger_selectors = [
            '.hamburger[data-js-navtoggle]',
            '[data-js-navtoggle]',
            '.hamburger',
        ]
        
        for selector in hamburger_selectors:
            try:
                element = await discovery.page.query_selector(selector)
                if element and await element.is_visible():
                    print(f"   Found hamburger: {selector}")
                    await element.click()
                    print("   ✅ Clicked hamburger menu")
                    await asyncio.sleep(2)
                    break
            except:
                continue
        
        # Test clicking MODELS/BIKES
        print("\n[4] Testing MODELS/BIKES click...")
        models_selectors = [
            'a:has-text("MODELS")',
            'a:has-text("BIKES")',
            '[data-js-navlv2-trigger]:has-text("BIKES")',
        ]
        
        for selector in models_selectors:
            try:
                await asyncio.sleep(1)
                element = await discovery.page.query_selector(selector)
                if element and await element.is_visible():
                    print(f"   Found: {selector}")
                    await element.click()
                    print("   ✅ Clicked MODELS/BIKES")
                    await asyncio.sleep(2)
                    break
            except:
                continue
        
        # Test scrolling
        print("\n[5] Testing scrolling...")
        await discovery.page.evaluate("window.scrollTo(0, 300)")
        await asyncio.sleep(1)
        await discovery.page.evaluate("window.scrollTo(0, 600)")
        await asyncio.sleep(1)
        await discovery.page.evaluate("window.scrollBy(0, 200)")
        await asyncio.sleep(1)
        print("   ✅ Performed test scrolls")
        
        # Wait a bit to collect any additional events
        await asyncio.sleep(3)
        
        # Categorize events
        clicks = [e for e in event_log if 'CLICK' in e]
        scrolls = [e for e in event_log if 'SCROLL' in e]
        mouse_moves = [e for e in event_log if 'MOUSE MOVE' in e]
        
        print(f"\n✅ Collected {len(event_log)} total events:")
        print(f"   🖱️  Clicks: {len(clicks)}")
        print(f"   📜 Scrolls: {len(scrolls)}")
        print(f"   🖱️  Mouse moves: {len(mouse_moves)}")
        
        print("\nEvent log summary (first 30 events):")
        for i, event in enumerate(event_log[:30], 1):
            print(f"  {i}. {event}")
        
        # Take final screenshot
        screenshot_dir = Path("test_screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        await discovery.page.screenshot(path=str(screenshot_dir / "click_tracking_final.png"))
        print(f"\n📸 Final screenshot: test_screenshots/click_tracking_final.png")
        
        print("\n" + "=" * 80)
        print("Test complete! Check the logs above to see all tracked clicks.")
        print("=" * 80)
        
        # Keep browser open a bit longer
        await asyncio.sleep(10)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await discovery.close_browser()

if __name__ == "__main__":
    asyncio.run(test_with_click_tracking())

