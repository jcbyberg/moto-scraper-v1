#!/usr/bin/env python3
"""
Comprehensive extraction from Multistrada V4 Rally page.
Extracts all data including images, video posters, specifications, features, etc.
"""

import sys
import json
import re
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Set
from urllib.parse import urljoin, urlparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.processors.normalizer import DataNormalizer
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.schema import BikeDataWithMetadata, ExtractionMetadata, ImageInfo
from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_urls_from_snapshot(snapshot_path: Path, base_url: str) -> Dict[str, List[str]]:
    """
    Extract all URLs (images, video posters, etc.) from snapshot file.
    
    Args:
        snapshot_path: Path to snapshot file
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Dictionary with 'images', 'video_posters', 'links' lists
    """
    content = snapshot_path.read_text(encoding='utf-8', errors='ignore')
    
    images = []
    video_posters = []
    links = []
    
    # Extract image URLs from various sources
    # Look for URLs in the content
    url_patterns = [
        r'https://[^\s<>"\']+\.(jpg|jpeg|png|gif|webp|svg)',
        r'https://images\.ctfassets\.net/[^\s<>"\']+',
        r'poster="([^"]+)"',
        r'src="([^"]+\.(jpg|jpeg|png|gif|webp|svg))"',
        r'url\(["\']?([^"\']+\.(jpg|jpeg|png|gif|webp|svg))["\']?\)',
    ]
    
    # Extract all URLs
    all_urls = set()
    for pattern in url_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                url = match[0] if match[0].startswith('http') else match[1] if len(match) > 1 and match[1].startswith('http') else None
            else:
                url = match
            if url and url.startswith('http'):
                all_urls.add(url)
    
    # Separate video posters
    poster_pattern = r'poster="([^"]+)"'
    poster_matches = re.findall(poster_pattern, content, re.IGNORECASE)
    for poster_url in poster_matches:
        if poster_url.startswith('http'):
            video_posters.append(poster_url)
            all_urls.add(poster_url)
    
    # All other image URLs
    for url in all_urls:
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
            if url not in video_posters:
                images.append(url)
    
    # Extract links
    link_pattern = r'https://[^\s<>"\']+'
    link_matches = re.findall(link_pattern, content)
    for link in link_matches:
        if 'ducati.com' in link and link not in images and link not in video_posters:
            links.append(link)
    
    return {
        'images': sorted(list(set(images))),
        'video_posters': sorted(list(set(video_posters))),
        'links': sorted(list(set(links)))[:50]  # Limit links
    }


def extract_text_content(snapshot_path: Path) -> Dict[str, Any]:
    """
    Extract text content from snapshot.
    
    Args:
        snapshot_path: Path to snapshot file
        
    Returns:
        Dictionary with text content organized by type
    """
    content = snapshot_path.read_text(encoding='utf-8', errors='ignore')
    
    # Extract URL and title
    url = None
    title = None
    
    for line in content.split('\n')[:100]:
        if 'Page URL:' in line:
            url = line.split('Page URL:')[1].strip()
        if 'Page Title:' in line:
            title = line.split('Page Title:')[1].strip()
            break
    
    # Extract all name fields (text content)
    name_pattern = r'name:\s*(.+?)(?:\n|$)'
    all_text = []
    
    matches = re.findall(name_pattern, content)
    for match in matches:
        text = match.strip()
        # Filter out very short strings and navigation elements
        if (len(text) > 5 and 
            not any(skip in text.lower() for skip in [
                'cookie', 'menu', 'navigation', 'button', 'close', 
                'login', 'sign up', 'myducati', 'the land of joy'
            ])):
            all_text.append(text)
    
    # Extract specifications
    specs = {}
    full_text = ' '.join(all_text)
    
    # Power
    power_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hp|HP|kW|kw)', full_text)
    if power_match:
        specs['power'] = power_match.group(1) + ' hp'
    
    # Torque
    torque_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lb-ft|Nm|kgm|N·m|lb ft)', full_text)
    if torque_match:
        specs['torque'] = torque_match.group(1) + ' ' + (torque_match.group(0).split()[-1] if ' ' in torque_match.group(0) else 'Nm')
    
    # Weight
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*kg\s*(?:\([^)]+\))?', full_text)
    if weight_match:
        specs['weight'] = weight_match.group(1) + ' kg'
    
    # Displacement
    displacement_match = re.search(r'(\d+(?:,\d+)?)\s*cc', full_text)
    if displacement_match:
        specs['displacement'] = displacement_match.group(1).replace(',', '') + ' cc'
    
    # Extract features (look for feature-like text)
    features = []
    feature_keywords = ['system', 'technology', 'equipment', 'feature', 'includes', 
                       'equipped', 'standard', 'optional', 'control', 'assist']
    
    sentences = re.split(r'[.!?]\s+', full_text)
    for sentence in sentences:
        sentence = sentence.strip()
        if (any(keyword in sentence.lower() for keyword in feature_keywords) and
            len(sentence) > 15 and len(sentence) < 300):
            features.append(sentence)
    
    # Description (first substantial text block)
    description = ' '.join(all_text[:1000])[:2000]  # First 2000 chars
    
    return {
        'url': url,
        'title': title,
        'specifications': specs,
        'features': features[:30],  # Limit to 30 features
        'description': description,
        'all_text': all_text
    }


async def extract_and_save(
    snapshot_file: str,
    manufacturer: str = "Ducati",
    output_dir: str = "output",
    images_dir: str = "images"
):
    """
    Extract all data from snapshot and save to files.
    
    Args:
        snapshot_file: Path to snapshot file
        manufacturer: Manufacturer name
        output_dir: Output directory
        images_dir: Images directory
    """
    snapshot_path = Path(snapshot_file)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")
    
    print("=" * 80)
    print("EXTRACTING DATA FROM MULTISTRADA V4 RALLY PAGE")
    print("=" * 80)
    
    # Extract URLs
    print("\n📸 Extracting images and video posters...")
    text_data = extract_text_content(snapshot_path)
    base_url = text_data.get('url', 'https://www.ducati.com')
    
    urls_data = extract_urls_from_snapshot(snapshot_path, base_url)
    
    print(f"   ✓ Images found: {len(urls_data['images'])}")
    print(f"   ✓ Video posters found: {len(urls_data['video_posters'])}")
    print(f"   ✓ Links found: {len(urls_data['links'])}")
    
    # Combine all images (including video posters)
    all_images = urls_data['images'] + urls_data['video_posters']
    
    # Extract text content
    print("\n📝 Extracting text content...")
    print(f"   ✓ Title: {text_data.get('title', 'Unknown')}")
    print(f"   ✓ Specifications: {len(text_data.get('specifications', {}))}")
    print(f"   ✓ Features: {len(text_data.get('features', []))}")
    print(f"   ✓ Description length: {len(text_data.get('description', ''))} chars")
    
    # Extract model and year
    url = text_data.get('url', '')
    title = text_data.get('title', '')
    
    model = "Multistrada V4 Rally"
    year = 2024
    
    # Try to extract year from title
    year_match = re.search(r'(\d{4})', title)
    if year_match:
        year = int(year_match.group(1))
    
    # Prepare raw data
    raw_data = {
        'specifications': text_data.get('specifications', {}),
        'features': text_data.get('features', []),
        'description': text_data.get('description', ''),
        'colors': [],
        'price': None,
        'content_sections': {},
        'images': [{'url': img_url, 'type': 'image'} for img_url in all_images]
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
    
    # Convert image URLs to ImageInfo objects
    image_infos = []
    for idx, img_url in enumerate(all_images[:50]):  # Limit to 50 images
        image_infos.append(ImageInfo(
            url=img_url,
            type='hero' if idx < 2 else 'gallery',
            alt_text=f"{model} image {idx + 1}"
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
    
    # Also save image URLs to a separate JSON file
    images_json = {
        'model': model,
        'year': year,
        'manufacturer': manufacturer,
        'url': url,
        'images': all_images,
        'video_posters': urls_data['video_posters'],
        'extracted_at': str(Path(snapshot_file).stat().st_mtime)
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
    print(f"   🎬 Video posters: {len(urls_data['video_posters'])}")
    
    # Print sample image URLs
    print("\n📸 Sample Image URLs:")
    for i, img_url in enumerate(all_images[:5], 1):
        print(f"   {i}. {img_url}")
    if len(all_images) > 5:
        print(f"   ... and {len(all_images) - 5} more")
    
    return {
        'success': True,
        'manufacturer': manufacturer,
        'model': model,
        'year': year,
        'images_count': len(all_images),
        'video_posters_count': len(urls_data['video_posters']),
        'specifications_count': len(text_data.get('specifications', {})),
        'features_count': len(text_data.get('features', [])),
        'output_file': str(output_path / f"{manufacturer}_{model.replace(' ', '_')}_{year}.md")
    }


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract data from Multistrada page")
    parser.add_argument("--snapshot", 
                       default=r"C:\Users\jcbyb\.cursor\browser-logs\snapshot-2025-11-29T21-15-17-709Z.log",
                       help="Path to snapshot file")
    parser.add_argument("--manufacturer", default="Ducati", help="Manufacturer name")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--images-dir", default="images", help="Images directory")
    
    args = parser.parse_args()
    
    try:
        result = await extract_and_save(
            snapshot_file=args.snapshot,
            manufacturer=args.manufacturer,
            output_dir=args.output_dir,
            images_dir=args.images_dir
        )
        
        print("\n" + "=" * 80)
        print("EXTRACTION SUMMARY")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())


