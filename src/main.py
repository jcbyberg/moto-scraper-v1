"""
Main entry point for motorcycle OEM web-crawler.

Orchestrates the complete crawl workflow following the Spec Kit architecture.
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import aiohttp
from src.utils.logging import setup_logging, get_logger
from src.crawler.discovery import PageDiscoveryEngine
from src.crawler.classifier import BikePageClassifier
from src.extractors.data_extractor import DataExtractor
from src.extractors.image_extractor import ImageExtractor
from src.processors.normalizer import DataNormalizer
from src.processors.merger import DataMerger
from src.downloaders.image_downloader import ImageDownloader
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.schema import BikeDataWithMetadata, ExtractionMetadata

logger = get_logger(__name__)


class MotorcycleCrawler:
    """Main crawler orchestrator."""

    def __init__(
        self,
        base_url: str,
        manufacturer: str,
        output_dir: str = "output",
        images_dir: str = "images",
        rate_limit: float = 2.0,
        headless: bool = True,
        proxy: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url
        self.manufacturer = manufacturer
        self.output_dir = Path(output_dir)
        self.images_dir = Path(images_dir)
        self.rate_limit = rate_limit
        self.headless = headless

        # Initialize components
        self.discovery_engine = PageDiscoveryEngine(
            base_url=base_url,
            rate_limit_seconds=rate_limit,
            proxy=proxy
        )
        self.classifier = BikePageClassifier(manufacturer=manufacturer)
        self.data_extractor = DataExtractor()
        self.image_extractor = ImageExtractor()
        self.normalizer = DataNormalizer()
        self.merger = DataMerger()
        self.image_downloader = ImageDownloader(base_output_dir=str(images_dir))
        self.markdown_writer = MarkdownWriter(output_dir=str(output_dir))
        self.metadata_writer = MetadataWriter(output_dir=str(output_dir))

    async def crawl(self):
        """Execute complete crawl workflow."""
        logger.info(f"Starting crawl of {self.base_url}")

        # Initialize browser
        await self.discovery_engine.initialize_browser(headless=self.headless)

        try:
            # Step 1: Discover all pages
            logger.info("=== Phase 1: Page Discovery ===")
            discovered_urls = []
            async for url in self.discovery_engine.discover_all_pages():
                discovered_urls.append(url)

            logger.info(f"Discovered {len(discovered_urls)} URLs")

            # Step 2: Classify bike pages
            logger.info("=== Phase 2: Page Classification ===")
            bike_pages = []
            for url in discovered_urls[:50]:  # Limit for testing
                if self.classifier.is_bike_page(url, ""):
                    page_type = self.classifier.get_page_type(url, "")
                    model_info = self.classifier.extract_model_info(url, "")
                    if model_info:
                        bike_pages.append({
                            'url': url,
                            'page_type': page_type,
                            'model_info': model_info
                        })

            logger.info(f"Classified {len(bike_pages)} bike pages")

            # Step 3: Group related pages
            grouped = self.classifier.group_related_pages(bike_pages)
            logger.info(f"Grouped into {len(grouped)} bike models")

            # Step 4: Extract and process each bike
            logger.info("=== Phase 3: Data Extraction & Processing ===")
            bikes_processed = 0

            for bike_key, pages in list(grouped.items())[:10]:  # Limit for testing
                try:
                    await self._process_bike(bike_key, pages)
                    bikes_processed += 1
                except Exception as e:
                    logger.error(f"Error processing {bike_key}: {e}")
                    continue

            logger.info(f"✅ Crawl complete! Processed {bikes_processed} bikes")

        except Exception as e:
            logger.error(f"Error during crawl: {e}", exc_info=True)
        finally:
            # Ensure proper cleanup
            try:
                # Wait for any pending tasks
                await asyncio.sleep(0.2)
                # Close browser and playwright
                await self.discovery_engine.close_browser()
                # Give additional time for subprocess cleanup
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.discovery_engine.save_state()

    async def _process_bike(self, bike_key, pages: List[Dict[str, Any]]):
        """Process a single bike (extract, normalize, merge, download images, write output)."""
        manufacturer, model, year, variant = bike_key
        logger.info(f"Processing: {manufacturer} {model} {year}")

        pages_data = []

        # Extract from each page
        for page_info in pages:
            url = page_info['url']
            page_type = page_info['page_type']

            try:
                # Navigate to page
                await self.discovery_engine.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(1)

                # Extract data
                extracted_data = await self.data_extractor.extract_from_page(
                    self.discovery_engine.page,
                    page_type
                )

                # Extract images
                images = await self.image_extractor.extract_images(
                    self.discovery_engine.page,
                    model,
                    year
                )
                extracted_data['images'] = images

                # Normalize
                bike_data = self.normalizer.normalize(
                    raw_data=extracted_data,
                    manufacturer=manufacturer,
                    model=model,
                    year=year,
                    source_url=url
                )

                pages_data.append({
                    'bike_data': bike_data,
                    'page_type': page_type
                })

                await asyncio.sleep(self.rate_limit)

            except Exception as e:
                logger.error(f"Error extracting from {url}: {e}")
                continue

        if not pages_data:
            logger.warning(f"No data extracted for {manufacturer} {model} {year}")
            return

        # Merge data from multiple pages
        merged_bike_data = self.merger.merge_bike_data(pages_data)

        # Download images
        image_paths = []
        try:
            async with aiohttp.ClientSession() as session:
                for idx, img_info in enumerate(merged_bike_data.images[:10]):  # Limit images
                    try:
                        path = await self.image_downloader.download_image(
                            url=img_info.url,
                            manufacturer=manufacturer,
                            model=model,
                            year=year,
                            index=idx,
                            session=session
                        )
                        if path:
                            image_paths.append(path)
                    except Exception as e:
                        logger.error(f"Error downloading image: {e}")
        except Exception as e:
            logger.error(f"Error with image download session: {e}")

        # Write markdown
        await self.markdown_writer.write_bike_markdown(merged_bike_data, image_paths)

        # Write metadata
        metadata = BikeDataWithMetadata(
            bike_data=merged_bike_data,
            extraction=ExtractionMetadata(
                source_urls=merged_bike_data.source_urls,
                page_types=[p['page_type'] for p in pages_data]
            )
        )
        await self.metadata_writer.write_metadata(metadata)


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Motorcycle OEM Web-Crawler")
    parser.add_argument("url", help="Base URL of the OEM website")
    parser.add_argument("--manufacturer", required=True, help="Manufacturer name")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--images-dir", default="images", help="Images directory")
    parser.add_argument("--rate-limit", type=float, default=3.0, help="Rate limit in seconds between requests (default: 3.0, recommended: 3-5 for human-like behavior)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    # Default is headless=False (browser visible), use --headless to run in headless mode
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode (default: False, browser visible)")
    parser.add_argument("--proxy", help="Proxy server (format: http://user:pass@host:port or host:port)")
    parser.add_argument("--proxy-user", help="Proxy username (if not in --proxy URL)")
    parser.add_argument("--proxy-pass", help="Proxy password (if not in --proxy URL)")

    args = parser.parse_args()
    
    # Parse proxy configuration
    proxy = None
    if args.proxy:
        from urllib.parse import urlparse
        # Parse proxy URL or host:port format
        if args.proxy.startswith('http://') or args.proxy.startswith('https://'):
            # Full URL format: http://user:pass@host:port
            parsed = urlparse(args.proxy)
            proxy = {
                'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 80}",
            }
            if parsed.username:
                proxy['username'] = parsed.username
            if parsed.password:
                proxy['password'] = parsed.password
        else:
            # host:port format
            if ':' in args.proxy:
                host, port = args.proxy.rsplit(':', 1)
                proxy = {'server': f'http://{host}:{port}'}
            else:
                proxy = {'server': f'http://{args.proxy}:8080'}
        
        # Add username/password if provided separately (overrides URL credentials)
        if args.proxy_user:
            proxy['username'] = args.proxy_user
        if args.proxy_pass:
            proxy['password'] = args.proxy_pass

    # Setup logging
    setup_logging(level=args.log_level)

    # Create crawler
    crawler = MotorcycleCrawler(
        base_url=args.url,
        manufacturer=args.manufacturer,
        output_dir=args.output_dir,
        images_dir=args.images_dir,
        rate_limit=args.rate_limit,
        headless=args.headless,
        proxy=proxy
    )

    # Run crawl
    try:
        await crawler.crawl()
    finally:
        # Give extra time for all async cleanup to complete
        # This helps prevent the "Event loop is closed" warning
        await asyncio.sleep(0.5)


def run_main():
    """Wrapper to run main with proper event loop handling."""
    import warnings
    import sys
    
    # Suppress the harmless asyncio cleanup warning
    if sys.version_info >= (3, 12):
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop is closed.*")
    
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
