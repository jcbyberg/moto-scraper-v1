"""Quick test to verify the scraper works."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scrape_ducati_models import DucatiModelScraper, DUCATI_MODELS

async def test():
    import sys
    sys.stdout.flush()
    print("=" * 60, flush=True)
    print("Testing Ducati Scraper", flush=True)
    print("=" * 60, flush=True)
    print(f"Total families: {len(DUCATI_MODELS)}")
    print(f"Total models: {sum(len(models) for models in DUCATI_MODELS.values())}")
    print()
    
    print("Creating scraper instance...")
    scraper = DucatiModelScraper(
        output_dir="output",
        images_dir="images",
        rate_limit=3.0,
        headless=False  # Show browser for testing
    )
    print("✓ Scraper created")
    print()
    
    print("Starting discovery (this may take a while)...")
    print("The browser will open - you can watch it work.")
    print()
    
    try:
        # Just test discovery first
        model_urls = await scraper.discover_model_urls()
        
        print()
        print("=" * 60)
        print("Discovery Results:")
        print("=" * 60)
        for key, urls in model_urls.items():
            if urls:
                print(f"{key}: {len(urls)} URLs")
                for url in list(urls)[:3]:  # Show first 3
                    print(f"  - {url}")
                if len(urls) > 3:
                    print(f"  ... and {len(urls) - 3} more")
        
        print()
        print("Closing browser...")
        await scraper.discovery_engine.close_browser()
        print("✓ Test complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        await scraper.discovery_engine.close_browser()

if __name__ == "__main__":
    asyncio.run(test())

