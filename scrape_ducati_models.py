"""
Scrape all specified Ducati models from the Ducati website.

This script uses the existing crawler infrastructure to discover and scrape
all pages for the specific Ducati models listed by the user.
"""

import asyncio
import re
import json
from pathlib import Path
from typing import Set, List, Dict, Any, Optional
from urllib.parse import urlparse

from src.crawler.discovery import PageDiscoveryEngine
from src.extractors.data_extractor import DataExtractor
from src.extractors.image_extractor import ImageExtractor
from src.processors.normalizer import DataNormalizer
from src.downloaders.image_downloader import ImageDownloader
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.logging import get_logger
import aiohttp

logger = get_logger(__name__)


# Ducati models organized by family
DUCATI_MODELS = {
    "DESERTX": [
        "DesertX MY26",
        "DesertX",
        "DesertX Rally",
        "DesertX Discovery",
    ],
    "DIAVEL": [
        "V4",
        "V4 RS",
        "Diavel for Bentley",
    ],
    "XDIAVEL": [
        "XDiavel V4",
    ],
    "MONSTER": [
        "Monster",
        "Monster SP",
    ],
    "HYPERMOTARD": [
        "698 Mono",
        "698 Mono RVE",
        "V2",
        "V2 SP",
    ],
    "PANIGALE": [
        "V2",
        "V2 MM93",
        "V2 FB63",
        "V4",
        "V4 R",
        "V4 Tricolore",
        "V4 Lamborghini",
    ],
    "MULTISTRADA": [
        "V2",
        "V4",
        "V4 Rally",
        "V4 Pikes Peak",
        "V4 RS",
    ],
    "STREETFIGHTER": [
        "V2",
        "V4",
        "V4 SP2",
        "V4 Supreme®",
    ],
    "SCRAMBLER": [
        "10° Anniversario Rizoma Edition",
        "Icon Dark",
        "Icon",
        "Full Throttle",
    ],
    "OFF-ROAD": [
        "Desmo250 MX",
        "Desmo450 MX",
        "Desmo450 EDS",
    ],
    "E-BIKE": [
        "MIG-S",
        "TK-01RR",
        "FUTA",
        "Powerstage RR",
    ],
    "DUCATI SPECIALE": [
        "Overview",
        "Limited Series",
        "Racing Replica",
        "Racing Real",
    ],
}


def normalize_model_name(model_name: str) -> str:
    """Normalize model name for URL matching."""
    # Remove special characters and normalize
    normalized = model_name.lower()
    normalized = re.sub(r'[°®]', '', normalized)  # Remove degree symbol and registered symbol
    normalized = re.sub(r'\s+', '-', normalized)  # Replace spaces with hyphens
    normalized = re.sub(r'[^\w-]', '', normalized)  # Remove special chars
    return normalized


def matches_model(url: str, family: str, model: str) -> bool:
    """
    Check if URL matches a specific model.
    
    Args:
        url: URL to check
        family: Model family (e.g., "DESERTX", "PANIGALE")
        model: Model name (e.g., "V4", "DesertX Rally")
    
    Returns:
        True if URL likely matches the model
    """
    url_lower = url.lower()
    family_lower = family.lower()
    
    # Check if family name is in URL
    if family_lower not in url_lower:
        return False
    
    # Normalize model name for matching
    model_normalized = normalize_model_name(model)
    model_lower = model.lower()
    
    # Check various patterns
    patterns = [
        model_normalized,
        model_lower.replace(' ', '-'),
        model_lower.replace(' ', ''),
        model_lower,
    ]
    
    # Special cases
    if model == "V2" or model == "V4":
        # V2/V4 variants - check for family + variant pattern
        if f"{family_lower}-{model_lower}" in url_lower or f"{family_lower}{model_lower}" in url_lower:
            return True
        # Also check for standalone V2/V4 in panigale, multistrada, etc.
        if model_lower in url_lower and family_lower in url_lower:
            # Make sure it's not a different family's V2/V4
            # e.g., panigale-v4 should match, but not if it's multistrada-v4 when looking for panigale-v2
            return True
    
    # Check if any pattern matches
    for pattern in patterns:
        if pattern in url_lower:
            return True
    
    # Special handling for specific models
    if model == "DesertX MY26":
        return "desertx" in url_lower and ("my26" in url_lower or "my-26" in url_lower)
    
    if model == "Diavel for Bentley":
        return "diavel" in url_lower and "bentley" in url_lower
    
    if model == "V2 MM93":
        return "v2" in url_lower and "mm93" in url_lower
    
    if model == "V2 FB63":
        return "v2" in url_lower and "fb63" in url_lower
    
    if model == "V4 Tricolore":
        return "v4" in url_lower and "tricolore" in url_lower
    
    if model == "V4 Lamborghini":
        return "v4" in url_lower and "lamborghini" in url_lower
    
    if model == "V4 SP2":
        return "v4" in url_lower and "sp2" in url_lower
    
    if model == "V4 Supreme®":
        return "v4" in url_lower and "supreme" in url_lower
    
    if model == "10° Anniversario Rizoma Edition":
        return "anniversario" in url_lower or "rizoma" in url_lower
    
    if model == "698 Mono":
        return "698" in url_lower and "mono" in url_lower
    
    if model == "698 Mono RVE":
        return "698" in url_lower and "mono" in url_lower and "rve" in url_lower
    
    if "Desmo" in model:
        return model_lower.replace(" ", "-") in url_lower or model_lower.replace(" ", "") in url_lower
    
    if model in ["MIG-S", "TK-01RR", "FUTA", "Powerstage RR"]:
        return model_lower.replace("-", "") in url_lower or model_lower in url_lower
    
    if model in ["Overview", "Limited Series", "Racing Replica", "Racing Real"]:
        # These are special pages under DUCATI SPECIALE
        return "speciale" in url_lower or "limited" in url_lower or "racing" in url_lower
    
    return False


class DucatiModelScraper:
    """Scraper for specific Ducati models."""
    
    def __init__(
        self,
        base_url: str = "https://www.ducati.com",
        output_dir: str = "output",
        images_dir: str = "images",
        rate_limit: float = 3.0,
        headless: bool = False
    ):
        """
        Initialize scraper.
        
        Args:
            base_url: Base URL of Ducati website
            output_dir: Directory for output files
            images_dir: Directory for images
            rate_limit: Seconds between requests
            headless: Run browser in headless mode
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.images_dir = Path(images_dir)
        self.rate_limit = rate_limit
        self.headless = headless
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.discovery_engine = PageDiscoveryEngine(
            base_url=base_url,
            rate_limit_seconds=rate_limit,
            state_file=str(self.output_dir / "ducati_scrape_state.json")
        )
        
        self.data_extractor = DataExtractor()
        self.image_extractor = ImageExtractor()
        self.normalizer = DataNormalizer()
        self.image_downloader = ImageDownloader(
            base_output_dir=str(self.images_dir),
            max_size_mb=10.0
        )
        self.markdown_writer = MarkdownWriter(output_dir=str(self.output_dir))
        self.metadata_writer = MetadataWriter(output_dir=str(self.output_dir))
        
        # Track discovered URLs per model
        self.model_urls: Dict[str, Set[str]] = {}
        for family, models in DUCATI_MODELS.items():
            for model in models:
                key = f"{family}_{model}"
                self.model_urls[key] = set()
        
        # Track visited URLs
        self.visited_urls: Set[str] = set()
    
    async def discover_model_urls(self) -> Dict[str, Set[str]]:
        """
        Discover URLs for all specified models.
        
        Returns:
            Dict mapping model keys to sets of URLs
        """
        print("Starting discovery of Ducati model pages...", flush=True)
        logger.info("Starting discovery of Ducati model pages...")
        
        print("Initializing browser...", flush=True)
        # Initialize browser
        await self.discovery_engine.initialize_browser(headless=self.headless)
        print("Browser initialized. Starting discovery...", flush=True)
        
        try:
            # Discover all pages
            all_discovered = set()
            count = 0
            async for url in self.discovery_engine.discover_all_pages():
                all_discovered.add(url)
                count += 1
                if count % 10 == 0:
                    print(f"Discovered {count} URLs so far...", flush=True)
                logger.debug(f"Discovered: {url}")
            
            print(f"Total discovered URLs: {len(all_discovered)}", flush=True)
            logger.info(f"Total discovered URLs: {len(all_discovered)}")
            
            # Match URLs to models
            print("Matching URLs to models...", flush=True)
            for family, models in DUCATI_MODELS.items():
                for model in models:
                    key = f"{family}_{model}"
                    matching_urls = set()
                    
                    for url in all_discovered:
                        if matches_model(url, family, model):
                            matching_urls.add(url)
                            logger.info(f"Matched {key}: {url}")
                    
                    self.model_urls[key] = matching_urls
                    if matching_urls:
                        print(f"  {key}: {len(matching_urls)} URLs", flush=True)
                    logger.info(f"Found {len(matching_urls)} URLs for {key}")
            
            # Save discovery results
            discovery_file = self.output_dir / "discovery_results.json"
            with open(discovery_file, 'w') as f:
                json.dump(
                    {k: list(v) for k, v in self.model_urls.items()},
                    f,
                    indent=2
                )
            logger.info(f"Saved discovery results to {discovery_file}")
            
        finally:
            # Don't close browser yet - we'll use it for scraping
            pass
        
        return self.model_urls
    
    async def scrape_model(self, family: str, model: str, urls: Set[str]) -> None:
        """
        Scrape all pages for a specific model.
        
        Args:
            family: Model family
            model: Model name
            urls: Set of URLs to scrape for this model
        """
        if not urls:
            logger.warning(f"No URLs found for {family} {model}")
            return
        
        logger.info(f"Scraping {family} {model} ({len(urls)} URLs)...")
        
        # Extract year from model name if present, otherwise use current year
        year = 2024  # Default year
        year_match = re.search(r'MY(\d{2})', model)
        if year_match:
            year = 2000 + int(year_match.group(1))
        
        # Process each URL
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls, 1):
                if url in self.visited_urls:
                    logger.info(f"Skipping already visited: {url}")
                    continue
                
                logger.info(f"[{i}/{len(urls)}] Scraping: {url}")
                
                try:
                    # Navigate to page
                    await self.discovery_engine.page.goto(
                        url,
                        wait_until='networkidle',
                        timeout=30000
                    )
                    await asyncio.sleep(2)  # Wait for dynamic content
                    
                    # Determine page type
                    page_type = 'main'
                    if '/specs' in url.lower():
                        page_type = 'specs'
                    elif '/gallery' in url.lower():
                        page_type = 'gallery'
                    elif '/features' in url.lower():
                        page_type = 'features'
                    elif '/insights' in url.lower():
                        page_type = 'insights'
                    elif '/stories' in url.lower() or '/travel' in url.lower():
                        page_type = 'stories'
                    
                    # Extract data
                    data = await self.data_extractor.extract_from_page(
                        self.discovery_engine.page,
                        page_type
                    )
                    
                    # Extract images
                    images = await self.image_extractor.extract_images(
                        self.discovery_engine.page,
                        model,
                        year
                    )
                    data['images'] = images
                    
                    # Download images
                    image_paths = []
                    for idx, img_info in enumerate(images[:20]):  # Limit to 20 images per page
                        try:
                            path = await self.image_downloader.download_image(
                                url=img_info['url'],
                                manufacturer="Ducati",
                                model=model,
                                year=year,
                                index=idx,
                                session=session
                            )
                            if path:
                                image_paths.append(path)
                            await asyncio.sleep(0.5)  # Rate limit image downloads
                        except Exception as e:
                            logger.error(f"Error downloading image: {e}")
                            continue
                    
                    # Update image data with local paths
                    for idx, img_info in enumerate(images[:20]):
                        if idx < len(image_paths):
                            img_info['local_path'] = image_paths[idx]
                    
                    # Normalize data using the normalizer (returns BikeData)
                    bike_data = self.normalizer.normalize(
                        raw_data=data,
                        manufacturer="Ducati",
                        model=model,
                        year=year,
                        source_url=url
                    )
                    
                    # Write markdown file
                    await self.markdown_writer.write_bike_markdown(
                        bike_data,
                        image_paths
                    )
                    
                    # Mark as visited
                    self.visited_urls.add(url)
                    
                    # Rate limiting
                    await asyncio.sleep(self.rate_limit)
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}", exc_info=True)
                    continue
        
        logger.info(f"Completed scraping {family} {model}")
    
    async def scrape_all_models(self) -> None:
        """Scrape all specified Ducati models."""
        logger.info("Starting scrape of all Ducati models...")
        
        # First, discover URLs
        await self.discover_model_urls()
        
        # Then scrape each model
        total_models = sum(len(models) for models in DUCATI_MODELS.values())
        current = 0
        
        for family, models in DUCATI_MODELS.items():
            for model in models:
                current += 1
                key = f"{family}_{model}"
                urls = self.model_urls.get(key, set())
                
                logger.info(f"[{current}/{total_models}] Processing {family} {model}")
                await self.scrape_model(family, model, urls)
        
        logger.info("Completed scraping all Ducati models!")
        
        # Close browser
        await self.discovery_engine.close_browser()
        
        # Print summary
        total_urls = sum(len(urls) for urls in self.model_urls.values())
        logger.info(f"Summary:")
        logger.info(f"  Total models: {total_models}")
        logger.info(f"  Total URLs discovered: {total_urls}")
        logger.info(f"  Total URLs scraped: {len(self.visited_urls)}")


async def main():
    """Main entry point."""
    import argparse
    
    print("=" * 60)
    print("Ducati Model Scraper - Starting...")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(description="Scrape specified Ducati models")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for markdown files"
    )
    parser.add_argument(
        "--images-dir",
        default="images",
        help="Directory for images"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=3.0,
        help="Seconds to wait between requests"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    args = parser.parse_args()
    
    print(f"Configuration:")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Images directory: {args.images_dir}")
    print(f"  Rate limit: {args.rate_limit} seconds")
    print(f"  Headless mode: {args.headless}")
    print()
    
    scraper = DucatiModelScraper(
        output_dir=args.output_dir,
        images_dir=args.images_dir,
        rate_limit=args.rate_limit,
        headless=args.headless
    )
    
    print(f"Initialized scraper for {len(DUCATI_MODELS)} families")
    print(f"Total models to scrape: {sum(len(models) for models in DUCATI_MODELS.values())}")
    print()
    
    try:
        await scraper.scrape_all_models()
        print("=" * 60)
        print("Scraping completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("Script starting...")
    asyncio.run(main())

