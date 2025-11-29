#!/usr/bin/env python3
"""
Test script to verify playwright-stealth integration works correctly.
"""

import asyncio
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth

async def test_stealth():
    """Test that stealth plugin works."""
    print("🧪 Testing playwright-stealth integration...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Apply stealth
        print("   → Applying stealth plugin...")
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        print("   ✓ Stealth plugin applied")
        
        page = await context.new_page()
        
        # Test navigation
        print("\n   → Testing navigation...")
        try:
            response = await page.goto("https://www.ducati.com/ww/en/home", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            title = await page.title()
            status = response.status if response else None
            
            print(f"   ✓ Status: {status}")
            print(f"   ✓ Title: {title}")
            
            if status == 200 and "Access Denied" not in title:
                print("\n✅ SUCCESS! Stealth plugin is working - page loaded successfully!")
            elif status == 403:
                print("\n⚠️  Still getting 403 - may be IP-based blocking, not stealth detection")
            else:
                print(f"\n⚠️  Unexpected status: {status}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_stealth())


