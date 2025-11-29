#!/usr/bin/env python3
"""
Demo script to run the crawler with visible browser.
Shows the scraping process in real-time.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from src.extractors.data_extractor import DataExtractor
from src.extractors.image_extractor import ImageExtractor
from src.utils.cookie_handler import CookieHandler
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def demo_scrape_page(url: str):
    """Demo scraping a single page with visible browser."""
    
    print("=" * 80)
    print("DUCATI SCRAPER DEMO - Console Mode")
    print("=" * 80)
    print(f"\n🎯 Scraping: {url}")
    print("\nRunning in headless mode with detailed console output...")
    print("Watch the scraping process step-by-step in the console!\n")
    
    async with async_playwright() as p:
        # Launch browser in headless mode (console-based)
        browser = await p.chromium.launch(
            headless=True,  # Headless browser (console-based)
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to page
            print(f"📍 Navigating to {url}...")
            print("   (This may take a moment...)")
            response = await page.goto(url, wait_until='networkidle', timeout=60000)
            if response:
                print(f"   ✓ Page loaded: {response.status} {response.status_text}")
            await asyncio.sleep(2)
            
            # Get page title
            title = await page.title()
            print(f"   ✓ Page title: {title}")
            
            # Handle cookies
            print("\n🍪 Handling cookies...")
            cookie_handler = CookieHandler(page)
            cookies_accepted = await cookie_handler.accept_cookies()
            if cookies_accepted:
                print("   ✓ Cookies accepted")
            else:
                print("   ⚠ No cookie banner found")
            await asyncio.sleep(1)
            
            # Extract data
            print("\n📝 Extracting content...")
            print("   - Expanding accordions...")
            print("   - Navigating carousels...")
            print("   - Extracting text content...")
            
            data_extractor = DataExtractor()
            data = await data_extractor.extract_from_page(page, 'main')
            
            print(f"\n   ✓ Extracted {len(data.get('specifications', {}))} specifications")
            if data.get('specifications'):
                print("   Sample specs:")
                for i, (key, value) in enumerate(list(data['specifications'].items())[:5], 1):
                    print(f"     {i}. {key}: {value[:60]}...")
            
            print(f"   ✓ Extracted {len(data.get('features', []))} features")
            if data.get('features'):
                print("   Sample features:")
                for i, feature in enumerate(data['features'][:3], 1):
                    print(f"     {i}. {feature[:60]}...")
            
            desc = data.get('description', '')
            print(f"   ✓ Description length: {len(desc)} chars")
            
            if data.get('content_sections'):
                sections = data['content_sections']
                print(f"   ✓ Content sections found: {list(sections.keys())}")
                for key, value in sections.items():
                    if value and isinstance(value, str):
                        print(f"     • {key}: {len(value)} chars")
            
            # Extract images
            print("\n🖼️  Extracting images...")
            print("   - Finding all image elements...")
            print("   - Expanding accordions to reveal hidden images...")
            print("   - Navigating carousels to get all images...")
            print("   - Extracting from picture elements...")
            print("   - Extracting video posters...")
            print("   - Extracting background images...")
            
            image_extractor = ImageExtractor()
            
            # Get model name from URL for context
            model = url.split('/')[-1] if '/' in url else 'unknown'
            year = 2024  # Default year
            
            images = await image_extractor.extract_images(page, model, year)
            print(f"\n   ✓ Found {len(images)} images")
            
            # Categorize images by type
            if images:
                image_types = {}
                for img in images:
                    img_type = img.get('type', 'unknown')
                    image_types[img_type] = image_types.get(img_type, 0) + 1
                
                print("   Image breakdown:")
                for img_type, count in image_types.items():
                    print(f"     • {img_type}: {count}")
                
                print("\n   Sample images:")
                for i, img in enumerate(images[:5], 1):
                    img_type = img.get('type', 'unknown')
                    url_short = img['url'][:70] + "..." if len(img['url']) > 70 else img['url']
                    print(f"     {i}. [{img_type}] {url_short}")
            
            # Show extracted content preview
            print("\n📄 Content Preview:")
            print("-" * 80)
            description = data.get('description', '')
            if description:
                preview = description[:500] + "..." if len(description) > 500 else description
                print(preview)
            
            if data.get('content_sections'):
                print("\n📋 Content Sections:")
                for key, value in data['content_sections'].items():
                    if value and isinstance(value, str):
                        preview = value[:200] + "..." if len(value) > 200 else value
                        print(f"   • {key}: {preview}")
            
            # Show full content preview
            print("\n" + "=" * 80)
            print("📄 FULL CONTENT PREVIEW")
            print("=" * 80)
            
            description = data.get('description', '')
            if description:
                print("\nDescription:")
                print("-" * 80)
                # Show first 1000 chars
                preview = description[:1000] + "\n..." if len(description) > 1000 else description
                print(preview)
            
            if data.get('content_sections'):
                print("\nContent Sections:")
                print("-" * 80)
                for key, value in data['content_sections'].items():
                    if value:
                        if isinstance(value, str):
                            preview = value[:300] + "..." if len(value) > 300 else value
                            print(f"\n{key.upper()}:")
                            print(f"  {preview}")
                        elif isinstance(value, dict):
                            print(f"\n{key.upper()}:")
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, str):
                                    preview = sub_value[:200] + "..." if len(sub_value) > 200 else sub_value
                                    print(f"  {sub_key}: {preview}")
            
            print("\n" + "=" * 80)
            print("✅ DEMO COMPLETE!")
            print("=" * 80)
            print(f"\nSummary:")
            print(f"  • Specifications: {len(data.get('specifications', {}))}")
            print(f"  • Features: {len(data.get('features', []))}")
            print(f"  • Images: {len(images)}")
            print(f"  • Description: {len(description)} characters")
            print(f"  • Content sections: {len(data.get('content_sections', {}))}")
            print("\nAll data extracted successfully! ✓\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            print("\nFull error traceback:")
            print("-" * 80)
            traceback.print_exc()
            print("-" * 80)
        finally:
            await browser.close()
            print("\n🔒 Browser closed.")


async def main():
    """Main demo function."""
    
    # Example URLs
    demo_urls = [
        ("1", "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally", "Multistrada V4 Rally"),
        ("2", "https://www.ducati.com/ww/en/bikes/hypermotard/hypermotard-v2", "Hypermotard V2"),
        ("3", "https://www.ducati.com/ww/en/bikes/scrambler", "Scrambler Category"),
        ("4", "https://www.ducati.com/ww/en/stories/travel/road-to-olympus-multistrada-v4-rally", "Travel Story"),
        ("5", "https://www.ducati.com/ww/en/bikes/offroad/desmo250-mx", "Desmo250 MX"),
    ]
    
    # Check for command line argument
    import sys
    if len(sys.argv) > 1:
        # URL provided as argument
        target_url = sys.argv[1]
        print(f"\n🎯 Using URL from command line: {target_url}\n")
    else:
        # Interactive mode (or default)
        print("\n🚀 DUCATI SCRAPER DEMO\n")
        print("Available demo pages:")
        for num, url, name in demo_urls:
            print(f"  {num}. {name}")
            print(f"     {url}")
        
        print("\nOr enter a custom URL to scrape.")
        try:
            choice = input("\nEnter number (1-5) or custom URL (or press Enter for option 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            # Non-interactive mode, use default
            choice = ""
            print("\n(Non-interactive mode, using default URL 1)\n")
        
        if choice.isdigit() and 1 <= int(choice) <= len(demo_urls):
            target_url = demo_urls[int(choice) - 1][1]
        elif choice:
            target_url = choice
        else:
            target_url = demo_urls[0][1]
    
    await demo_scrape_page(target_url)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user.")
