#!/usr/bin/env python3
"""
Complete extraction and download script for Multistrada V4 Rally.
Extracts all content (including interactive tooltips) and downloads all images.
"""

import asyncio
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set
from urllib.parse import urlparse
import aiohttp

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from src.extractors.data_extractor import DataExtractor
from src.extractors.image_extractor import ImageExtractor
from src.processors.normalizer import DataNormalizer
from src.downloaders.image_downloader import ImageDownloader
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.schema import BikeDataWithMetadata, ExtractionMetadata, ImageInfo
from src.utils.logging import get_logger

logger = get_logger(__name__)

# All image URLs from network requests
ALL_IMAGE_URLS = [
    # Video posters
    "https://images.ctfassets.net/x7j9qwvpvr5s/5IXVgkiu7t0lkRsePf83gN/bcf2d82c34d0977c855c659b1cb56f7e/MTS-V4-rally-overview-hero-1600x1000-1.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/3EVUy9K4e64kFLGORnK068/e6fc6ebd4128f7ad9630b37cd5041e6b/MTS-V4-rally-overview-hero-1600x1000-02.jpg",
    # Additional images
    "https://images.ctfassets.net/x7j9qwvpvr5s/4a6hZcNBIGditITuBTTVdx/7385fd8ae2a33f2d056d2f22aca52a24/2025-10-06_Multistrada-V4-Rally-ENG-Curve-768x480.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/6xgJEjCNf5tJaDRYbj8XUP/265228b8f61ffc577cb7c341f31b3bb6/2025-10-06_Multistrada-V4-Rally-Red-MY26-360_0017_it16.png",
    "https://images.ctfassets.net/x7j9qwvpvr5s/6whYPwF6eGEOccH8uIecTh/2a4fe621a2db0f7dbd374522085f6066/MTS-V4-rally-overview-gallery-mosaic-780x430-01.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/Mne2P4iHd3bIfjVXuPCfV/ee87dc3d1c10b83d9aaab28ddfd12b62/MTS-V4-rally-overview-gallery-mosaic-442x600-01.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/5XW7CzPtYMCp7TPhp5MpwN/1bf0d0d3c352dfaa7d027a1ac61b3769/MTS-V4-rally-overview-gallery-mosaic-780x430-02.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/6dfy8yg9Igw4latZQ5rx8J/04774b6e5e3fa7f79361e57f0e7e68cc/MTS-V4-rally-overview-gallery-mosaic-442x600-02.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2jVVCYdLfyVmIKX7w41qU7/7f4e4464f2b24a298aa46ebd0b54b742/MTS-V4-rally-overview-gallery-mosaic-780x430-03.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2fed17KFb2g0yKbsI3NaU1/bd67c213a75ab83e531a14ad77e7a687/MTS-V4-rally-overview-gallery-mosaic-442x600-03.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2HxmivWt0VmXT7ksGAFIUN/82b375254244ee8726ecc1f4aba4b9c9/2025-10-06_Multistrada-V4-Rally-Jade-Green-MY26-360_0017_it16.png",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2HSjkIVvsP1mNiaaKSqinW/0157c16e7399c71c0fb3fadd13db2044/MTS-V4-rally-overview-gallery-mosaic-780x430-04.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/1PbR8SM9YLx7asmXOZRK0P/b524959f937695501d3d548b822d60d1/MTS-V4-rally-overview-gallery-mosaic-442x600-04.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/5hLiNRrHlwUctba6ygjPH9/4ba2d81ab406eee31c8471361417426f/MTS-V4-rally-overview-gallery-mosaic-780x430-05.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/7vi1OXCL0yDL46bv8kytEw/a2aedcd28c05501f206a8142f0487142/MTS-V4-rally-overview-gallery-mosaic-442x600-05.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/7kaviQjfLSwoktJnm6wzJv/7649e97d29dde1e685e3e925bf2cd59c/MTS-V4-rally-overview-gallery-mosaic-780x430-06.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/7nE9J276MuBuuzZseBDxnc/28c222bdb4dba0a6abcfc2238866413c/MTS-V4-rally-overview-gallery-mosaic-442x600-06.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2jyHyA4XE7Yv3hMqPA0ivs/c350e449cd2ff73f3aedd947e21a1697/MTS-V4-rally-overview-gallery-mosaic-780x430-08.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/NZeHOpasyRqpMAYACYz29/c779906d76bb7ac598a93a57e58b93d9/MTS-V4-rally-overview-gallery-mosaic-780x430-07.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/6vW7R3ik6PkB7l8nEjTFA3/1876a12f8d94598039195c1e5f1b8c5d/MTS-V4-rally-overview-gallery-mosaic-442x600-07.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/AoZ5Zy7WaWcUcc2uGhZOK/94649aaa3e0003b01d3151836efe7994/MTS-V4-rally-overview-gallery-mosaic-442x600-08.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/FQU1NnmMsa9pIVKh33yqn/bd2fc4199535874c6660ff546ad854eb/MTS-V4-rally-overview-gallery-mosaic-780x430-09.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/WV6mkSZDXwHGXssjVnmAE/89f7c58d7453aa51b1ca0e033a929649/MTS-V4-rally-overview-gallery-mosaic-442x600-09.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/8e2Bgi465I6NgTYeHXYJB/c840a0a5d6ced91ca03f232733acbf8f/MTS-V4-rally-overview-gallery-mosaic-780x430-10.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/3u0u47DboT51GJcaj4tLfE/879bc8b2d89763f5705259ef1cf59e13/MTS-V4-rally-overview-gallery-mosaic-442x600-10.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/5m4ESqif1KhD6eLi9FM8nV/bd26254dc7023ec06d5bc716464dbc90/MTS-V4-rally-overview-bg-model-preview-2000x800_v02.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/xTomuNqrsDRglg08paSQA/787da8a3319f86b0f3a3759c9e2b98ba/2025-10-06_Multistrada-V4-Rally-Radar-Rd-MY26-Hotspot-1920x1189.png",
    "https://images.ctfassets.net/x7j9qwvpvr5s/1Qx45jpVBTc01Txyl2oQ3D/3b657895a23a4f2a792705f11a1ff445/MTS-V4-rally-looks-preview-802x561-01.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/4BDOMfSUQPflo94EiVTwPe/ad4b8b79105b805f54e7c3e0f3c9a26b/MTS-V4-rally-looks-preview-802x561-02.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/iZbC5MTLOD4Av4u74mCUj/1f345ea0d0e96f900d0cac85fe83ad6f/MTS-V4-rally-looks-preview-802x561-03.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/335oYYeSAkorkIeDbGAwBC/1592dc07e36f12c6f7acc540b8a45d79/MTS-V4-rally-looks-preview-802x561-05.jpg",
]


async def extract_all_content_and_download_images(
    url: str = "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally",
    manufacturer: str = "Ducati",
    model: str = "Multistrada V4 Rally",
    year: int = 2024,
    output_dir: str = "output",
    images_dir: str = "images"
):
    """Extract all content including tooltips and download all images."""
    
    print("=" * 80)
    print("COMPLETE EXTRACTION AND IMAGE DOWNLOAD")
    print("=" * 80)
    print(f"\n🎯 URL: {url}")
    print(f"🏭 Manufacturer: {manufacturer}")
    print(f"🏍️  Model: {model}")
    print(f"📅 Year: {year}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            print("📍 Navigating to page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)
            
            # Handle cookies
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("Accept All")').first
                if await cookie_button.is_visible(timeout=2000):
                    await cookie_button.click()
                    await asyncio.sleep(1)
                    print("   ✓ Cookies accepted")
            except:
                pass
            
            # Extract all content divs
            print("\n📝 Extracting content sections...")
            content_sections = []
            
            # Get all content divs
            content_divs = await page.locator('div.content').all()
            for idx, div in enumerate(content_divs):
                text = await div.inner_text()
                if text and text.strip():
                    content_sections.append({
                        'index': idx + 1,
                        'text': text.strip()
                    })
            
            print(f"   ✓ Content sections found: {len(content_sections)}")
            
            # Click hotspot buttons and extract tooltips
            print("\n🔍 Extracting tooltip content...")
            tooltips = []
            
            try:
                # Find all hotspot buttons
                hotspot_buttons = await page.locator('[class*="hotspot__button"]').all()
                print(f"   ✓ Hotspot buttons found: {len(hotspot_buttons)}")
                
                for idx, button in enumerate(hotspot_buttons):
                    try:
                        # Click the button
                        await button.click()
                        await asyncio.sleep(0.5)  # Wait for tooltip to appear
                        
                        # Find tooltip content
                        tooltip = await page.locator('[data-js-tip]').first
                        if await tooltip.is_visible(timeout=1000):
                            tooltip_text = await tooltip.inner_text()
                            if tooltip_text and tooltip_text.strip():
                                tooltips.append({
                                    'hotspot_number': idx + 1,
                                    'content': tooltip_text.strip()
                                })
                                print(f"   ✓ Tooltip {idx + 1} extracted")
                    except Exception as e:
                        logger.debug(f"Could not extract tooltip {idx + 1}: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Error extracting tooltips: {e}")
            
            print(f"   ✓ Tooltips extracted: {len(tooltips)}")
            
            # Extract data using extractors
            print("\n📊 Extracting specifications and features...")
            data_extractor = DataExtractor()
            data = await data_extractor.extract_from_page(page, 'main')
            
            # Add extracted content sections
            data['content_sections'] = {
                'main_content': [s['text'] for s in content_sections],
                'tooltips': {t['hotspot_number']: t['content'] for t in tooltips}
            }
            
            print(f"   ✓ Specifications: {len(data.get('specifications', {}))}")
            print(f"   ✓ Features: {len(data.get('features', []))}")
            print(f"   ✓ Content sections: {len(content_sections)}")
            print(f"   ✓ Tooltips: {len(tooltips)}")
            
            # Download all images
            print("\n📥 Downloading images...")
            image_downloader = ImageDownloader(base_output_dir=images_dir)
            downloaded_paths = []
            
            async with aiohttp.ClientSession() as session:
                for idx, img_url in enumerate(ALL_IMAGE_URLS):
                    try:
                        print(f"   → Downloading image {idx + 1}/{len(ALL_IMAGE_URLS)}: {Path(img_url).name[:50]}...")
                        path = await image_downloader.download_image(
                            url=img_url,
                            manufacturer=manufacturer,
                            model=model,
                            year=year,
                            index=idx,
                            session=session
                        )
                        if path:
                            downloaded_paths.append(path)
                            print(f"      ✓ Saved: {path}")
                        await asyncio.sleep(0.2)  # Rate limiting
                    except Exception as e:
                        logger.error(f"Error downloading {img_url}: {e}")
                        continue
            
            print(f"\n   ✅ Downloaded {len(downloaded_paths)} images")
            
            # Prepare normalized data
            data['images'] = [{'url': img_url, 'type': 'image'} for img_url in ALL_IMAGE_URLS]
            
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
            for idx, img_url in enumerate(ALL_IMAGE_URLS):
                img_type = 'hero' if idx < 2 else 'gallery'
                image_infos.append(ImageInfo(
                    url=img_url,
                    type=img_type,
                    alt_text=f"{model} {img_type} image {idx + 1}"
                ))
            
            bike_data.images = image_infos
            
            # Create output directories
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Write markdown
            print("\n💾 Saving files...")
            markdown_writer = MarkdownWriter(output_dir=str(output_path))
            await markdown_writer.write_bike_markdown(bike_data, downloaded_paths)
            
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
            
            # Save detailed content JSON
            content_json = {
                'model': model,
                'year': year,
                'manufacturer': manufacturer,
                'url': url,
                'content_sections': content_sections,
                'tooltips': tooltips,
                'images_downloaded': len(downloaded_paths),
                'image_paths': downloaded_paths
            }
            
            content_json_path = output_path / f"{manufacturer}_{model.replace(' ', '_')}_{year}_content.json"
            with open(content_json_path, 'w', encoding='utf-8') as f:
                json.dump(content_json, f, indent=2)
            
            print(f"\n✅ Extraction and download complete!")
            print(f"   📁 Output directory: {output_path}")
            print(f"   📄 Markdown: {manufacturer}_{model.replace(' ', '_')}_{year}.md")
            print(f"   📄 Metadata: {manufacturer}_{model.replace(' ', '_')}_{year}_meta.json")
            print(f"   📄 Content JSON: {content_json_path.name}")
            print(f"   🖼️  Images downloaded: {len(downloaded_paths)}/{len(ALL_IMAGE_URLS)}")
            print(f"   📝 Content sections: {len(content_sections)}")
            print(f"   🔍 Tooltips: {len(tooltips)}")
            
            return {
                'success': True,
                'images_downloaded': len(downloaded_paths),
                'content_sections': len(content_sections),
                'tooltips': len(tooltips),
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
    result = await extract_all_content_and_download_images()
    if result:
        print("\n" + "=" * 80)
        print("EXTRACTION SUMMARY")
        print("=" * 80)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

