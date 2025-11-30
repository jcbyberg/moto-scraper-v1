#!/usr/bin/env python3
"""
Extract data from Cursor browser snapshots and save to files.
This script parses the snapshot files created by Cursor browser to extract
specifications, features, images, and other data.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.processors.normalizer import DataNormalizer
from src.writers.markdown_writer import MarkdownWriter
from src.writers.metadata_writer import MetadataWriter
from src.utils.schema import BikeDataWithMetadata, ExtractionMetadata
from src.utils.logging import get_logger

logger = get_logger(__name__)


def parse_snapshot_file(snapshot_path: Path) -> Dict[str, Any]:
    """
    Parse a Cursor browser snapshot file to extract page information.
    
    Args:
        snapshot_path: Path to snapshot log file
        
    Returns:
        Dictionary with extracted information
    """
    content = snapshot_path.read_text(encoding='utf-8', errors='ignore')
    
    # Extract URL and title from header
    url = None
    title = None
    
    for line in content.split('\n')[:50]:  # Check first 50 lines
        if 'Page URL:' in line:
            url = line.split('Page URL:')[1].strip()
        if 'Page Title:' in line:
            title = line.split('Page Title:')[1].strip()
            break
    
    # Extract text content from YAML structure
    # Look for name fields which contain text content
    text_content = []
    images = []
    links = []
    
    # Simple regex to extract name fields (text content)
    name_pattern = r'name:\s*(.+?)(?:\n|$)'
    matches = re.findall(name_pattern, content)
    
    for match in matches:
        text = match.strip()
        if text and len(text) > 3:  # Filter out very short strings
            # Skip navigation elements
            if not any(skip in text.lower() for skip in ['cookie', 'menu', 'navigation', 'button']):
                text_content.append(text)
    
    # Extract image references
    img_pattern = r'role:\s*img[^\n]*\n[^\n]*ref:\s*(ref-\w+)'
    img_refs = re.findall(img_pattern, content)
    images = [f"Image ref: {ref}" for ref in img_refs[:20]]  # Limit to first 20
    
    # Extract links
    link_pattern = r'role:\s*link[^\n]*\n[^\n]*name:\s*(.+?)(?:\n|$)'
    link_matches = re.findall(link_pattern, content)
    links = [link.strip() for link in link_matches[:30]]  # Limit to first 30
    
    return {
        'url': url,
        'title': title,
        'text_content': text_content,
        'images': images,
        'links': links,
        'snapshot_file': str(snapshot_path),
        'content_length': len(content)
    }


def extract_specifications_from_text(text_content: List[str]) -> Dict[str, Any]:
    """
    Extract specifications from text content using pattern matching.
    
    Args:
        text_content: List of text strings from page
        
    Returns:
        Dictionary of specifications
    """
    specs = {}
    
    # Common specification patterns
    patterns = {
        'power': r'(\d+(?:\.\d+)?)\s*(?:hp|HP|kW|kw)',
        'torque': r'(\d+(?:\.\d+)?)\s*(?:lb-ft|Nm|kgm|N·m)',
        'weight': r'(\d+(?:\.\d+)?)\s*kg',
        'displacement': r'(\d+(?:,\d+)?)\s*cc',
        'top_speed': r'(\d+)\s*(?:km/h|mph)',
    }
    
    full_text = ' '.join(text_content)
    
    for key, pattern in patterns.items():
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            specs[key] = matches[0] if matches else None
    
    # Look for specification tables or sections
    spec_keywords = ['power', 'torque', 'weight', 'displacement', 'engine', 'transmission', 
                     'suspension', 'brakes', 'dimensions', 'fuel', 'capacity']
    
    for keyword in spec_keywords:
        # Find text near keyword
        pattern = rf'{keyword}[:\s]+([^\n]+?)(?:\n|$)'
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            specs[keyword] = matches[0].strip()[:100]  # Limit length
    
    return specs


def extract_features_from_text(text_content: List[str]) -> List[str]:
    """
    Extract features from text content.
    
    Args:
        text_content: List of text strings from page
        
    Returns:
        List of features
    """
    features = []
    
    # Look for feature-like text (bullet points, lists, etc.)
    feature_keywords = ['feature', 'technology', 'equipment', 'standard', 'optional', 
                       'includes', 'equipped', 'system']
    
    full_text = ' '.join(text_content)
    
    # Simple heuristic: look for capitalized phrases that might be features
    # This is a basic implementation - could be improved
    sentences = re.split(r'[.!?]\s+', full_text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        # Look for feature-like sentences
        if any(keyword in sentence.lower() for keyword in feature_keywords):
            if len(sentence) > 10 and len(sentence) < 200:
                features.append(sentence)
    
    return features[:20]  # Limit to 20 features


async def process_snapshot(
    snapshot_file: str,
    manufacturer: str = "Ducati",
    output_dir: str = "output",
    images_dir: str = "images"
) -> Dict[str, Any]:
    """
    Process a snapshot file and extract all data.
    
    Args:
        snapshot_file: Path to snapshot file
        manufacturer: Manufacturer name
        output_dir: Output directory
        images_dir: Images directory
        
    Returns:
        Dictionary with extraction results
    """
    snapshot_path = Path(snapshot_file)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")
    
    print(f"\n📄 Processing snapshot: {snapshot_path.name}")
    
    # Parse snapshot
    parsed_data = parse_snapshot_file(snapshot_path)
    
    print(f"   ✓ URL: {parsed_data.get('url', 'Unknown')}")
    print(f"   ✓ Title: {parsed_data.get('title', 'Unknown')}")
    print(f"   ✓ Text elements: {len(parsed_data.get('text_content', []))}")
    print(f"   ✓ Images found: {len(parsed_data.get('images', []))}")
    
    # Extract specifications and features
    text_content = parsed_data.get('text_content', [])
    specifications = extract_specifications_from_text(text_content)
    features = extract_features_from_text(text_content)
    
    print(f"   ✓ Specifications: {len(specifications)}")
    print(f"   ✓ Features: {len(features)}")
    
    # Extract model and year from URL or title
    url = parsed_data.get('url', '')
    title = parsed_data.get('title', '')
    
    # Try to extract model from URL
    model = "Unknown"
    year = 2024  # Default year
    
    if '/bikes/' in url:
        parts = url.split('/bikes/')
        if len(parts) > 1:
            model_part = parts[1].split('/')[0]
            model = model_part.replace('-', ' ').title()
    
    # Try to extract year from title or URL
    year_match = re.search(r'(\d{4})', title)
    if year_match:
        year = int(year_match.group(1))
    
    # Normalize data
    normalizer = DataNormalizer()
    
    raw_data = {
        'specifications': specifications,
        'features': features,
        'description': ' '.join(text_content[:500]),  # First 500 words
        'colors': [],
        'price': None,
        'content_sections': {},
        'images': parsed_data.get('images', [])
    }
    
    bike_data = normalizer.normalize(
        raw_data=raw_data,
        manufacturer=manufacturer,
        model=model,
        year=year,
        source_url=url
    )
    
    # Create output directories
    output_path = Path(output_dir)
    images_path = Path(images_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    images_path.mkdir(parents=True, exist_ok=True)
    
    # Write markdown
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
    
    print(f"\n✅ Data extracted and saved!")
    print(f"   📁 Output: {output_path}")
    print(f"   📄 Markdown: {manufacturer}_{model}_{year}.md")
    
    return {
        'success': True,
        'manufacturer': manufacturer,
        'model': model,
        'year': year,
        'specifications_count': len(specifications),
        'features_count': len(features),
        'output_file': str(output_path / f"{manufacturer}_{model}_{year}.md")
    }


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract data from Cursor browser snapshots")
    parser.add_argument("snapshot", help="Path to snapshot file")
    parser.add_argument("--manufacturer", default="Ducati", help="Manufacturer name")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--images-dir", default="images", help="Images directory")
    
    args = parser.parse_args()
    
    try:
        result = await process_snapshot(
            snapshot_file=args.snapshot,
            manufacturer=args.manufacturer,
            output_dir=args.output_dir,
            images_dir=args.images_dir
        )
        
        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


