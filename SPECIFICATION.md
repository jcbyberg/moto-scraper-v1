# Motorcycle OEM Web-Crawler System Specification

## System Overview

The Motorcycle OEM Web-Crawler is a Playwright-based full-site crawler that systematically discovers all internal pages within a target OEM domain, identifies bike-related pages, extracts specifications/features/images, normalizes data into a unified schema, downloads images with semantic naming, and produces structured output including one markdown file per model/year combination, organized image folders, and metadata files.

---

## System Architecture

### High-Level Flow

```
┌─────────────────┐
│  Configuration  │
│   (Target URL)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Page Discovery  │◄────────┐
│   (Crawler)     │          │
└────────┬────────┘          │
         │                   │
         ▼                   │
┌─────────────────┐         │
│  Page Classifier │         │
│ (Bike Detector)  │         │
└────────┬────────┘          │
         │                   │
    ┌────┴────┐              │
    │         │              │
    ▼         ▼              │
┌──────┐  ┌──────────┐       │
│ Bike │  │  Other   │       │
│ Page │  │  Page    │       │
└──┬───┘  └────┬─────┘       │
   │           │             │
   │           └─────────────┘
   │
   ▼
┌─────────────────┐
│ Data Extractor  │
│ (Specs/Features)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Image Extractor │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Normalizer │
│ (Schema/Units)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Merger     │
│ (Multi-page)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Image Downloader│
│ (Semantic Names)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Markdown Writer │
│ (Per Bike/Year) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Metadata Writer │
└─────────────────┘
```

---

## Component Specifications

### 1. Page Discovery Engine (Crawler)

**Purpose**: Discover all internal pages within the target domain.

**Responsibilities**:
- Start from seed URL(s)
- Follow all internal links recursively
- Maintain visited URL registry
- Respect robots.txt
- Handle rate limiting
- Track crawl state for resumption

**Interface**:
```python
class PageDiscoveryEngine:
    def __init__(
        self,
        base_url: str,
        max_depth: int = None,
        rate_limit_seconds: float = 2.0,
        max_concurrent: int = 3,
        respect_robots: bool = True
    ) -> None
    
    async def discover_all_pages(self) -> AsyncIterator[str]:
        """Yields URLs of all discovered internal pages."""
        
    def get_visited_count(self) -> int:
        """Returns count of pages visited."""
        
    def save_state(self, filepath: str) -> None:
        """Save crawl state for resumption."""
        
    def load_state(self, filepath: str) -> None:
        """Load crawl state to resume crawling."""
```

**Implementation Details**:
- Use Playwright's `Browser` and `Page` objects
- Extract links using `page.query_selector_all('a[href]')`
- Filter links to same domain using `urlparse`
- Maintain `visited_urls: set[str]` and `pending_urls: deque[str]`
- Use asyncio semaphore for concurrency control
- Implement exponential backoff on errors
- **Cookie consent handling**: Automatically detect and accept cookie consent dialogs before crawling
- **JavaScript interactions**: Handle dropdowns, modals, and other JS-rendered navigation elements

---

### 2. Bike Page Classifier

**Purpose**: Identify which pages contain bike model information.

**Responsibilities**:
- Analyze page content and URL patterns
- Detect bike model pages vs. other pages
- Extract preliminary model/year information
- Group related pages (main page, specs page, gallery, etc.)

**Interface**:
```python
class BikePageClassifier:
    def __init__(self, manufacturer: str) -> None
    
    def is_bike_page(self, url: str, page_content: str) -> bool:
        """Determine if page contains bike model information."""
        
    def extract_model_info(self, url: str, page_content: str) -> dict[str, Any] | None:
        """Extract preliminary model, year, variant from page."""
        # Returns: {"model": str, "year": int, "variant": str | None}
        
    def get_page_type(self, url: str, content: str) -> str:
        """Classify page type: 'main', 'specs', 'gallery', 'features', 'other'."""
        
    def group_related_pages(self, pages: list[dict]) -> dict[str, list[dict]]:
        """Group pages by model/year combination."""
```

**Detection Strategies**:
- URL pattern matching (e.g., `/motorcycles/{model}/{year}/`)
- Content analysis (presence of spec tables, model names, year indicators)
- HTML structure analysis (common bike page patterns)
- Keyword detection (specifications, features, technical details)

---

### 3. Data Extractor

**Purpose**: Extract specifications, features, descriptions, and other bike data from pages.

**Responsibilities**:
- Parse HTML structure to find specification tables
- Extract text content (descriptions, features)
- Identify structured data (specs in tables, lists)
- Extract pricing information
- Extract color options
- Handle various page layouts and structures

**Interface**:
```python
class DataExtractor:
    def __init__(self) -> None
    
    async def extract_from_page(
        self,
        page: Page,
        page_type: str
    ) -> dict[str, Any]:
        """Extract all available data from a page."""
        # Returns raw extracted data dict
        
    def extract_specifications(self, page: Page) -> dict[str, Any]:
        """Extract specification tables/data."""
        
    def extract_features(self, page: Page) -> list[str]:
        """Extract feature list."""
        
    def extract_description(self, page: Page) -> str:
        """Extract main description text."""
        
    def extract_colors(self, page: Page) -> list[str]:
        """Extract available color options."""
        
    def extract_pricing(self, page: Page) -> dict[str, Any] | None:
        """Extract pricing information if available."""
```

**Extraction Strategies**:
- CSS selector-based extraction (tables, lists, divs with specific classes)
- XPath queries for structured data
- Text pattern matching (regex for specs like "XXX cc", "XXX kW")
- Multiple fallback strategies for different page layouts
- Handle both table-based and list-based spec presentations

---

### 4. Image Extractor

**Purpose**: Identify and extract all image URLs associated with a bike model.

**Responsibilities**:
- Find all images on bike pages
- Filter relevant images (exclude logos, icons, UI elements)
- Extract high-resolution image URLs
- Identify image metadata (alt text, captions)
- Handle lazy-loaded images
- Detect image galleries and carousels

**Interface**:
```python
class ImageExtractor:
    def __init__(self) -> None
    
    async def extract_images(
        self,
        page: Page,
        model: str,
        year: int
    ) -> list[dict[str, Any]]:
        """Extract all relevant images from page."""
        # Returns: [{"url": str, "alt": str, "type": str}, ...]
        
    def filter_relevant_images(
        self,
        images: list[dict],
        model: str
    ) -> list[dict]:
        """Filter out non-bike images (logos, icons, etc.)."""
        
    async def wait_for_lazy_images(self, page: Page) -> None:
        """Wait for lazy-loaded images to load."""
```

**Image Detection**:
- Find `<img>` tags with `src` and `srcset` attributes
- Detect background images in CSS
- Handle JavaScript-rendered image galleries
- Extract full-resolution URLs from thumbnails
- Filter by image dimensions (exclude small icons)
- Use alt text and surrounding context to determine relevance

---

### 5. Data Normalizer

**Purpose**: Normalize extracted data into unified schema with metric units.

**Responsibilities**:
- Convert all measurements to metric units
- Map extracted fields to standard schema
- Validate data types
- Handle missing/optional fields
- Preserve data precision
- Detect and parse units from text

**Interface**:
```python
class DataNormalizer:
    def __init__(self) -> None
    
    def normalize(
        self,
        raw_data: dict[str, Any],
        source_url: str
    ) -> dict[str, Any]:
        """Normalize raw extracted data to standard schema."""
        
    def convert_to_metric(
        self,
        value: float,
        unit: str,
        target_unit: str
    ) -> float:
        """Convert value from source unit to metric target unit."""
        
    def parse_spec_value(self, text: str) -> tuple[float | None, str | None]:
        """Parse numeric value and unit from text string."""
        
    def validate_schema(self, data: dict) -> tuple[bool, list[str]]:
        """Validate data against schema, return (is_valid, errors)."""
```

**Unit Conversion Rules**:
- Power: hp → kW (multiply by 0.7457)
- Torque: lb-ft → Nm (multiply by 1.3558)
- Length: inches → mm (multiply by 25.4), feet → mm (multiply by 304.8)
- Weight: lbs → kg (multiply by 0.453592)
- Speed: mph → km/h (multiply by 1.60934)
- Volume: gallons → liters (multiply by 3.78541)
- Fuel consumption: mpg → L/100km (235.214 / mpg)

**Schema Mapping**:
- Map common field names to schema fields (e.g., "Engine Size" → "displacement_cc")
- Handle variations in field naming across sites
- Preserve original values in metadata for debugging

---

### 6. Data Merger

**Purpose**: Merge data from multiple pages for the same bike model/year.

**Responsibilities**:
- Group data by model/year combination
- Merge specifications from different pages
- Resolve conflicts (prefer authoritative sources)
- Combine features and descriptions
- Aggregate image URLs
- Track source URLs for each data point

**Interface**:
```python
class DataMerger:
    def __init__(self) -> None
    
    def merge_bike_data(
        self,
        pages_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Merge data from multiple pages for same bike."""
        
    def resolve_conflict(
        self,
        values: list[tuple[Any, str]],
        page_types: list[str]
    ) -> Any:
        """Resolve conflicts when same field has different values."""
        # Prefer: specs page > main page > gallery page
        
    def combine_features(self, features_lists: list[list[str]]) -> list[str]:
        """Combine and deduplicate feature lists."""
        
    def aggregate_source_urls(
        self,
        pages_data: list[dict]
    ) -> list[str]:
        """Collect all source URLs."""
```

**Merging Strategy**:
- Priority order: specs page > main page > features page > gallery page
- For numeric values: prefer most specific/precise value
- For text: combine with deduplication
- Preserve all source URLs
- Mark fields with multiple sources in metadata

---

### 7. Image Downloader

**Purpose**: Download images with semantic filenames and organize in folder structure.

**Responsibilities**:
- Download images from URLs
- Generate semantic filenames based on content
- Organize into folder structure by manufacturer/model/year
- Deduplicate identical images (hash-based)
- Handle download errors gracefully
- Preserve image metadata

**Interface**:
```python
class ImageDownloader:
    def __init__(
        self,
        base_output_dir: str,
        max_size_mb: float = 10.0
    ) -> None
    
    async def download_images(
        self,
        image_urls: list[dict[str, Any]],
        manufacturer: str,
        model: str,
        year: int
    ) -> list[str]:
        """Download images and return local file paths."""
        
    def generate_semantic_filename(
        self,
        url: str,
        alt_text: str,
        image_type: str,
        index: int
    ) -> str:
        """Generate descriptive filename from image metadata."""
        
    def get_image_hash(self, filepath: str) -> str:
        """Calculate hash for deduplication."""
        
    def is_duplicate(self, filepath: str, known_hashes: set[str]) -> bool:
        """Check if image is duplicate."""
```

**Semantic Naming Convention**:
- Format: `{manufacturer}_{model}_{year}_{type}_{index}.{ext}`
- Types: `main`, `gallery`, `detail`, `specs`, `feature`
- Use alt text when available: `{manufacturer}_{model}_{year}_{sanitized_alt}.{ext}`
- Fallback to index if no metadata: `{manufacturer}_{model}_{year}_{index:03d}.{ext}`

**Folder Structure**:
```
images/
  {manufacturer}/
    {model}/
      {year}/
        {manufacturer}_{model}_{year}_main_001.jpg
        {manufacturer}_{model}_{year}_gallery_001.jpg
        ...
```

---

### 8. Markdown Writer

**Purpose**: Generate one markdown file per model/year combination.

**Responsibilities**:
- Format normalized data into markdown
- Include all specifications in structured format
- Embed images with relative paths
- Include source attribution
- Handle missing/optional fields gracefully

**Interface**:
```python
class MarkdownWriter:
    def __init__(self, output_dir: str) -> None
    
    def write_bike_markdown(
        self,
        bike_data: dict[str, Any],
        image_paths: list[str]
    ) -> str:
        """Write markdown file and return filepath."""
        
    def format_specifications(self, specs: dict) -> str:
        """Format specifications section."""
        
    def format_images(self, image_paths: list[str], base_path: str) -> str:
        """Format images section with relative paths."""
        
    def sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename."""
```

**Output Structure**:
```
output/
  {manufacturer}/
    {model}/
      {manufacturer}_{model}_{year}.md
```

**Markdown Template**: See `.constitution` section 5.2 for detailed structure.

---

### 9. Metadata Writer

**Purpose**: Generate structured metadata files for each bike.

**Responsibilities**:
- Save normalized JSON data
- Include extraction metadata (timestamps, source URLs)
- Store image metadata (URLs, local paths, hashes)
- Enable data reprocessing and debugging

**Interface**:
```python
class MetadataWriter:
    def __init__(self, output_dir: str) -> None
    
    def write_metadata(
        self,
        bike_data: dict[str, Any],
        extraction_metadata: dict[str, Any]
    ) -> str:
        """Write JSON metadata file and return filepath."""
```

**Metadata Structure**:
```json
{
  "bike_data": { /* normalized schema */ },
  "extraction": {
    "timestamp": "ISO 8601",
    "source_urls": ["url1", "url2"],
    "page_types": ["main", "specs", "gallery"],
    "extractor_version": "1.0"
  },
  "images": [
    {
      "url": "original_url",
      "local_path": "relative/path",
      "hash": "sha256_hash",
      "alt_text": "description"
    }
  ]
}
```

---

### 10. UI Interaction Handler

**Purpose**: Handle cookie consent dialogs, modals, dropdowns, and other JavaScript-rendered UI elements that may block content access.

**Responsibilities**:
- Detect and accept cookie consent dialogs
- Dismiss blocking modals and overlays
- Handle JavaScript-based navigation (dropdowns, menus)
- Wait for dynamic content to load
- Handle site-specific UI patterns

**Interface**:
```python
class UIInteractionHandler:
    def __init__(self, page: Page) -> None
    
    async def handle_cookie_consent(
        self,
        custom_selector: str | None = None
    ) -> bool:
        """Detect and accept cookie consent. Returns True if handled."""
        
    async def dismiss_modals(self) -> None:
        """Dismiss any blocking modals or overlays."""
        
    async def handle_dropdown(
        self,
        dropdown_selector: str,
        option_selector: str | None = None,
        option_index: int | None = None
    ) -> bool:
        """Click dropdown and select option if specified."""
        
    async def wait_for_interactive(self, timeout: int = 5000) -> None:
        """Wait for page to be fully interactive."""
```

**Implementation Details**:
- Use common cookie consent button selectors (OneTrust, custom implementations)
- Try multiple selectors with fallback chain
- Handle both visible and hidden elements that become visible
- Support site-specific selectors via configuration
- Log all interactions for debugging

---

## Data Flow

### Complete Processing Pipeline

1. **Initialization**
   - Load configuration (target URL, output directory, settings)
   - Initialize Playwright browser
   - Load crawl state if resuming

2. **Initial Page Setup** (first page only)
   - Navigate to seed URL
   - Handle cookie consent dialogs
   - Dismiss any blocking modals/overlays
   - Wait for page to be interactive

3. **Page Discovery**
   - Start from seed URL
   - Discover all internal pages
   - Maintain visited/pending queues
   - Rate limit requests
   - Handle cookie consent on each new domain (if needed)

3. **Page Classification**
   - For each discovered page:
     - Load page with Playwright
     - Classify as bike page or other
     - Extract preliminary model/year info
     - Group related pages

4. **Data Extraction** (for bike pages)
   - Extract specifications
   - Extract features and description
   - Extract colors and pricing
   - Extract images

5. **Data Normalization**
   - Convert to standard schema
   - Convert units to metric
   - Validate data types
   - Handle missing fields

6. **Data Merging**
   - Group by model/year
   - Merge multi-page data
   - Resolve conflicts
   - Aggregate source URLs

7. **Image Download**
   - Download all images
   - Generate semantic filenames
   - Organize in folder structure
   - Deduplicate

8. **Output Generation**
   - Write markdown file per bike/year
   - Write metadata JSON file
   - Update progress tracking

9. **Completion**
   - Save final crawl state
   - Generate summary statistics
   - Log completion

---

## File Structure

```
moto-scraper-v1/
├── .constitution              # Core rules and principles
├── SPECIFICATION.md          # This file
├── config/
│   ├── config.yaml           # Configuration file
│   └── schema.json           # Data schema definition
├── src/
│   ├── __init__.py
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── discovery.py      # PageDiscoveryEngine
│   │   └── classifier.py     # BikePageClassifier
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── data_extractor.py # DataExtractor
│   │   └── image_extractor.py # ImageExtractor
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── normalizer.py     # DataNormalizer
│   │   └── merger.py         # DataMerger
│   ├── downloaders/
│   │   ├── __init__.py
│   │   └── image_downloader.py # ImageDownloader
│   ├── writers/
│   │   ├── __init__.py
│   │   ├── markdown_writer.py # MarkdownWriter
│   │   └── metadata_writer.py # MetadataWriter
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── units.py          # Unit conversion utilities
│   │   ├── schema.py         # Schema validation
│   │   ├── logging.py        # Logging configuration
│   │   └── cookie_handler.py  # Cookie consent and UI interaction handler
│   └── main.py               # Main entry point
├── output/
│   ├── {manufacturer}/
│   │   ├── {model}/
│   │   │   ├── {manufacturer}_{model}_{year}.md
│   │   │   └── {manufacturer}_{model}_{year}.json
├── images/
│   ├── {manufacturer}/
│   │   ├── {model}/
│   │   │   ├── {year}/
│   │   │   │   ├── {semantic_filenames}.jpg
├── state/
│   ├── crawl_state.json      # Crawl progress state
│   └── visited_urls.json     # Visited URLs registry
├── logs/
│   └── crawler.log           # Application logs
├── scripts/
│   └── test_site_navigation.py  # Test script for site navigation
├── tests/
│   ├── __init__.py
│   ├── test_normalizer.py
│   ├── test_units.py
│   └── test_extractor.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Configuration Schema

```yaml
# config/config.yaml
target:
  base_url: "https://example-oem.com"
  seed_urls:
    - "https://example-oem.com/motorcycles"
  
crawler:
  max_depth: null  # null = unlimited
  rate_limit_seconds: 2.0
  max_concurrent: 3
  respect_robots: true
  timeout_seconds: 30
  max_retries: 3
  
extraction:
  manufacturer: "Example OEM"
  page_detection_patterns:
    - "/motorcycles/"
    - "/bikes/"
  spec_table_selectors:
    - ".specifications-table"
    - ".tech-specs"
  
images:
  max_size_mb: 10.0
  allowed_formats: ["jpg", "jpeg", "png", "webp"]
  min_dimensions: [200, 200]  # width, height
  
output:
  base_dir: "./output"
  images_dir: "./images"
  state_dir: "./state"
  logs_dir: "./logs"
  
logging:
  level: "INFO"
  file: "logs/crawler.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## Error Handling

### Error Categories

1. **Network Errors**
   - Timeouts: Retry with exponential backoff
   - Connection errors: Log and skip, continue
   - HTTP errors (404, 500): Log and skip

2. **Parsing Errors**
   - Malformed HTML: Log warning, attempt fallback selectors
   - Missing expected elements: Log, use None for missing data
   - Unit parsing failures: Log, preserve original text

3. **Data Validation Errors**
   - Schema violations: Log error, save partial data
   - Type mismatches: Attempt conversion, log if fails
   - Missing required fields: Log warning, skip bike if critical

4. **File System Errors**
   - Permission errors: Log and fail gracefully
   - Disk full: Log error and stop
   - Path creation failures: Log and skip

### Error Recovery

- **Checkpoint System**: Save state after each successful bike extraction
- **Resume Capability**: Load state and continue from last checkpoint
- **Partial Results**: Save what was successfully extracted even if complete extraction fails
- **Error Reporting**: Comprehensive error log with context for debugging

---

## Performance Requirements

### Scalability
- Handle sites with 1000+ pages
- Process 100+ bike models
- Download 1000+ images
- Complete full crawl in reasonable time (hours, not days)

### Resource Usage
- Memory: Efficient streaming, avoid loading all pages in memory
- Disk: Organize output to prevent directory bloat
- Network: Respect rate limits, efficient connection reuse

### Monitoring
- Progress tracking: Pages crawled, bikes extracted, images downloaded
- Performance metrics: Pages/minute, extraction success rate
- Error rates: Track and report error categories

---

## Testing Strategy

### Unit Tests
- Unit conversion functions
- Schema validation
- Filename sanitization
- URL parsing and filtering

### Integration Tests
- End-to-end extraction from sample pages
- Multi-page data merging
- Image download and organization
- Markdown generation

### Test Data
- Mock HTML pages with various structures
- Sample specification tables
- Test images for download functionality

---

## Dependencies

### Core Dependencies
```txt
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pyyaml>=6.0
pydantic>=2.0  # For schema validation
aiohttp>=3.9.0  # For async image downloads
Pillow>=10.0  # For image processing
```

### Development Dependencies
```txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
mypy>=1.5.0
```

---

## Implementation Phases

### Phase 1: Core Crawling
- Page discovery engine
- Basic page classification
- State management

### Phase 2: Data Extraction
- Specification extraction
- Feature extraction
- Image URL extraction

### Phase 3: Data Processing
- Normalization and unit conversion
- Schema validation
- Multi-page merging

### Phase 4: Output Generation
- Image downloading with semantic names
- Markdown generation
- Metadata files

### Phase 5: Polish & Optimization
- Error handling refinement
- Performance optimization
- Comprehensive testing

---

## Success Criteria

A successful crawl is achieved when:

1. ✅ All internal pages within domain have been discovered
2. ✅ All bike pages have been identified and classified
3. ✅ All bike data has been extracted and normalized
4. ✅ All measurements are in metric units
5. ✅ Multi-page data has been merged correctly
6. ✅ No guessed values (missing data marked as None)
7. ✅ All images downloaded with semantic filenames
8. ✅ One markdown file created per model/year
9. ✅ Images organized in proper folder structure
10. ✅ Metadata files generated for all bikes
11. ✅ Source URLs included in all outputs
12. ✅ Crawling completed with respectful rate limiting
13. ✅ All errors logged and handled gracefully

---

**Version**: 1.0  
**Last Updated**: 2024  
**Status**: Active Specification

