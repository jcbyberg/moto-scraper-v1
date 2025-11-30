"""Simple runner for the Ducati scraper with immediate feedback."""
import asyncio
import sys
from pathlib import Path

# Write to file for immediate feedback
log_file = Path("scraper_run.log")
with open(log_file, 'w') as f:
    f.write("Starting scraper...\n")
    f.flush()

def log(msg):
    """Log to both file and console."""
    print(msg)
    with open(log_file, 'a') as f:
        f.write(msg + "\n")
        f.flush()

async def main():
    log("=" * 60)
    log("Ducati Model Scraper")
    log("=" * 60)
    
    try:
        from scrape_ducati_models import DucatiModelScraper, DUCATI_MODELS
        log("✓ Imports successful")
        
        log(f"Total models to scrape: {sum(len(models) for models in DUCATI_MODELS.values())}")
        log("")
        log("Creating scraper...")
        
        scraper = DucatiModelScraper(
            output_dir="output",
            images_dir="images", 
            rate_limit=3.0,
            headless=False  # Show browser
        )
        log("✓ Scraper created")
        log("")
        log("Starting discovery phase...")
        log("(This will open a browser window)")
        log("")
        
        # Run discovery
        await scraper.discover_model_urls()
        
        log("")
        log("Discovery complete!")
        log("Check output/discovery_results.json for results")
        
        # Close browser
        await scraper.discovery_engine.close_browser()
        log("✓ Complete!")
        
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        error_msg = traceback.format_exc()
        log(error_msg)
        raise

if __name__ == "__main__":
    log("Script entry point reached")
    asyncio.run(main())
    log("Script finished")


