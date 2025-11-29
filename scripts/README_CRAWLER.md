# Full Site Crawler

Comprehensive crawler for motorcycle OEM websites that:
- Checks sitemap.xml for URLs
- Navigates through MODELS dropdown
- Discovers all bike pages
- Extracts all content (specs, features, descriptions, prices)
- Downloads all images to specified directory
- Creates markdown files for each bike (e.g., `Diavel_V4.md`)

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python scripts/full_site_crawler.py <URL> [options]
```

### Options

- `--output-dir`: Directory for markdown files and images (default: `/mnt/seagate4tb/moto-scraper-v1`)
- `--rate-limit`: Seconds to wait between requests (default: 2.0)

### Example

```bash
# Basic usage
python scripts/full_site_crawler.py https://www.ducati.com

# Custom output directory
python scripts/full_site_crawler.py https://www.ducati.com --output-dir /path/to/output

# Faster crawling (lower rate limit - use responsibly!)
python scripts/full_site_crawler.py https://www.ducati.com --rate-limit 1.0
```

## Features

### 1. Sitemap Discovery
- Automatically checks for `sitemap.xml` and `sitemap_index.xml`
- Extracts all bike-related URLs from sitemap

### 2. Dropdown Navigation
- Handles cookie consent (OneTrust and others)
- Clicks MODELS dropdown
- Extracts all bike links from dropdown menu
- Handles lazy-loaded content

### 3. Content Extraction
- **Specifications**: Power, torque, weight, dimensions, etc.
- **Features**: Feature lists and descriptions
- **Pricing**: Price information if available
- **Colors**: Available color options
- **Images**: All images on the page (including lazy-loaded)

### 4. Image Download
- Downloads all images to `{output_dir}/images/{bike_name}/`
- Deduplicates images using SHA-256 hashing
- Preserves original file formats (jpg, png, webp)
- Generates semantic filenames: `{bike_name}_{index}.{ext}`

### 5. Markdown Generation
- Creates one markdown file per bike: `{Bike_Name}.md`
- Includes all extracted content
- Links to downloaded images with relative paths
- Includes source URL and extraction timestamp

## Output Structure

```
/mnt/seagate4tb/moto-scraper-v1/
├── images/
│   ├── DesertX/
│   │   ├── DesertX_001.jpg
│   │   ├── DesertX_002.jpg
│   │   └── ...
│   ├── Diavel_V4/
│   │   ├── Diavel_V4_001.jpg
│   │   └── ...
│   └── ...
├── DesertX.md
├── Diavel_V4.md
├── ...
└── crawl_state.json
```

## State Management

The crawler maintains state in `crawl_state.json`:
- Tracks visited URLs to avoid re-crawling
- Allows resuming interrupted crawls
- Saves progress every 5 pages

## Error Handling

- Gracefully handles missing elements
- Continues crawling even if individual pages fail
- Logs all errors to `crawler.log`
- Takes screenshots on critical errors

## Rate Limiting

Default rate limit is 2 seconds between requests. Adjust based on:
- Site's robots.txt recommendations
- Server capacity
- Your ethical considerations

## Notes

- The crawler runs with browser visible by default (`headless=False`) for debugging
- Set `headless=True` in the code for production use
- Images are downloaded asynchronously for better performance
- All content is extracted from the rendered page (handles JavaScript)


