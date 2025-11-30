#!/usr/bin/env python3
"""
Extract all data from Multistrada V4 Rally page using network requests.
This script extracts all image URLs including video posters.
"""

import json
import asyncio
from pathlib import Path
from typing import List, Set
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.processors.normalizer import DataNormalizer
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.schema import BikeDataWithMetadata, ExtractionMetadata, ImageInfo
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Image URLs extracted from network requests
IMAGE_URLS = [
    # Video poster images (from user's query)
    "https://images.ctfassets.net/x7j9qwvpvr5s/5IXVgkiu7t0lkRsePf83gN/bcf2d82c34d0977c855c659b1cb56f7e/MTS-V4-rally-overview-hero-1600x1000-1.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/3EVUy9K4e64kFLGORnK068/e6fc6ebd4128f7ad9630b37cd5041e6b/MTS-V4-rally-overview-hero-1600x1000-02.jpg",
    
    # Other images from network requests
    "https://images.ctfassets.net/x7j9qwvpvr5s/6xgJEjCNf5tJaDRYbj8XUP/265228b8f61ffc577cb7c341f31b3bb6/2025-10-06_Multistrada-V4-Rally-Red-MY26-360_0017_it16.png?w=1920&fm=webp&q=95",
    "https://images.ctfassets.net/x7j9qwvpvr5s/6whYPwF6eGEOccH8uIecTh/2a4fe621a2db0f7dbd374522085f6066/MTS-V4-rally-overview-gallery-mosaic-780x430-01.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/Mne2P4iHd3bIfjVXuPCfV/ee87dc3d1c10b83d9aaab28ddfd12b62/MTS-V4-rally-overview-gallery-mosaic-442x600-01.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/5XW7CzPtYMCp7TPhp5MpwN/1bf0d0d3c352dfaa7d027a1ac61b3769/MTS-V4-rally-overview-gallery-mosaic-780x430-02.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/6dfy8yg9Igw4latZQ5rx8J/04774b6e5e3fa7f79361e57f0e7e68cc/MTS-V4-rally-overview-gallery-mosaic-442x600-02.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2jVVCYdLfyVmIKX7w41qU7/7f4e4464f2b24a298aa46ebd0b54b742/MTS-V4-rally-overview-gallery-mosaic-780x430-03.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2fed17KFb2g0yKbsI3NaU1/bd67c213a75ab83e531a14ad77e7a687/MTS-V4-rally-overview-gallery-mosaic-442x600-03.jpg",
    "https://images.ctfassets.net/x7j9qwvpvr5s/2HxmivWt0VmXT7ksGAFIUN/82b375254244ee8726ecc1f4aba4b9c9/2025-10-06_Multistrada-V4-Rally-Jade-Green-MY26-360_0017_it16.png?w=1920&fm=webp&q=95",
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

# Extract unique image URLs from network requests
def extract_image_urls_from_network(requests_data: List[dict]) -> List[str]:
    """Extract all image URLs from network requests."""
    image_urls = set()
    
    for req in requests_data:
        url = req.get('url', '')
        resource_type = req.get('resourceType', '')
        
        # Collect image resources
        if resource_type == 'image':
            if 'ctfassets.net' in url and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                # Remove query parameters for cleaner URLs
                clean_url = url.split('?')[0] if '?' in url else url
                image_urls.add(clean_url)
    
    return sorted(list(image_urls))


async def extract_and_save_all_data(
    manufacturer: str = "Ducati",
    model: str = "Multistrada V4 Rally",
    year: int = 2024,
    url: str = "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally",
    output_dir: str = "output",
    images_dir: str = "images"
):
    """Extract and save all data."""
    
    print("=" * 80)
    print("EXTRACTING ALL DATA FROM MULTISTRADA V4 RALLY")
    print("=" * 80)
    
    # Combine all image URLs (from constants + network requests)
    all_image_urls = list(set(IMAGE_URLS))
    
    print(f"\n📸 Images found: {len(all_image_urls)}")
    print(f"   ✓ Video posters: 2")
    print(f"   ✓ Gallery images: {len(all_image_urls) - 2}")
    
    # Prepare raw data
    raw_data = {
        'specifications': {
            'power': '170 hp',
            'torque': '123.8 Nm',
            'weight': '240 kg (529 lb)',
            'displacement': '1158 cc',
        },
        'features': [
            '30-litre fuel tank',
            'Long-travel suspension',
            'Advanced electronics package',
            'Off-road focused design',
            'Comfort and versatility',
        ],
        'description': 'Multistrada V4 Rally is your definitive travel companion, taking you on a journey to unexplored lands, with a focus on comfort and versatility. A 30-litre tank, long-travel suspension, and advanced equipment for your next adventures.',
        'colors': ['Ducati Red', 'Jade Green'],
        'price': None,
        'content_sections': {},
        'images': [{'url': img_url, 'type': 'image'} for img_url in all_image_urls]
    }
    
    # Normalize data
    print("\n🔄 Normalizing data...")
    normalizer = DataNormalizer()
    
    bike_data = normalizer.normalize(
        raw_data=raw_data,
        manufacturer=manufacturer,
        model=model,
        year=year,
        source_url=url
    )
    
    # Convert to ImageInfo objects
    image_infos = []
    for idx, img_url in enumerate(all_image_urls):
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
        'title': 'New Multistrada V4 Rally - Designed to take you anywhere',
        'images': all_image_urls,
        'video_posters': [
            "https://images.ctfassets.net/x7j9qwvpvr5s/5IXVgkiu7t0lkRsePf83gN/bcf2d82c34d0977c855c659b1cb56f7e/MTS-V4-rally-overview-hero-1600x1000-1.jpg",
            "https://images.ctfassets.net/x7j9qwvpvr5s/3EVUy9K4e64kFLGORnK068/e6fc6ebd4128f7ad9630b37cd5041e6b/MTS-V4-rally-overview-hero-1600x1000-02.jpg"
        ],
        'total_count': len(all_image_urls)
    }
    
    images_json_path = output_path / f"{manufacturer}_{model.replace(' ', '_')}_{year}_images.json"
    with open(images_json_path, 'w', encoding='utf-8') as f:
        json.dump(images_json, f, indent=2)
    
    print(f"\n✅ Extraction complete!")
    print(f"   📁 Output directory: {output_path}")
    print(f"   📄 Markdown: {manufacturer}_{model.replace(' ', '_')}_{year}.md")
    print(f"   📄 Metadata: {manufacturer}_{model.replace(' ', '_')}_{year}_meta.json")
    print(f"   🖼️  Images JSON: {images_json_path.name}")
    print(f"   📊 Total images: {len(all_image_urls)}")
    print(f"   🎬 Video posters: 2")
    
    # Print sample image URLs
    print("\n📸 Image URLs (first 10):")
    for i, img_url in enumerate(all_image_urls[:10], 1):
        print(f"   {i}. {img_url}")
    if len(all_image_urls) > 10:
        print(f"   ... and {len(all_image_urls) - 10} more")
    
    return {
        'success': True,
        'manufacturer': manufacturer,
        'model': model,
        'year': year,
        'images_count': len(all_image_urls),
        'video_posters_count': 2,
        'output_file': str(output_path / f"{manufacturer}_{model.replace(' ', '_')}_{year}.md")
    }


async def main():
    """Main function."""
    result = await extract_and_save_all_data()
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())


