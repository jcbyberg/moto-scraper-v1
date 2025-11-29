#!/usr/bin/env python3
"""Test proxy connection."""

import asyncio
from playwright.async_api import async_playwright

async def test_proxy():
    """Test if proxy works."""
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
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        # Test with a simple site first
        print("Testing proxy with httpbin.org...")
        try:
            response = await page.goto("https://httpbin.org/ip", timeout=30000)
            content = await page.content()
            print(f"Status: {response.status if response else 'None'}")
            print(f"Content: {content[:500]}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Now test Ducati
        print("\nTesting proxy with Ducati...")
        try:
            response = await page.goto("https://www.ducati.com", timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            title = await page.title()
            url = page.url
            print(f"Status: {response.status if response else 'None'}")
            print(f"Title: {title}")
            print(f"URL: {url}")
            
            if "Access Denied" not in title:
                print("✅ Success! Proxy is working!")
            else:
                print("❌ Still getting Access Denied")
        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_proxy())


