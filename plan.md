# Motorcycle OEM Web-Crawler Implementation Plan

## Executive Summary

This plan outlines the implementation of a comprehensive Playwright-based web crawler for motorcycle OEM websites. The system will discover all internal pages, classify bike-related content, extract specifications/images, normalize data into a unified schema, and produce structured markdown output with organized image folders.

**Target**: Full implementation of the crawler system as specified in `SPECIFICATION.md` and adhering to `.constitution` principles.

---

## Technical Context

### Technology Stack

**Core Framework**:
- **Playwright** (>=1.40.0) - Browser automation and page interaction
- **Python 3.9+** - Primary language (as per constitution requirement)
- **asyncio** - Asynchronous operations for concurrent crawling
- **aiohttp** (>=3.9.0) - Async HTTP client for image downloads
- **aiofiles** (>=23.0.0) - Async file operations

**Data Processing**:
- **BeautifulSoup4** (>=4.12.0) - HTML parsing (fallback/alternative)
- **lxml** (>=4.9.0) - Fast XML/HTML parsing
- **Pydantic** (>=2.0) - Schema validation and data modeling
- **PyYAML** (>=6.0) - Configuration file parsing

**Utilities**:
- **hashlib** - Image deduplication (SHA-256)
- **Pillow** (>=10.0) - Image processing and validation

### Architecture Decisions

1. **Modular Component Design**: Each major function (discovery, extraction, normalization, etc.) is a separate class/module for maintainability and testability.

2. **Async-First Architecture**: All I/O operations (network, file) use async/await for better performance and resource utilization.

3. **State Management**: Persistent state tracking allows resuming interrupted crawls without re-processing.

4. **Multi-Strategy Discovery**: Combine sitemap, dropdown navigation, search, and link-following for comprehensive coverage.

5. **Schema-Driven Normalization**: Use Pydantic models for type-safe data validation and conversion.

6. **Fallback Extraction**: Multiple extraction strategies per data point to handle varying site structures.

### Dependencies

**External Services**:
- Target OEM websites (e.g., ducati.com)
- Content delivery networks (for images, e.g., ctfassets.net)

**System Requirements**:
- Python 3.9+
- Playwright browsers (Chromium)
- Sufficient disk space for images and output
- Network connectivity

### Integration Points

1. **Playwright Browser**: Primary interface for page loading and interaction
2. **File System**: Output directory structure for markdown and images
3. **Configuration Files**: YAML-based site-specific configurations
4. **State Files**: JSON-based crawl state persistence

---

## Constitution Check

### Adherence to Core Principles

✅ **Playwright-Based**: All crawling uses Playwright (Constitution 1.1)  
✅ **Metric Units**: All measurements converted to metric (Constitution 3.2)  
✅ **No Guessing**: Missing values use `None`, never placeholders (Constitution 3.3)  
✅ **Rate Limiting**: Minimum 2 seconds between requests (Constitution 1.2)  
✅ **Respectful Crawling**: Proper user-agent, robots.txt respect (Constitution 1.2)  
✅ **Multi-Page Merging**: Data from multiple pages merged correctly (Constitution 2.2)  
✅ **One Markdown Per Bike/Year**: Output structure follows specification (Constitution 5.1)  
✅ **Image Organization**: Images organized by manufacturer/model/year (Constitution 4.1)  
✅ **Error Handling**: Graceful degradation, no crashes (Constitution 8.1)  

### Gates

- ✅ **GATE 1**: All code in Python (Constitution 6.1)
- ✅ **GATE 2**: Type hints on all functions (Constitution 6.1)
- ✅ **GATE 3**: Comprehensive logging (Constitution 6.1)
- ✅ **GATE 4**: Metric unit conversion (Constitution 3.2)
- ✅ **GATE 5**: Schema validation (Constitution 3.1)
- ✅ **GATE 6**: State persistence (Constitution 6.2)

---

## Implementation Phases

### Phase 0: Foundation & Setup

**Goal**: Establish project structure, dependencies, and core utilities.

**Tasks**:
1. **Project Structure Setup**
   - Create directory structure (`src/`, `config/`, `output/`, `images/`, `state/`, `logs/`, `tests/`)
   - Set up `__init__.py` files for Python packages
   - Create `.gitignore` for output directories and state files

2. **Dependencies Installation**
   - Create `requirements.txt` with all dependencies
   - Set up `requirements-dev.txt` for development tools
   - Install Playwright browsers

3. **Core Utilities**
   - Implement `src/utils/units.py` - Unit conversion functions (hp→kW, lb-ft→Nm, etc.)
   - Implement `src/utils/schema.py` - Schema validation using Pydantic
   - Implement `src/utils/logging.py` - Structured logging configuration
   - Implement `src/utils/cookie_handler.py` - Cookie consent and UI interaction (already exists)

4. **Configuration System**
   - Create `config/config.yaml` template
   - Implement configuration loader
   - Support site-specific configurations

5. **Testing Infrastructure**
   - Set up pytest configuration
   - Create test fixtures for mock pages
   - Create sample HTML for testing

**Deliverables**:
- ✅ Project structure
- ✅ Working unit conversion functions
- ✅ Schema validation framework
- ✅ Configuration system
- ✅ Basic test suite

**Estimated Time**: 2-3 days

---

### Phase 1: Page Discovery & Classification

**Goal**: Implement comprehensive page discovery and bike page classification.

**Tasks**:
1. **Page Discovery Engine** (`src/crawler/discovery.py`)
   - Implement `PageDiscoveryEngine` class
   - URL normalization and internal URL detection
   - Recursive link following with depth control
   - Visited URL registry (in-memory and persistent)
   - Rate limiting with asyncio semaphore
   - State save/load functionality
   - Robots.txt parsing and respect
   - Sitemap.xml parsing
   - Search-based discovery (find search button, perform searches)
   - Link-following from key pages (heritage, etc.)

2. **Bike Page Classifier** (`src/crawler/classifier.py`)
   - Implement `BikePageClassifier` class
   - URL pattern matching (e.g., `/bikes/{model}/{year}/`)
   - Content analysis (spec tables, model names, year indicators)
   - HTML structure analysis
   - Keyword detection
   - Page type classification (main, specs, gallery, features, other)
   - Model/year/variant extraction with fallback inference
   - Related page grouping

3. **UI Interaction Handler** (`src/utils/cookie_handler.py` - extend existing)
   - Cookie consent handling (already implemented)
   - Modal dismissal
   - Dropdown navigation
   - Search interaction

4. **Integration & Testing**
   - Test discovery on sample site
   - Test classification accuracy
   - Test state persistence
   - Test rate limiting

**Deliverables**:
- ✅ `PageDiscoveryEngine` class
- ✅ `BikePageClassifier` class
- ✅ Comprehensive page discovery (sitemap + dropdown + search + link-following)
- ✅ Page classification working
- ✅ State management functional

**Estimated Time**: 3-4 days

---

### Phase 2: Data Extraction

**Goal**: Extract all bike data (specs, features, images, descriptions) from pages.

**Tasks**:
1. **Data Extractor** (`src/extractors/data_extractor.py`)
   - Implement `DataExtractor` class
   - Specification table extraction (multiple strategies)
   - Feature list extraction
   - Description extraction
   - Color option extraction
   - Pricing extraction
   - Fallback strategies for different page layouts
   - CSS selector-based extraction
   - XPath queries for structured data
   - Text pattern matching (regex for specs)

2. **Image Extractor** (`src/extractors/image_extractor.py`)
   - Implement `ImageExtractor` class
   - Find all `<img>` tags (src and srcset)
   - Detect background images in CSS
   - Handle lazy-loaded images (wait for load)
   - Extract high-resolution URLs from thumbnails
   - Filter relevant images (exclude logos, icons)
   - Image metadata extraction (alt text, captions)
   - Gallery/carousel detection

3. **Extraction Strategies**
   - Primary extraction (site-specific selectors)
   - Fallback extraction (generic patterns)
   - Text-based extraction (regex patterns)
   - Multiple attempts per data point

4. **Testing**
   - Test extraction on various page layouts
   - Test image extraction and filtering
   - Test fallback strategies

**Deliverables**:
- ✅ `DataExtractor` class
- ✅ `ImageExtractor` class
- ✅ Multiple extraction strategies
- ✅ Image filtering working
- ✅ Extraction tests passing

**Estimated Time**: 4-5 days

---

### Phase 3: Data Processing & Normalization

**Goal**: Normalize extracted data into unified schema with metric units.

**Tasks**:
1. **Data Normalizer** (`src/processors/normalizer.py`)
   - Implement `DataNormalizer` class
   - Unit detection and parsing from text
   - Unit conversion (all to metric)
   - Field name mapping (variations to schema fields)
   - Type validation (int vs float)
   - Missing field handling (use None)
   - Precision preservation
   - Schema validation using Pydantic

2. **Unit Conversion** (`src/utils/units.py` - extend)
   - Power: hp → kW
   - Torque: lb-ft → Nm
   - Length: inches/feet → mm
   - Weight: lbs → kg
   - Speed: mph → km/h
   - Volume: gallons → liters
   - Fuel consumption: mpg → L/100km
   - Handle ranges and approximate values
   - Handle ambiguous units

3. **Schema Definition** (`config/schema.json` or Pydantic models)
   - Define complete schema structure
   - Required vs optional fields
   - Type definitions
   - Validation rules

4. **Data Merger** (`src/processors/merger.py`)
   - Implement `DataMerger` class
   - Group pages by (manufacturer, model, year, variant)
   - Merge specifications from multiple pages
   - Conflict resolution (priority: specs > main > gallery)
   - Feature list combination and deduplication
   - Source URL aggregation
   - Handle missing vs None values

5. **Testing**
   - Test unit conversions (all cases)
   - Test schema validation
   - Test data merging and conflict resolution
   - Test edge cases (ranges, ambiguous units)

**Deliverables**:
- ✅ `DataNormalizer` class
- ✅ Complete unit conversion functions
- ✅ Schema validation working
- ✅ `DataMerger` class
- ✅ All data in metric units
- ✅ Multi-page merging functional

**Estimated Time**: 4-5 days

---

### Phase 4: Image Download & Organization

**Goal**: Download images with semantic naming and organize in folder structure.

**Tasks**:
1. **Image Downloader** (`src/downloaders/image_downloader.py`)
   - Implement `ImageDownloader` class
   - Async image downloading with aiohttp
   - SHA-256 hash calculation for deduplication
   - Global hash registry (across all bikes)
   - Semantic filename generation
   - Image type detection (main, gallery, detail, specs, feature)
   - Alt text sanitization for filenames
   - Folder structure creation (`images/{manufacturer}/{model}/{year}/`)
   - File size limits and validation
   - Error handling (skip corrupted images)

2. **Image Processing**
   - Format detection (jpg, png, webp)
   - Dimension validation (exclude small icons)
   - Duplicate detection and skipping
   - Progress tracking

3. **Testing**
   - Test image download
   - Test deduplication
   - Test filename generation
   - Test folder structure

**Deliverables**:
- ✅ `ImageDownloader` class
- ✅ Semantic filename generation
- ✅ Image deduplication working
- ✅ Proper folder organization
- ✅ Download tests passing

**Estimated Time**: 2-3 days

---

### Phase 5: Output Generation

**Goal**: Generate markdown files and metadata for each bike/year.

**Tasks**:
1. **Markdown Writer** (`src/writers/markdown_writer.py`)
   - Implement `MarkdownWriter` class
   - Format specifications section
   - Format features section
   - Format images with relative paths
   - Handle missing/optional fields gracefully
   - Filename sanitization
   - Relative path calculation (`os.path.relpath`)

2. **Metadata Writer** (`src/writers/metadata_writer.py`)
   - Implement `MetadataWriter` class
   - Save normalized JSON data
   - Include extraction metadata (timestamps, source URLs)
   - Store image metadata (URLs, local paths, hashes)
   - Schema version tracking

3. **Index Generation** (optional enhancement)
   - Create index markdown file listing all bikes
   - Generate summary statistics
   - Create sitemap of generated files

4. **Testing**
   - Test markdown generation
   - Test relative path calculation
   - Test metadata file structure

**Deliverables**:
- ✅ `MarkdownWriter` class
- ✅ `MetadataWriter` class
- ✅ One markdown file per bike/year
- ✅ Proper image linking
- ✅ Metadata files generated

**Estimated Time**: 2-3 days

---

### Phase 6: Integration & Main Entry Point

**Goal**: Integrate all components into working crawler system.

**Tasks**:
1. **Main Entry Point** (`src/main.py`)
   - Command-line argument parsing
   - Configuration loading
   - Component initialization
   - Orchestrate full crawl workflow
   - Progress reporting
   - Error handling and recovery
   - Summary statistics

2. **Workflow Integration**
   - Initialize Playwright
   - Handle cookie consent
   - Run all discovery methods
   - Classify pages
   - Extract data from bike pages
   - Normalize data
   - Merge multi-page data
   - Download images
   - Generate markdown and metadata
   - Post-crawl search
   - Final state save

3. **Error Handling**
   - Network error retries (exponential backoff)
   - Parse error handling (log and continue)
   - Partial data acceptance
   - Checkpoint system (save after each bike)

4. **Logging & Monitoring**
   - Progress tracking
   - Statistics (pages crawled, bikes extracted, images downloaded)
   - Error reporting
   - Performance metrics

5. **Testing**
   - End-to-end test on sample site
   - Test error recovery
   - Test state resumption
   - Test all discovery methods

**Deliverables**:
- ✅ `main.py` entry point
- ✅ Full workflow integrated
- ✅ Error handling complete
- ✅ Logging and monitoring
- ✅ End-to-end tests passing

**Estimated Time**: 3-4 days

---

### Phase 7: Enhancements & Polish

**Goal**: Add fallback extraction, deduplication improvements, retry logic, and OEM-specific configurations.

**Tasks**:
1. **Fallback Extraction Strategies**
   - Multiple CSS selector attempts per field
   - Text-based extraction as fallback
   - Pattern matching for common formats
   - Site-specific fallback configurations

2. **Enhanced Deduplication**
   - Image hash-based deduplication (already implemented)
   - URL-based deduplication
   - Content-based page deduplication
   - Cross-bike image sharing detection

3. **Retry Logic**
   - Network retries with exponential backoff (max 3 attempts)
   - Parse retry with different strategies
   - State recovery and resumption
   - Failed URL retry queue

4. **OEM-Specific Configurations**
   - Site-specific selector configurations
   - Custom field mappings per OEM
   - URL pattern configurations
   - Image container selectors
   - Exclusion rules

5. **Performance Optimization**
   - Concurrent image downloads (with limits)
   - Batch processing optimizations
   - Memory management improvements
   - Caching strategies

6. **Documentation**
   - README with usage examples
   - Configuration guide
   - Troubleshooting guide
   - API documentation

7. **Testing**
   - Test fallback strategies
   - Test retry logic
   - Test OEM configurations
   - Performance tests

**Deliverables**:
- ✅ Fallback extraction working
- ✅ Enhanced deduplication
- ✅ Robust retry logic
- ✅ OEM configuration system
- ✅ Performance optimizations
- ✅ Complete documentation
- ✅ Comprehensive test suite

**Estimated Time**: 4-5 days

---

## Technical Decisions

### 1. Async Architecture
**Decision**: Use async/await throughout for I/O operations.  
**Rationale**: Better performance for concurrent operations, efficient resource usage.  
**Trade-offs**: More complex code, but necessary for scalability.

### 2. Pydantic for Schema Validation
**Decision**: Use Pydantic models for data validation.  
**Rationale**: Type-safe, automatic validation, good error messages.  
**Trade-offs**: Additional dependency, but provides significant value.

### 3. Multiple Discovery Methods
**Decision**: Combine sitemap, dropdown, search, and link-following.  
**Rationale**: Ensures comprehensive coverage, handles different site structures.  
**Trade-offs**: More complex, but necessary for completeness.

### 4. Global Image Deduplication
**Decision**: Maintain global hash registry across all bikes.  
**Rationale**: Prevents downloading same image multiple times, saves storage.  
**Trade-offs**: Requires memory for hash storage, but manageable.

### 5. State Persistence
**Decision**: Save state after each bike, support resumption.  
**Rationale**: Allows recovery from interruptions, long-running crawls.  
**Trade-offs**: Slight performance overhead, but essential for reliability.

---

## Risk Assessment

### High Risk
- **Site Structure Changes**: Target sites may change HTML structure.  
  **Mitigation**: Multiple extraction strategies, fallback patterns, configurable selectors.

- **Rate Limiting/Blocking**: Sites may block aggressive crawlers.  
  **Mitigation**: Respectful rate limiting, proper user-agent, robots.txt compliance.

### Medium Risk
- **Large Site Scale**: Sites with 1000+ pages may take significant time.  
  **Mitigation**: State persistence, resumable crawls, progress reporting.

- **Image Storage**: Large number of images may require significant disk space.  
  **Mitigation**: Deduplication, size limits, organized folder structure.

### Low Risk
- **Dependency Updates**: Playwright or other dependencies may change APIs.  
  **Mitigation**: Pin versions, test updates, maintain compatibility layer.

---

## Success Criteria

### Functional Requirements
- ✅ All internal pages discovered (sitemap + dropdown + search + links)
- ✅ All bike pages classified correctly
- ✅ All specifications extracted and normalized to metric
- ✅ All images downloaded with semantic names
- ✅ One markdown file per bike/year
- ✅ Multi-page data merged correctly
- ✅ No guessed values (missing data = None)

### Non-Functional Requirements
- ✅ Respectful crawling (rate limiting, proper headers)
- ✅ Error handling (graceful degradation, no crashes)
- ✅ State persistence (resumable crawls)
- ✅ Comprehensive logging
- ✅ Performance (reasonable crawl time)

### Quality Metrics
- Extraction success rate > 90%
- Image download success rate > 95%
- Zero crashes on valid sites
- All data in metric units
- Schema validation passes for all bikes

---

## Testing Strategy

### Unit Tests
- Unit conversion functions
- Schema validation
- URL normalization
- Filename sanitization
- Field name mapping

### Integration Tests
- End-to-end extraction from sample pages
- Multi-page data merging
- Image download and organization
- Markdown generation
- State save/load

### Test Data
- Mock HTML pages with various structures
- Sample specification tables
- Test images for download functionality
- Sample sitemap.xml

---

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Foundation | 2-3 days | None |
| Phase 1: Discovery & Classification | 3-4 days | Phase 0 |
| Phase 2: Data Extraction | 4-5 days | Phase 1 |
| Phase 3: Processing & Normalization | 4-5 days | Phase 2 |
| Phase 4: Image Download | 2-3 days | Phase 2 |
| Phase 5: Output Generation | 2-3 days | Phase 3, 4 |
| Phase 6: Integration | 3-4 days | Phase 5 |
| Phase 7: Enhancements | 4-5 days | Phase 6 |
| **Total** | **25-32 days** | |

---

## Next Steps

1. **Review and Approve Plan**: Review this plan for completeness and accuracy.
2. **Set Up Development Environment**: Install dependencies, set up project structure.
3. **Begin Phase 0**: Start with foundation and setup tasks.
4. **Iterate**: Follow phases sequentially, with testing at each phase.

---

**Version**: 1.0  
**Created**: 2024  
**Status**: Ready for Implementation


