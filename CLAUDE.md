# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Motorcycle OEM Web-Crawler is a Playwright-based full-site crawler that systematically discovers all internal pages within a target OEM domain, identifies bike-related pages, extracts specifications/features/images, normalizes data into a unified schema, downloads images with semantic naming, and produces structured output.
To make **Claude Code** (the CLI tool) follow the **Spec Kit** specifications that you are using in Cursor, you need to bridge the gap between how Cursor handles context (via `.cursorrules`) and how Claude Code handles context (via `CLAUDE.md`).

Spec Kit works by generating markdown files (usually in a `specs/` or `.specify/` folder) that define your project's plan. While Cursor often reads these automatically via its rules, Claude Code needs to be explicitly told where to look.

Here is the step-by-step guide to setting this up.

### 1. Create (or Update) `CLAUDE.md`
Claude Code looks for a file named `CLAUDE.md` in the root of your project every time it runs. This is the equivalent of `.cursorrules`. You need to configure this file to point to your Spec Kit files.

Create a `CLAUDE.md` file in your project root with the following content:

```markdown
# Claude Code Project Configuration

## Spec-Driven Development (Spec Kit)
This project uses Spec Kit for development. You must strictly follow the specifications defined in the `specs/` directory.

### Active Context
Before writing any code or running commands, **always** read the following files to understand the current task and architecture:
- `specs/active/spec.md` (The requirements and user stories)
- `specs/active/plan.md` (The technical implementation plan)
- `specs/active/tasks.md` (The checklist of tasks to complete)

## Project Rules (Constitution)
1. **Do not deviate from the plan**: If you find a better way to implement something, update `specs/active/plan.md` first, ask for confirmation, and *then* code.
2. **Update Status**: When a task from `specs/active/tasks.md` is completed, mark it as done in the file.
3. **No Vibe Coding**: Do not guess implementation details. Refer to the `data-model.md` or `contracts/` if available.
```

*(Note: Adjust the file paths above if your Spec Kit version uses a different folder structure, such as `.specify/` instead of `specs/`.)*

### 2. Initialize Spec Kit for Claude (If using the CLI)
If you are using the `spec-kit` CLI tool (e.g., from GitHub), it may have an initialization command that sets this up for you automatically.

Run this command in your terminal:
```bash
# Attempt to initialize spec-kit specifically for Claude
spec-kit init --ai claude
# OR if you are using the 'specify' CLI tool
specify init --ai claude
```
If your version of Spec Kit supports this flag, it will automatically generate a `CLAUDE.md` or prompts optimized for Claude.

### 3. How to Workflow with Claude Code
Once your `CLAUDE.md` is set up, you can run Claude Code in your terminal. It will automatically ingest the instructions.

*   **Starting a Task:**
    ```bash
    claude "Implement the next task in tasks.md"
    ```
    *Because of `CLAUDE.md`, Claude will automatically read the spec and plan files first.*

*   **Updating Specs:**
    You can also tell Claude to update the specs, just like in Cursor:
    ```bash
    claude "I want to add a dark mode. Update spec.md and plan.md to reflect this change."
    ```

### Summary of Differences
| Feature | Cursor (Cursor Rules) | Claude Code (CLI) |
| :--- | :--- | :--- |
| **Config File** | `.cursorrules` or `.cursor/rules` | `CLAUDE.md` |
| **Context Loading** | Automatic (often implicit) | Must be referenced in `CLAUDE.md` |
| **Spec Kit Files** | Reads from `specs/` via rules | Reads from `specs/` via `CLAUDE.md` instructions |

**Pro Tip:** If you have a very complex `.cursorrules` file with many custom coding conventions, you should copy the "Coding Standards" section from that file and paste it into your `CLAUDE.md` so Claude follows the same linting and style guides as Cursor.

## Core Architecture

### Technology Stack
- **Playwright** (>=1.40.0) - Browser automation and page interaction
- **Python 3.9+** - Primary language with async/await architecture
- **aiohttp** (>=3.9.0) - Async HTTP client for image downloads
- **aiofiles** (>=23.0.0) - Async file operations
- **BeautifulSoup4** (>=4.12.0) - HTML parsing
- **lxml** (>=4.9.0) - Fast XML/HTML parsing
- **Pydantic** (>=2.0) - Schema validation (planned)
- **PyYAML** (>=6.0) - Configuration file parsing (planned)

### High-Level Data Flow

```
Page Discovery → Classification → Extraction → Normalization → Merging → Image Download → Markdown Output
```

1. **Page Discovery**: Multiple strategies (sitemap, dropdown, search, link-following)
2. **Classification**: Identify bike pages vs. other pages
3. **Extraction**: Extract specs, features, images, descriptions
4. **Normalization**: Convert to metric units, standard schema
5. **Merging**: Combine data from multiple pages per bike/year
6. **Image Download**: Semantic naming, SHA-256 deduplication
7. **Output**: One markdown file per bike/year with relative image paths

### Component Structure

```
src/
├── crawler/           # Page discovery and classification
│   ├── discovery.py   # PageDiscoveryEngine
│   └── classifier.py  # BikePageClassifier
├── extractors/        # Data and image extraction
│   ├── data_extractor.py
│   └── image_extractor.py
├── processors/        # Normalization and merging
│   ├── normalizer.py  # DataNormalizer
│   └── merger.py      # DataMerger
├── downloaders/       # Image downloading
│   └── image_downloader.py
├── writers/           # Output generation
│   ├── markdown_writer.py
│   └── metadata_writer.py
└── utils/            # Shared utilities
    ├── units.py      # Unit conversion
    ├── schema.py     # Pydantic schema models
    ├── logging.py    # Logging configuration
    └── cookie_handler.py  # Cookie consent & UI interaction
```

## Development Commands

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running the Crawler
```bash
# Full site crawl
python scripts/full_site_crawler.py https://example-oem.com --output-dir /path/to/output --rate-limit 2.0

# Test navigation only
python scripts/test_site_navigation.py https://example-oem.com
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_normalizer.py

# Run with verbose output
pytest -v

# Run specific test function
pytest tests/test_units.py::test_convert_power_hp_to_kw
```

### Code Quality
```bash
# Format code
black src/ tests/

# Type checking
mypy src/
```

## Critical Implementation Rules (from .constitution)

### 1. Metric Units Requirement
**ALL measurements MUST be in metric units:**
- Length/dimensions: millimeters (mm)
- Weight: kilograms (kg)
- Displacement: cubic centimeters (cc)
- Power: kilowatts (kW) - convert from hp: 1 hp ≈ 0.7457 kW
- Torque: Newton-meters (Nm)
- Speed: kilometers per hour (km/h)
- Volume: liters (L)
- Fuel consumption: liters per 100 kilometers (L/100km)

### 2. Data Quality Rules
- **NO guessing values**: If a specification is not found, use `None` or omit the field
- **Preserve precision**: Maintain original precision when converting units
- **Type validation**: Ensure numeric fields are properly typed (int vs float)
- **Required fields**: Manufacturer, model, and year are mandatory; all others optional

### 3. Crawling Strategy
- **Rate limiting**: Minimum 2 seconds between requests (configured via `rate_limit` parameter)
- **Respect robots.txt**: Parse and comply with directives
- **User-Agent**: Use descriptive, honest user-agent string
- **Max retries**: Limit to 3 retries with exponential backoff
- **State persistence**: Save state after each bike for resumption

### 4. Multi-Page Data Merging
When a bike is described across multiple pages (main, specs, gallery):
- **Merge data** from all pages for the same bike/year
- **Track source attribution**: Record which page each data point came from
- **Conflict resolution**: Prefer specs page > main page > gallery page
- **Combine features**: Deduplicate feature lists
- **Aggregate source URLs**: Include all source URLs in output

### 5. Output Format
- **One markdown file per bike/year**: Named `{manufacturer}_{model}_{year}.md`
- **Organized images**: `images/{manufacturer}/{model}/{year}/`
- **Semantic image naming**: `{manufacturer}_{model}_{year}_{type}_{index}.{ext}`
- **Relative paths**: Images use relative paths in markdown
- **Metadata files**: JSON file per bike with normalized data and extraction metadata

## Existing Implementation Status

### Currently Implemented (in scripts/)
The `scripts/full_site_crawler.py` file contains a working prototype with:
- Cookie consent handling via `CookieHandler`
- Multi-strategy page discovery (sitemap, dropdown, search, link-following)
- Post-crawl search for missed pages
- Basic data extraction (specs, features, images, colors, price)
- Image download with SHA-256 deduplication
- Markdown file generation with relative image paths
- State persistence for resumable crawls

### To Be Implemented (following tasks.md)
The full architecture requires implementing modular components:
- Proper bike page classification (vs. prototype's basic URL matching)
- Pydantic schema validation
- Comprehensive unit conversion utilities
- Multi-page data merging with conflict resolution
- Advanced extraction strategies with fallbacks
- Site-specific configuration system (YAML-based)
- Complete test suite

## Key Design Patterns

### 1. Multi-Strategy Discovery
The crawler uses four complementary discovery methods:
- **Sitemap parsing**: Extract URLs from sitemap.xml
- **Dropdown navigation**: Click MODELS dropdown and extract bike links
- **Search-based**: Use site search with bike-related terms
- **Link following**: Recursively follow internal links from key pages
- **Post-crawl search**: Pattern-based checking for missed pages

### 2. Cookie Consent Handling
The `CookieHandler` class handles common cookie consent patterns:
- OneTrust integration (#onetrust-accept-btn-handler)
- Multiple fallback selectors for accept buttons
- Site-specific custom selectors via parameter
- Modal dismissal support

### 3. Image Deduplication
Uses SHA-256 hashing to prevent downloading duplicate images:
- Global hash registry across all bikes
- Skip already-downloaded images
- Maintain hash set in memory and persist in state

### 4. State Management
Resumable crawls via JSON state files:
- Track visited URLs
- Save state every 5 pages
- Load previous state on restart
- Enable long-running crawls to recover from interruptions

## Important Notes

### Working with Existing Code
The `scripts/full_site_crawler.py` is a working prototype that implements the core workflow. When building the modular architecture:
- **Extract patterns** from the prototype into reusable components
- **Preserve working logic** for discovery, extraction, and image handling
- **Maintain compatibility** with the state file format for resumability

### Code Standards
All code must follow these standards (from .constitution):
- **Python type hints**: All function signatures must have type hints
- **Comprehensive logging**: Structured logging for all operations
- **Error handling**: Try/except blocks with graceful degradation
- **Async-first**: All I/O operations use async/await

### Testing Strategy
- **Unit tests**: Unit conversion, schema validation, URL normalization
- **Integration tests**: End-to-end extraction from sample HTML
- **Test data**: Mock HTML pages with various structures

## Configuration

### Site-Specific Configuration (Planned)
The system will support YAML-based configurations for different OEM sites:
- Custom CSS selectors for specs, features, images
- Field name mappings (site-specific labels → schema fields)
- URL patterns for bike page detection
- Cookie consent selectors

### Example Configuration Structure
```yaml
target:
  base_url: "https://example-oem.com"
  seed_urls:
    - "https://example-oem.com/motorcycles"

crawler:
  max_depth: null
  rate_limit_seconds: 2.0
  max_concurrent: 3
  respect_robots: true

extraction:
  manufacturer: "Example OEM"
  spec_table_selectors:
    - ".specifications-table"
    - ".tech-specs"
```

## Documentation References

For detailed specifications, see:
- **SPECIFICATION.md**: Complete system architecture and component specifications
- **.constitution**: Core principles and non-negotiable requirements
- **tasks.md**: Detailed implementation task breakdown (88 tasks across 9 groups)
- **plan.md**: Implementation phases and timeline

## Common Pitfalls to Avoid

1. **Never guess missing data**: Use `None` instead of placeholder values
2. **Always convert to metric**: Even if source data is already metric, verify units
3. **Preserve precision**: Don't round during unit conversion
4. **Handle multi-page data**: Same bike may span main page, specs page, gallery
5. **Use relative paths**: Image paths in markdown must be relative to markdown file location
6. **Rate limit properly**: Respect the configured rate limit to avoid overwhelming servers
7. **Save state frequently**: Checkpoint after each successful bike extraction
