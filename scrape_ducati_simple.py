"""
Simplified Ducati scraper - based on working full_site_crawler.py
Run this to scrape all Ducati models.
"""
import asyncio
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the working crawler
from scripts.full_site_crawler import SiteCrawler

async def main():
    print("=" * 60)
    print("Ducati Model Scraper")
    print("=" * 60)
    print()
    print("This will scrape all Ducati bike pages.")
    print("The crawler will discover pages automatically.")
    print()
    
    base_url = "https://www.ducati.com"
    output_dir = "output"
    
    print(f"Base URL: {base_url}")
    print(f"Output directory: {output_dir}")
    print()
    print("Starting crawler...")
    print("(A browser window will open)")
    print()
    
    crawler = SiteCrawler(
        base_url=base_url,
        output_dir=output_dir,
        rate_limit=3.0
    )
    
    try:
        await crawler.crawl()
        print()
        print("=" * 60)
        print("Scraping complete!")
        print("=" * 60)
        print(f"Check {output_dir} for results")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())


