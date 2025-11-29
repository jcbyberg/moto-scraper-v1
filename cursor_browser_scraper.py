#!/usr/bin/env python3
"""
Scraper that uses Cursor IDE's browser for visualization.
Uses Playwright for actual scraping but provides Cursor browser integration.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
try:
    from playwright_stealth.stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    Stealth = None

from src.extractors.data_extractor import DataExtractor
from src.extractors.image_extractor import ImageExtractor
from src.utils.cookie_handler import CookieHandler
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def scrape_with_cursor_browser(url: str, headless: bool = True, proxy: Optional[Dict[str, str]] = None):
    """
    Scrape a page using Playwright but designed to work with Cursor browser.
    Provides detailed console output that matches what you see in Cursor browser.
    
    Args:
        url: URL to scrape
        headless: Whether to run browser in headless mode (False = visible browser, harder to detect)
        proxy: Optional proxy configuration dict with 'server', optionally 'username' and 'password'
    """
    
    print("=" * 80)
    print("DUCATI SCRAPER - Console Output Mode")
    print("=" * 80)
    print(f"\n🎯 Scraping: {url}")
    print("\n💡 TIP: Open this URL in Cursor's browser to watch along!")
    print(f"   URL: {url}\n")
    
    async with async_playwright() as p:
        # Use headless browser with stealth configuration to avoid bot detection
        # Non-headless mode (headless=False) is harder to detect but requires display access
        if not headless:
            print("   ℹ️  Running in visible mode (headless=False) - this may help bypass detection")
        
        # Configure launch options
        launch_options = {
            'headless': headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        }
        
        # Add proxy if configured
        if proxy:
            launch_options['proxy'] = proxy
            proxy_info = proxy.get('server', 'unknown')
            if 'username' in proxy:
                proxy_info += f" (user: {proxy['username']})"
            print(f"   🌐 Using proxy: {proxy_info}")
        else:
            print("   ℹ️  No proxy configured - using server's IP address")
            print("   💡 If you get 403 errors, try using --proxy or PROXY env var")
        
        browser = await p.chromium.launch(**launch_options)
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
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
        )
        
        # Apply playwright-stealth plugin (equivalent to puppeteer-extra-plugin-stealth)
        if STEALTH_AVAILABLE:
            print("   🥷 Applying playwright-stealth plugin...")
            stealth = Stealth()
            await stealth.apply_stealth_async(context)
            print("   ✓ Stealth plugin applied successfully")
        else:
            print("   ⚠️  Using manual stealth features (playwright-stealth not available)")
            print("   💡 Install with: pip install playwright-stealth")
        
        # Remove webdriver property and add comprehensive stealth features to avoid bot detection
        # (These are in addition to playwright-stealth for extra protection)
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock plugins with realistic plugin data
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ];
                    return plugins;
                }
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override chrome runtime
            window.chrome = {
                runtime: {}
            };
            
            // Mock platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // Override permissions API
            const originalPermissions = navigator.permissions;
            Object.defineProperty(navigator, 'permissions', {
                get: () => originalPermissions
            });
            
            // Add realistic hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // Add realistic device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
        """)
        
        page = await context.new_page()
        
        try:
            # Step 1: Navigate (with session establishment strategy)
            print("📍 Step 1: Establishing session...")
            
            # Strategy: Visit homepage first to establish a session, then navigate to target
            # This is more human-like and can help bypass some bot detection
            try:
                # Extract base domain
                parsed = urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                homepage_url = f"{base_url}/ww/en/home"
                
                print(f"   → Visiting homepage first: {homepage_url}")
                await asyncio.sleep(0.5)
                homepage_response = await page.goto(
                    homepage_url, 
                    wait_until='domcontentloaded', 
                    timeout=30000
                )
                
                if homepage_response and homepage_response.status == 403:
                    print("   ⚠️  Homepage also blocked (403)")
                    # Continue anyway - might be able to access target page
                else:
                    print("   ✓ Homepage loaded, establishing session...")
                    await asyncio.sleep(2)  # Wait for session cookies/JS to initialize
                    
                    # Handle cookies on homepage if present
                    cookie_handler = CookieHandler(page)
                    await cookie_handler.accept_cookies()
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Homepage visit failed, continuing to target: {e}")
            
            # Check what IP we're using (helpful for debugging)
            try:
                print("   → Checking IP address...")
                ip_check_page = await context.new_page()
                ip_response = await ip_check_page.goto("https://api.ipify.org?format=json", timeout=10000)
                if ip_response and ip_response.status == 200:
                    ip_data = await ip_check_page.evaluate("() => document.body.textContent")
                    import json
                    ip_info = json.loads(ip_data)
                    current_ip = ip_info.get('ip', 'unknown')
                    print(f"   ✓ Current IP: {current_ip}")
                    print(f"   💡 If this IP differs from your local browser's IP, that may cause 403 errors")
                await ip_check_page.close()
            except Exception as e:
                logger.debug(f"Could not check IP: {e}")
            
            # Now navigate to target page
            print(f"\n📍 Step 2: Navigating to target page...")
            await asyncio.sleep(1)  # Human-like delay between navigations
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            # Wait a bit for any dynamic content to load
            await asyncio.sleep(2)
            
            if response:
                status = response.status
                print(f"   ✓ HTTP Status: {status}")
                if status == 403:
                    print("   ⚠️  Access Denied - Site may be blocking automated access")
                    print("   💡 Solutions:")
                    print("      • Use --proxy to route through a different IP (residential proxy recommended)")
                    print("      • Set PROXY environment variable")
                    print("      • Try running with headless=False (requires display)")
                    print("      • Check if your server's IP is blocked (different from your local browser IP)")
                    print("      • Try accessing the URL manually in a browser first to verify it works")
                    return
            title = await page.title()
            print(f"   ✓ Page Title: {title}")
            await asyncio.sleep(2)
            
            # Step 3: Handle cookies (if not already handled)
            print("\n🍪 Step 3: Handling cookies...")
            cookie_handler = CookieHandler(page)
            cookies_accepted = await cookie_handler.accept_cookies()
            if cookies_accepted:
                print("   ✓ Cookies accepted")
            else:
                print("   ⚠ No cookie banner found")
            await asyncio.sleep(1)
            
            # Step 4: Extract content
            print("\n📝 Step 4: Extracting content...")
            print("   → Expanding accordions...")
            print("   → Navigating carousels...")
            print("   → Extracting text content...")
            
            data_extractor = DataExtractor()
            data = await data_extractor.extract_from_page(page, 'main')
            
            print(f"\n   ✓ Specifications: {len(data.get('specifications', {}))} found")
            if data.get('specifications'):
                print("   Sample specs:")
                for i, (key, value) in enumerate(list(data['specifications'].items())[:3], 1):
                    val_preview = value[:50] + "..." if len(value) > 50 else value
                    print(f"     {i}. {key}: {val_preview}")
            
            print(f"   ✓ Features: {len(data.get('features', []))} found")
            if data.get('features'):
                print("   Sample features:")
                for i, feature in enumerate(data['features'][:3], 1):
                    feat_preview = feature[:60] + "..." if len(feature) > 60 else feature
                    print(f"     {i}. {feat_preview}")
            
            desc = data.get('description', '')
            print(f"   ✓ Description: {len(desc)} characters")
            
            if data.get('content_sections'):
                sections = data['content_sections']
                print(f"   ✓ Content sections: {list(sections.keys())}")
                for key, value in sections.items():
                    if value and isinstance(value, str):
                        print(f"     • {key}: {len(value)} chars")
            
            # Step 5: Extract images
            print("\n🖼️  Step 5: Extracting images...")
            print("   → Finding all image elements...")
            print("   → Expanding accordions for hidden images...")
            print("   → Navigating carousels...")
            print("   → Extracting from picture elements...")
            print("   → Extracting video posters...")
            print("   → Extracting background images...")
            
            image_extractor = ImageExtractor()
            model = url.split('/')[-1] if '/' in url else 'unknown'
            year = 2024
            
            images = await image_extractor.extract_images(page, model, year)
            print(f"\n   ✓ Total images found: {len(images)}")
            
            if images:
                # Categorize by type
                by_type = {}
                for img in images:
                    img_type = img.get('type', 'unknown')
                    by_type[img_type] = by_type.get(img_type, 0) + 1
                
                print("   Image breakdown:")
                for img_type, count in sorted(by_type.items()):
                    print(f"     • {img_type}: {count}")
                
                print("\n   Sample image URLs:")
                for i, img in enumerate(images[:5], 1):
                    url_short = img['url'][:70] + "..." if len(img['url']) > 70 else img['url']
                    print(f"     {i}. {url_short}")
            
            # Step 6: Show content preview
            print("\n" + "=" * 80)
            print("📄 CONTENT PREVIEW")
            print("=" * 80)
            
            if desc:
                preview = desc[:800] + "\n..." if len(desc) > 800 else desc
                print("\nDescription:")
                print("-" * 80)
                print(preview)
            
            if data.get('content_sections'):
                print("\nContent Sections:")
                print("-" * 80)
                for key, value in data['content_sections'].items():
                    if value and isinstance(value, str):
                        preview = value[:300] + "..." if len(value) > 300 else value
                        print(f"\n{key.upper()}:")
                        print(f"  {preview}")
            
            print("\n" + "=" * 80)
            print("✅ SCRAPING COMPLETE!")
            print("=" * 80)
            print(f"\nSummary:")
            print(f"  • Page: {title}")
            print(f"  • Specifications: {len(data.get('specifications', {}))}")
            print(f"  • Features: {len(data.get('features', []))}")
            print(f"  • Images: {len(images)}")
            print(f"  • Description: {len(desc)} characters")
            print(f"  • Content sections: {len(data.get('content_sections', {}))}")
            print("\n💡 To see the page visually, open it in Cursor's browser!")
            print(f"   URL: {url}\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


async def main():
    """Main function."""
    import sys
    import os
    
    # Check for headless mode override
    headless_mode = os.getenv('HEADLESS', 'true').lower() == 'true'
    if '--no-headless' in sys.argv:
        headless_mode = False
        sys.argv.remove('--no-headless')
    elif '--headless' in sys.argv:
        headless_mode = True
        sys.argv.remove('--headless')
    
    # Parse proxy configuration
    proxy = None
    proxy_arg = None
    
    # Check for --proxy argument
    if '--proxy' in sys.argv:
        idx = sys.argv.index('--proxy')
        if idx + 1 < len(sys.argv):
            proxy_arg = sys.argv[idx + 1]
            sys.argv.pop(idx)  # Remove --proxy
            sys.argv.pop(idx)  # Remove proxy value (now at idx after removing --proxy)
    
    # Check environment variable
    proxy_env = os.getenv('PROXY')
    
    # Use command-line arg if provided, otherwise use env var
    proxy_str = proxy_arg or proxy_env
    
    if proxy_str:
        # Parse proxy URL or host:port format
        if proxy_str.startswith('http://') or proxy_str.startswith('https://'):
            # Full URL format: http://user:pass@host:port
            parsed = urlparse(proxy_str)
            proxy = {
                'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 80}",
            }
            if parsed.username:
                proxy['username'] = parsed.username
            if parsed.password:
                proxy['password'] = parsed.password
        else:
            # host:port format
            if ':' in proxy_str:
                host, port = proxy_str.rsplit(':', 1)
                proxy = {'server': f'http://{host}:{port}'}
            else:
                proxy = {'server': f'http://{proxy_str}:8080'}
        
        # Check for separate username/password env vars
        proxy_user = os.getenv('PROXY_USER')
        proxy_pass = os.getenv('PROXY_PASS')
        if proxy_user:
            proxy['username'] = proxy_user
        if proxy_pass:
            proxy['password'] = proxy_pass
    
    demo_urls = [
        ("1", "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally", "Multistrada V4 Rally"),
        ("2", "https://www.ducati.com/ww/en/bikes/hypermotard/hypermotard-v2", "Hypermotard V2"),
        ("3", "https://www.ducati.com/ww/en/bikes/scrambler", "Scrambler Category"),
        ("4", "https://www.ducati.com/ww/en/stories/travel/road-to-olympus-multistrada-v4-rally", "Travel Story"),
        ("5", "https://www.ducati.com/ww/en/bikes/offroad/desmo250-mx", "Desmo250 MX"),
    ]
    
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        print("\n🚀 DUCATI SCRAPER - Console Mode\n")
        print("Usage: python cursor_browser_scraper.py [URL] [OPTIONS]")
        print("Options:")
        print("  --no-headless: Run with visible browser (may help bypass bot detection)")
        print("  --headless: Run in headless mode (default)")
        print("  --proxy PROXY: Use proxy (format: http://user:pass@host:port or host:port)")
        print("  Environment variables:")
        print("    PROXY: Proxy server (same format as --proxy)")
        print("    PROXY_USER: Proxy username (if not in PROXY URL)")
        print("    PROXY_PASS: Proxy password (if not in PROXY URL)")
        print("    HEADLESS: Set to 'false' to run with visible browser\n")
        print("Available demo pages:")
        for num, url, name in demo_urls:
            print(f"  {num}. {name}")
        
        try:
            choice = input("\nEnter number (1-5) or URL (or press Enter for 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = ""
        
        if choice.isdigit() and 1 <= int(choice) <= len(demo_urls):
            target_url = demo_urls[int(choice) - 1][1]
        elif choice:
            target_url = choice
        else:
            target_url = demo_urls[0][1]
    
    # Update the function to accept headless parameter
    # For now, we'll modify the function to check an environment variable
    await scrape_with_cursor_browser(target_url, headless=headless_mode, proxy=proxy)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")

