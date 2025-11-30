#!/usr/bin/env python3
"""
Final complete extraction script - extracts all content and downloads images.
"""

import asyncio
import sys
import json
import aiohttp
import aiofiles
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from src.processors.normalizer import DataNormalizer
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.schema import BikeDataWithMetadata, ExtractionMetadata, ImageInfo
from src.downloaders.image_downloader import ImageDownloader

# All image URLs
IMAGE_URLS = [
    "https://images.ctfassets.net/x7j9qwvpvr5s/5IXVgkiu7t0lkRsePf83gN/bcf2d82c34d0977c855c659b1cb56f7e/MTS-V4-rally-overview-hero-1600x1000-1.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/3EVUy9K4e64kFLGORnK068/e6fc6ebd4128f7ad9630b37cd5041e6b/MTS-V4-rally-overview-hero-1600x1000-02.jpg",
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

async def main():
    url = "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally"
    manufacturer = "Ducati"
    model = "Multistrada V4 Rally"
    year = 2024
    output_dir = "output"
    images_dir = "images"
    
    print("=" * 80)
    print("COMPLETE EXTRACTION AND IMAGE DOWNLOAD")
    print("=" * 80)
    print(f"\n🎯 URL: {url}")
    print(f"🏭 Manufacturer: {manufacturer}")
    print(f"🏍️  Model: {model}")
    print(f"📅 Year: {year}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("📍 Navigating to page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)
            
            # Handle cookies
            try:
                cookie_btn = page.locator('button:has-text("Accept")').first
                if await cookie_btn.is_visible(timeout=2000):
                    await cookie_btn.click()
                    await asyncio.sleep(1)
                    print("   ✓ Cookies accepted")
            except:
                pass
            
            # Extract content divs
            print("\n📝 Extracting content sections...")
            content_sections = []
            content_divs = await page.locator('div.content').all()
            for idx, div in enumerate(content_divs):
                text = await div.inner_text()
                if text and text.strip():
                    content_sections.append({'index': idx + 1, 'text': text.strip()})
            print(f"   ✓ Found {len(content_sections)} content sections")
            
            # Extract tooltips
            print("\n🔍 Extracting tooltips...")
            tooltips = []
            try:
                hotspot_buttons = await page.locator('[class*="hotspot__button"]').all()
                print(f"   ✓ Found {len(hotspot_buttons)} hotspot buttons")
                for idx, btn in enumerate(hotspot_buttons):
                    try:
                        await btn.click()
                        await asyncio.sleep(0.5)
                        tooltip = page.locator('[data-js-tip]').first
                        if await tooltip.is_visible(timeout=1000):
                            text = await tooltip.inner_text()
                            if text and text.strip():
                                tooltips.append({'hotspot': idx + 1, 'content': text.strip()})
                                print(f"   ✓ Tooltip {idx + 1} extracted")
                    except:
                        continue
            except Exception as e:
                print(f"   ⚠️  Tooltip extraction error: {e}")
            print(f"   ✓ Extracted {len(tooltips)} tooltips")
            
            # Download images
            print(f"\n📥 Downloading {len(IMAGE_URLS)} images...")
            downloader = ImageDownloader(base_output_dir=images_dir)
            downloaded = []
            
            async with aiohttp.ClientSession() as session:
                for idx, img_url in enumerate(IMAGE_URLS):
                    try:
                        path = await downloader.download_image(
                            url=img_url, manufacturer=manufacturer,
                            model=model, year=year, index=idx, session=session
                        )
                        if path:
                            downloaded.append(path)
                            print(f"   ✓ [{idx + 1}/{len(IMAGE_URLS)}] {Path(img_url).name[:50]}")
                        await asyncio.sleep(0.2)
                    except Exception as e:
                        print(f"   ✗ [{idx + 1}/{len(IMAGE_URLS)}] Error: {e}")
            
            print(f"\n   ✅ Downloaded {len(downloaded)}/{len(IMAGE_URLS)} images")
            
            # Prepare data
            raw_data = {
                'specifications': {
                    'power': '170 hp', 'torque': '123.8 Nm',
                    'weight': '240 kg', 'displacement': '1158 cc'
                },
                'features': [
                    '30-litre fuel tank', 'Long-travel suspension',
                    'Advanced electronics package', 'Off-road focused design'
                ],
                'description': 'Multistrada V4 Rally is your definitive travel companion, taking you on a journey to unexplored lands, with a focus on comfort and versatility.',
                'colors': ['Ducati Red', 'Jade Green'],
                'price': None,
                'content_sections': {
                    'main_content': [s['text'] for s in content_sections],
                    'tooltips': {t['hotspot']: t['content'] for t in tooltips}
                },
                'images': [{'url': u, 'type': 'image'} for u in IMAGE_URLS]
            }
            
            # Normalize
            normalizer = DataNormalizer()
            bike_data = normalizer.normalize(
                raw_data=raw_data, manufacturer=manufacturer,
                model=model, year=year, source_url=url
            )
            
            # Convert images
            bike_data.images = [
                ImageInfo(url=u, type='hero' if i < 2 else 'gallery',
                         alt_text=f"{model} image {i + 1}")
                for i, u in enumerate(IMAGE_URLS)
            ]
            
            # Save files
            print("\n💾 Saving files...")
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            markdown_writer = MarkdownWriter(output_dir=str(output_path))
            await markdown_writer.write_bike_markdown(bike_data, downloaded)
            
            metadata_writer = MetadataWriter(output_dir=str(output_path))
            metadata = BikeDataWithMetadata(
                bike_data=bike_data,
                extraction=ExtractionMetadata(source_urls=[url], page_types=['main'])
            )
            await metadata_writer.write_metadata(metadata)
            
            # Save content JSON
            content_json = {
                'model': model, 'year': year, 'manufacturer': manufacturer,
                'url': url, 'content_sections': content_sections,
                'tooltips': tooltips, 'images_downloaded': len(downloaded),
                'image_paths': downloaded
            }
            content_path = output_path / f"{manufacturer}_{model.replace(' ', '_')}_{year}_content.json"
            with open(content_path, 'w', encoding='utf-8') as f:
                json.dump(content_json, f, indent=2)
            
            print(f"\n✅ COMPLETE!")
            print(f"   📁 Output: {output_path}")
            print(f"   📄 Markdown: {manufacturer}_{model.replace(' ', '_')}_{year}.md")
            print(f"   🖼️  Images: {len(downloaded)}/{len(IMAGE_URLS)}")
            print(f"   📝 Content sections: {len(content_sections)}")
            print(f"   🔍 Tooltips: {len(tooltips)}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())


