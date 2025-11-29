# Motorcycle OEM Web-Crawler

A comprehensive Playwright-based web crawler for systematically discovering and extracting motorcycle specifications from OEM websites, with automatic normalization to metric units and structured markdown output.

## Features

- **Multi-Strategy Discovery**: Sitemap parsing, dropdown navigation, search, and link following
- **Intelligent Classification**: Automatic bike page detection and classification
- **Comprehensive Extraction**: Specs, features, images, descriptions, colors, and pricing
- **Metric Normalization**: All measurements automatically converted to metric units
- **Multi-Page Merging**: Intelligently combines data from multiple pages per bike
- **Image Deduplication**: SHA-256 hash-based deduplication
- **Semantic Naming**: Images named with manufacturer, model, and year
- **State Persistence**: Resumable crawls with checkpoint system
- **Pydantic Validation**: Type-safe data models with validation

## Installation

```bash
# Clone repository
cd moto-scraper-v1

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install dev dependencies (optional)
pip install -r requirements-dev.txt
```

## Usage

### Basic Crawl

**Option 1: Using the wrapper script (recommended)**
```bash
python run_crawler.py https://www.ducati.com --manufacturer "Ducati" --output-dir output --images-dir images
```

**Option 2: Running as a module**
```bash
python -m src.main https://www.ducati.com --manufacturer "Ducati" --output-dir output --images-dir images
```

**Option 3: Direct execution (requires PYTHONPATH)**
```bash
PYTHONPATH=. python src/main.py https://www.ducati.com --manufacturer "Ducati" --output-dir output --images-dir images
```

### With Custom Settings

```bash
python run_crawler.py https://www.ducati.com \
  --manufacturer "Ducati" \
  --output-dir /path/to/output \
  --images-dir /path/to/images \
  --rate-limit 3.0 \
  --log-level DEBUG
```

### With Proxy (for sites blocking automated access)

**Option 1: Full proxy URL with credentials**
```bash
python run_crawler.py https://www.ducati.com \
  --manufacturer "Ducati" \
  --proxy "http://username:password@proxy-host:port"
```

**Option 2: Separate proxy host and credentials**
```bash
python run_crawler.py https://www.ducati.com \
  --manufacturer "Ducati" \
  --proxy "proxy-host:port" \
  --proxy-user "username" \
  --proxy-pass "password"
```

**Example with WebShare proxy:**
```bash
python run_crawler.py https://www.ducati.com \
  --manufacturer "Ducati" \
  --proxy "142.111.48.253:7030" \
  --proxy-user "dwpatyix" \
  --proxy-pass "egi9npccxz3j"
```

## Architecture

The crawler follows a modular architecture per the Spec Kit specification:

```
src/
├── crawler/          # Page discovery and classification
│   ├── discovery.py  # PageDiscoveryEngine
│   └── classifier.py # BikePageClassifier
├── extractors/       # Data and image extraction
│   ├── data_extractor.py
│   └── image_extractor.py
├── processors/       # Normalization and merging
│   ├── normalizer.py
│   └── merger.py
├── downloaders/      # Image downloading
│   └── image_downloader.py
├── writers/          # Output generation
│   ├── markdown_writer.py
│   └── metadata_writer.py
└── utils/           # Shared utilities
    ├── schema.py    # Pydantic models
    ├── units.py     # Unit conversions
    ├── logging.py   # Logging setup
    └── cookie_handler.py
```

## Output Structure

```
output/
└── Ducati/
    └── Panigale_V4/
        ├── Ducati_Panigale_V4_2024.md
        └── Ducati_Panigale_V4_2024_meta.json

images/
└── Ducati/
    └── Panigale_V4/
        └── 2024/
            ├── Ducati_Panigale_V4_2024_001.jpg
            ├── Ducati_Panigale_V4_2024_002.jpg
            └── ...
```

## Development

### Running Tests

```bash
pytest
pytest -v
pytest tests/test_units.py
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Troubleshooting

### Access Denied / 403 Forbidden Errors

Some websites (like Ducati.com) use bot detection (Cloudflare, etc.) that may block automated access. If you see "Access Denied" or 403 errors:

**Symptoms:**
- All discovery methods return 0 URLs
- Page title shows "Access Denied"
- HTTP status 403

**Possible Solutions:**
1. **Use a proxy** - Configure with `--proxy` flag (see examples above)
2. **Use a VPN or different IP address** - The site may be blocking your server's IP
3. **Add longer delays** - Increase `--rate-limit` to 5+ seconds
4. **Use residential proxy** - Some datacenter proxies may still be blocked; residential proxies work better
5. **Run from different location** - Some sites block certain geographic regions
6. **Manual sitemap access** - Try accessing `https://www.ducati.com/sitemap.xml` directly in a browser to verify it's accessible

**Note:** Even with a proxy, some sites (like Ducati.com) use sophisticated bot detection that may still block automated access. The proxy helps bypass IP-based blocking, but advanced detection systems may still identify automated browsers.

**Current Status:**
The crawler includes stealth features (realistic headers, webdriver property removal, etc.), but some sites may still block automated access based on IP reputation or other factors.

## Configuration

The system supports YAML-based configuration for site-specific settings (planned feature):

```yaml
target:
  base_url: "https://example-oem.com"

crawler:
  rate_limit_seconds: 2.0
  max_concurrent: 3

extraction:
  spec_table_selectors:
    - ".specifications-table"
    - ".tech-specs"
```

## Constitution Rules

This crawler strictly follows the constitution requirements:

- ✅ **Metric Units Only**: All measurements in metric (kW, Nm, mm, kg, km/h, L)
- ✅ **No Guessing**: Missing data is `None`, never guessed
- ✅ **Rate Limiting**: Minimum 2 seconds between requests
- ✅ **Multi-Page Merging**: Data from multiple pages merged intelligently
- ✅ **One Markdown Per Bike/Year**: Organized output structure
- ✅ **State Persistence**: Resumable crawls
- ✅ **Type Safety**: Full Pydantic validation

## License

See LICENSE file for details.

## Contributing

This project uses Spec Kit for development. See SPECIFICATION.md, plan.md, and tasks.md for implementation details.
