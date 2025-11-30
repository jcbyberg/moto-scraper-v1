#!/usr/bin/env python3
"""
Extract data from Multistrada V4 Rally page using Playwright.
This gets the actual HTML content including all image URLs.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import re

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from src.extractors.data_extractor import DataExtractor
from src.extractors.image_extractor import ImageExtractor
from src.processors.normalizer import DataNormalizer
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.schema import BikeDataWithMetadata, ExtractionMetadata, ImageInfo
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def extract_page_data(
    url: str = "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally",
    manufacturer: str = "Ducati",
    output_dir: str = "output",
    images_dir: str = "images"
):
    """Extract all data from the page."""
    
    print("=" * 80)
    print("EXTRACTING DATA FROM MULTISTRADA V4 RALLY PAGE")
    print("=" * 80)
    print(f"\n🎯 URL: {url}")
    print(f"🏭 Manufacturer: {manufacturer}\n")
    
    async with async_playwright() as p:
        # Launch browser in headless mode (or visible if you prefer)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            print("📍 Navigating to page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)  # Wait for content to load
            
            # Get page title
            title = await page.title()
            print(f"   ✓ Page loaded: {title}")
            
            # Handle cookies if present
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("Accept All")').first
                if await cookie_button.is_visible(timeout=2000):
                    await cookie_button.click()
                    await asyncio.sleep(1)
                    print("   ✓ Cookies accepted")
            except:
                pass
            
            # Get HTML content to extract image URLs
            print("\n📸 Extracting images and video posters...")
            html_content = await page.content()
            
            # Extract all image URLs
            image_urls = []
            video_posters = []
            
            # Extract from img tags
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
            img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            for img_url in img_matches:
                if img_url.startswith('http') and img_url not in image_urls:
                    image_urls.append(img_url)
            
            # Extract from video poster attributes
            poster_pattern = r'poster=["\']([^"\']+)["\']'
            poster_matches = re.findall(poster_pattern, html_content, re.IGNORECASE)
            for poster_url in poster_matches:
                if poster_url.startswith('http') and poster_url not in video_posters:
                    video_posters.append(poster_url)
            
            # Extract from background-image CSS
            bg_pattern = r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)'
            bg_matches = re.findall(bg_pattern, html_content, re.IGNORECASE)
            for bg_url in bg_matches:
                if bg_url.startswith('http') and bg_url not in image_urls:
                    image_urls.append(bg_url)
            
            # Extract from picture/source tags
            source_pattern = r'<source[^>]+srcset=["\']([^"\']+)["\']'
            source_matches = re.findall(source_pattern, html_content, re.IGNORECASE)
            for srcset in source_matches:
                # srcset can contain multiple URLs
                urls = re.findall(r'https://[^\s,]+', srcset)
                for url in urls:
                    if url not in image_urls:
                        image_urls.append(url)
            
            # Combine all images
            all_images = sorted(list(set(image_urls + video_posters)))
            
            print(f"   ✓ Images found: {len(image_urls)}")
            print(f"   ✓ Video posters found: {len(video_posters)}")
            print(f"   ✓ Total unique images: {len(all_images)}")
            
            # Extract data using extractors
            print("\n📝 Extracting specifications, features, and content...")
            data_extractor = DataExtractor()
            data = await data_extractor.extract_from_page(page, 'main')
            
            print(f"   ✓ Specifications: {len(data.get('specifications', {}))}")
            print(f"   ✓ Features: {len(data.get('features', []))}")
            print(f"   ✓ Description length: {len(data.get('description', ''))} chars")
            
            # Extract model and year
            model = "Multistrada V4 Rally"
            year = 2024
            
            # Try to extract year from title
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = int(year_match.group(1))
            
            # Add images to data
            data['images'] = [{'url': img_url, 'type': 'image'} for img_url in all_images]
            
            # Normalize data
            print("\n🔄 Normalizing data...")
            normalizer = DataNormalizer()
            
            bike_data = normalizer.normalize(
                raw_data=data,
                manufacturer=manufacturer,
                model=model,
                year=year,
                source_url=url
            )
            
            # Convert to ImageInfo objects
            image_infos = []
            for idx, img_url in enumerate(all_images[:50]):  # Limit to 50
                img_type = 'hero' if idx < 2 else 'gallery'
                image_infos.append(ImageInfo(
                    url=img_url,
                    type=img_type,
                    alt_text=f"{model} {img_type} image {idx + 1}"
                ))
            
            bike_data.images = image_infos
            
            # Create output directories
            output_path = Path(output_dir)
            images_path = Path(images_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            images_path.mkdir(parents=True, exist_ok=True)
            
            # Write markdown
            print("\n💾 Saving files...")
            markdown_writer = MarkdownWriter(output_dir=str(output_path))
            await markdown_writer.write_bike_markdown(bike_data, [])
            
            # Write metadata
            metadata_writer = MetadataWriter(output_dir=str(output_path))
            metadata = BikeDataWithMetadata(
                bike_data=bike_data,
                extraction=ExtractionMetadata(
                    source_urls=[url],
                    page_types=['main']
                )
            )
            await metadata_writer.write_metadata(metadata)
            
            # Save image URLs to JSON
            images_json = {
                'model': model,
                'year': year,
                'manufacturer': manufacturer,
                'url': url,
                'title': title,
                'images': image_urls,
                'video_posters': video_posters,
                'all_images': all_images,
                'total_count': len(all_images)
            }
            
            images_json_path = output_path / f"{manufacturer}_{model.replace(' ', '_')}_{year}_images.json"
            with open(images_json_path, 'w', encoding='utf-8') as f:
                json.dump(images_json, f, indent=2)
            
            print(f"\n✅ Extraction complete!")
            print(f"   📁 Output directory: {output_path}")
            print(f"   📄 Markdown: {manufacturer}_{model.replace(' ', '_')}_{year}.md")
            print(f"   📄 Metadata: {manufacturer}_{model.replace(' ', '_')}_{year}_meta.json")
            print(f"   🖼️  Images JSON: {images_json_path.name}")
            print(f"   📊 Total images: {len(all_images)}")
            print(f"   🎬 Video posters: {len(video_posters)}")
            
            # Print sample image URLs
            print("\n📸 Sample Image URLs:")
            for i, img_url in enumerate(all_images[:10], 1):
                print(f"   {i}. {img_url}")
            if len(all_images) > 10:
                print(f"   ... and {len(all_images) - 10} more")
            
            return {
                'success': True,
                'manufacturer': manufacturer,
                'model': model,
                'year': year,
                'images_count': len(all_images),
                'video_posters_count': len(video_posters),
                'specifications_count': len(data.get('specifications', {})),
                'features_count': len(data.get('features', [])),
                'output_file': str(output_path / f"{manufacturer}_{model.replace(' ', '_')}_{year}.md")
            }
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            await browser.close()


async def main():
    """Main function."""
    result = await extract_page_data()
    if result:
        print("\n" + "=" * 80)
        print("EXTRACTION SUMMARY")
        print("=" * 80)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())


