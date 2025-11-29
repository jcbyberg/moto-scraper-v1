# Specification Clarifications

This document clarifies ambiguities, edge cases, and implementation details that require explicit decisions.

---

## 1. Page Discovery & URL Handling

### 1.1 What Constitutes "Internal Pages"?

**Clarification**: 
- **Same domain**: Pages on the exact same domain (e.g., `example-oem.com`)
- **Subdomains**: Include subdomains by default (e.g., `www.example-oem.com`, `shop.example-oem.com`) unless explicitly excluded in config
- **Exclude**: External links, mailto:, tel:, javascript:, data: URIs
- **Query parameters**: Treat URLs with different query parameters as different pages (e.g., `?year=2024` vs `?year=2023`)
- **Fragments**: Normalize URLs by removing fragments (`#section`) - treat as same page
- **Trailing slashes**: Normalize by removing trailing slashes - `example.com/page/` and `example.com/page` are the same

**Implementation**:
```python
def normalize_url(url: str) -> str:
    """Normalize URL for comparison: remove fragments, trailing slashes."""
    parsed = urlparse(url)
    # Remove fragment
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    # Remove trailing slash (except root)
    if normalized.endswith('/') and len(parsed.path) > 1:
        normalized = normalized[:-1]
    return normalized.lower()
```

### 1.2 URL Discovery Depth

**Clarification**:
- **Default**: Unlimited depth (follow all internal links recursively)
- **Configurable**: `max_depth` parameter can limit depth if needed
- **Stop conditions**: Stop following links when:
  - External domain reached
  - Max depth reached (if set)
  - robots.txt disallows
  - URL pattern explicitly excluded in config

---

## 2. Bike Page Classification

### 2.1 Handling Pages with Multiple Bikes

**Clarification**:
- **Listing pages**: Pages showing multiple bikes (e.g., model lineup) are NOT bike pages
- **Comparison pages**: Pages comparing multiple bikes are NOT bike pages (but may contain useful data)
- **Single bike focus**: A page is a "bike page" only if it focuses on a single model/year combination
- **Extraction from listings**: Do NOT extract individual bike data from listing pages; wait to find dedicated pages

**Decision**: Skip listing/comparison pages during initial classification, but may revisit for cross-referencing.

### 2.2 Model/Year Extraction Failures

**Clarification**:
- **Required fields**: If manufacturer, model, OR year cannot be extracted, the page is NOT classified as a bike page
- **Partial extraction**: If model is found but year is not, attempt to infer year from:
  1. URL pattern (e.g., `/motorcycles/model-2024/`)
  2. Page metadata (e.g., `<meta name="year">`)
  3. Content analysis (e.g., "2024 Model" in text)
- **If inference fails**: Mark page as "potential bike page" but do NOT process until model/year can be determined
- **Multiple years on page**: If page shows multiple years (e.g., "Available in 2023, 2024, 2025"), create separate entries for each year if sufficient data exists

**Implementation**:
```python
def extract_model_info(self, url: str, content: str) -> dict[str, Any] | None:
    """Extract model/year with fallback inference."""
    # Primary extraction from content
    model = self._extract_model(content)
    year = self._extract_year(content)
    
    # Fallback: infer from URL
    if not year:
        year = self._infer_year_from_url(url)
    
    # Fallback: infer from metadata
    if not year:
        year = self._infer_year_from_metadata(content)
    
    # Must have both model and year
    if not model or not year:
        return None
    
    return {"model": model, "year": int(year), "variant": self._extract_variant(content)}
```

---

## 3. Data Extraction & Normalization

### 3.1 Handling Missing or Inapplicable Fields

**Clarification**:
- **Electric bikes**: Fields like `displacement_cc`, `bore_mm`, `stroke_mm` are `None` for electric bikes
- **Missing specs**: If a specification category is completely missing (e.g., no engine specs at all), the entire category dict can be empty `{}` or omitted
- **Partial specs**: If some fields in a category exist but others don't, include the category with available fields and `None` for missing ones
- **Never guess**: If unsure about a value, use `None` - never use placeholder values like "N/A", "Unknown", or "TBD"

**Example**:
```python
# Electric bike - no displacement
"engine": {
    "type": "Electric",
    "displacement_cc": None,  # Not applicable
    "max_power_kw": 50.0,
    # ... other fields
}

# Missing entire category
"performance": {}  # or omit entirely if completely missing
```

### 3.2 Unit Detection and Conversion Edge Cases

**Clarification**:
- **Ambiguous units**: If unit is ambiguous (e.g., "100" without unit), preserve original text in a `raw_value` field and set normalized value to `None`
- **Range values**: If spec shows a range (e.g., "150-200 kg"), store as string: `"150-200 kg"` and convert to metric range: `"150-200 kg"` (already metric) or `"330-440 lbs"` → `"150-200 kg"`
- **Approximate values**: Preserve "~", "approx", "about" indicators in original text, but still convert numeric value
- **Multiple units in text**: If text contains multiple values with different units, extract each separately

**Example**:
```python
# Input: "Weight: ~450 lbs (204 kg)"
# Output: 
{
    "wet_weight_kg": 204.0,  # Use metric value if provided
    "raw_text": "~450 lbs (204 kg)"  # Preserve original
}

# Input: "150-200 kg"
# Output:
{
    "wet_weight_kg": None,  # Can't represent range as single float
    "wet_weight_range_kg": "150-200",  # Store range separately
    "raw_text": "150-200 kg"
}
```

### 3.3 Schema Field Mapping Variations

**Clarification**:
- **Field name variations**: Maintain a mapping dictionary for common field name variations:
  ```python
  FIELD_MAPPINGS = {
      "engine_size": "displacement_cc",
      "engine_capacity": "displacement_cc",
      "cc": "displacement_cc",
      "horsepower": "max_power_kw",  # Will convert hp to kW
      "hp": "max_power_kw",
      "torque": "max_torque_nm",
      # ... etc
  }
  ```
- **Case insensitivity**: Field matching should be case-insensitive
- **Partial matches**: If exact match fails, attempt fuzzy matching for common variations
- **Unmapped fields**: If a field cannot be mapped to schema, store in `extra_fields` dict in metadata

---

## 4. Multi-Page Data Merging

### 4.1 Determining Page Relationships

**Clarification**:
- **Grouping key**: Pages are grouped by `(manufacturer, model, year, variant)` tuple
- **Variant handling**: If variant is `None`, group with other pages for same model/year
- **URL patterns**: Use URL structure to infer relationships:
  - `/motorcycles/{model}/{year}/` → main page
  - `/motorcycles/{model}/{year}/specifications` → specs page
  - `/motorcycles/{model}/{year}/gallery` → gallery page
- **Content analysis**: If URL patterns don't reveal relationship, analyze page content for model/year mentions
- **Confidence scoring**: Assign confidence scores to page relationships; only merge if confidence > threshold

**Implementation**:
```python
def group_related_pages(self, pages: list[dict]) -> dict[str, list[dict]]:
    """Group pages by (manufacturer, model, year, variant)."""
    groups = {}
    for page in pages:
        key = (
            page['manufacturer'],
            page['model'],
            page['year'],
            page.get('variant') or 'base'  # Normalize None to 'base'
        )
        if key not in groups:
            groups[key] = []
        groups[key].append(page)
    return groups
```

### 4.2 Conflict Resolution Details

**Clarification**:
- **Priority order**: specs page > main page > features page > gallery page > other
- **Numeric conflicts**: If same numeric field has different values:
  - Prefer value from higher-priority page
  - If values are very close (< 1% difference), use average
  - If values differ significantly (> 10%), log warning and use higher-priority value
- **Text conflicts**: If same text field differs:
  - Combine unique values (for lists like features)
  - For single-value fields, prefer longer/more detailed text
  - Preserve all versions in metadata for manual review
- **Missing vs. None**: If one page has `None` and another has a value, use the value (not None)

**Example**:
```python
# Page 1 (specs): max_power_kw = 50.0
# Page 2 (main): max_power_kw = 49.8
# Result: 50.0 (from specs page, higher priority)

# Page 1 (specs): max_power_kw = 50.0
# Page 2 (main): max_power_kw = 45.0  # 10% difference
# Result: 50.0 (from specs page) + log warning
```

---

## 5. Image Handling

### 5.1 Image Relevance Filtering

**Clarification**:
- **Size threshold**: Images smaller than 200x200 pixels are likely icons/logos - exclude
- **Filename patterns**: Exclude images with filenames containing:
  - `logo`, `icon`, `button`, `badge`, `social`, `facebook`, `twitter`
- **Alt text analysis**: Exclude if alt text contains:
  - "logo", "icon", "button", "menu", "navigation"
- **Context analysis**: If image is in header/footer/nav areas, likely not bike image
- **Gallery detection**: Images in elements with classes like "gallery", "carousel", "slider" are likely relevant
- **Manual override**: Allow config to specify CSS selectors for image containers to include/exclude

**Implementation**:
```python
def filter_relevant_images(self, images: list[dict], model: str) -> list[dict]:
    """Filter out non-bike images."""
    filtered = []
    exclude_keywords = ['logo', 'icon', 'button', 'badge', 'social']
    
    for img in images:
        # Check size
        if img['width'] < 200 or img['height'] < 200:
            continue
        
        # Check filename
        filename_lower = img['url'].lower()
        if any(kw in filename_lower for kw in exclude_keywords):
            continue
        
        # Check alt text
        alt_lower = (img.get('alt') or '').lower()
        if any(kw in alt_lower for kw in exclude_keywords):
            continue
        
        filtered.append(img)
    
    return filtered
```

### 5.2 Semantic Filename Generation

**Clarification**:
- **Image type detection**:
  - `main`: Hero image, primary product image, first image in gallery
  - `gallery`: Images in gallery/carousel (not the first one)
  - `detail`: Close-up shots, detail views
  - `specs`: Images showing specifications, diagrams
  - `feature`: Images highlighting specific features
- **Alt text sanitization**: 
  - Remove special characters, convert to lowercase
  - Replace spaces with underscores
  - Limit to 50 characters
  - Remove common words: "image", "photo", "picture"
- **Fallback naming**: If no alt text and type unknown, use: `{manufacturer}_{model}_{year}_{index:03d}.{ext}`
- **Extension preservation**: Preserve original file extension (jpg, jpeg, png, webp)

**Example**:
```python
# Alt: "2024 Sport Bike in Red"
# Type: "main"
# Result: "yamaha_r1_2024_main_red.jpg"

# No alt, index 5
# Result: "yamaha_r1_2024_005.jpg"
```

### 5.3 Image Deduplication Scope

**Clarification**:
- **Global deduplication**: Maintain a global hash registry across all bikes
- **Same image, different bikes**: If same image appears for multiple bikes, download once and reference from multiple locations
- **Hash algorithm**: Use SHA-256 hash of image content (not URL or filename)
- **Storage strategy**: Store image once in a shared location, create symlinks or references in bike-specific folders
- **Alternative**: If symlinks not desired, copy image to each bike folder but track to avoid re-downloading

**Decision**: Use global hash registry, download once, create copies in each bike's folder (simpler than symlinks, works across filesystems).

---

## 6. Output Format & File Structure

### 6.1 Relative Path Calculation for Images

**Clarification**:
- **Markdown location**: `output/{manufacturer}/{model}/{manufacturer}_{model}_{year}.md`
- **Image location**: `images/{manufacturer}/{model}/{year}/{filename}.jpg`
- **Relative path calculation**: From markdown file to image:
  ```
  Markdown: output/yamaha/r1/yamaha_r1_2024.md
  Image:    images/yamaha/r1/2024/yamaha_r1_2024_main_001.jpg
  Relative: ../../images/yamaha/r1/2024/yamaha_r1_2024_main_001.jpg
  ```
- **Path calculation**: Use `os.path.relpath()` to compute relative path dynamically

**Implementation**:
```python
def format_images(self, image_paths: list[str], markdown_path: str) -> str:
    """Format images with relative paths."""
    markdown_dir = os.path.dirname(markdown_path)
    image_section = []
    
    for img_path in image_paths:
        rel_path = os.path.relpath(img_path, markdown_dir)
        filename = os.path.basename(img_path)
        image_section.append(f"![{filename}]({rel_path})")
    
    return "\n".join(image_section)
```

### 6.2 Filename Sanitization

**Clarification**:
- **Special characters**: Replace with underscores: `/ \ : * ? " < > |`
- **Spaces**: Replace with underscores
- **Multiple underscores**: Collapse consecutive underscores to single
- **Length limit**: Truncate to 200 characters (filesystem limit consideration)
- **Case handling**: Preserve case but ensure no conflicts (some filesystems are case-insensitive)
- **Unicode**: Normalize unicode characters (e.g., é → e)

**Implementation**:
```python
def sanitize_filename(self, text: str) -> str:
    """Sanitize text for filename."""
    import unicodedata
    import re
    
    # Normalize unicode
    text = unicodedata.normalize('NFKD', text)
    
    # Remove special chars
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'_+', '_', text)  # Collapse underscores
    
    # Truncate
    text = text[:200]
    
    return text.strip('_')
```

### 6.3 Variant Handling in Output

**Clarification**:
- **Separate files**: Each variant gets its own markdown file if it has distinct specifications
- **File naming**: `{manufacturer}_{model}_{variant}_{year}.md` if variant exists
- **Base model**: If no variant, use `{manufacturer}_{model}_{year}.md`
- **Variant detection**: Variant is considered distinct if:
  - Different engine specs (displacement, power)
  - Different weight (significant difference > 5%)
  - Explicitly named variant (e.g., "R1M", "R1 Base")
- **Shared data**: If variants share most specs, still create separate files but note shared specifications

---

## 7. Error Handling & Edge Cases

### 7.1 Required Field Extraction Failures

**Clarification**:
- **Manufacturer missing**: Use value from config if provided, otherwise skip page
- **Model missing**: Cannot proceed - skip page, log error
- **Year missing**: Attempt inference (see 2.2), if fails - skip page, log error
- **All three missing**: Skip page entirely, do not create partial entry

**Decision**: Never create bike entries without manufacturer, model, AND year.

### 7.2 Partial Extraction Scenarios

**Clarification**:
- **No specifications found**: Create markdown with available data (description, features, images) and note "Specifications not available"
- **No images found**: Create markdown without images section
- **No description found**: Use empty string or "Description not available"
- **Only images found**: Still create entry with images, mark specs as unavailable

**Decision**: Create output files even with partial data, but clearly indicate what's missing.

### 7.3 Network & Timeout Handling

**Clarification**:
- **Page load timeout**: Default 30 seconds, configurable
- **Image download timeout**: Default 10 seconds per image
- **Retry strategy**: 
  - First retry: 2 seconds delay
  - Second retry: 5 seconds delay
  - Third retry: 10 seconds delay
  - After 3 failures: Skip and log
- **Concurrent limit**: Max 3 concurrent page loads, max 5 concurrent image downloads
- **Rate limiting**: Minimum 2 seconds between page requests to same domain

---

## 8. State Management & Resumption

### 8.1 Checkpoint Frequency

**Clarification**:
- **After each bike**: Save state after successfully processing each bike (extraction + download + markdown)
- **Periodic saves**: Also save state every 10 pages crawled (even if not bike pages)
- **State includes**:
  - Visited URLs set
  - Pending URLs queue
  - Successfully processed bikes (to avoid re-processing)
  - Failed URLs (to retry later)
  - Statistics (counts, timestamps)

### 8.2 Resume Behavior

**Clarification**:
- **Skip processed**: Do not re-extract bikes that were already successfully processed
- **Retry failures**: Re-attempt failed URLs from previous run
- **Continue discovery**: Resume URL discovery from pending queue
- **State validation**: Validate state file on load; if corrupted, start fresh with warning

---

## 9. Performance & Resource Management

### 9.1 Memory Management

**Clarification**:
- **Stream processing**: Process and write data immediately, don't accumulate all bikes in memory
- **Page content**: Release page content from memory after extraction
- **Image handling**: Download and write images immediately, don't buffer in memory
- **State size**: Limit visited URLs set size; if exceeds 100k URLs, consider using disk-based set

### 9.2 Disk Space Management

**Clarification**:
- **Image size limits**: Reject images larger than 10MB (configurable)
- **Disk space check**: Before starting, check available disk space; warn if < 1GB free
- **Cleanup**: Option to clean up intermediate files (raw HTML, temporary downloads)

---

## 10. Configuration & Extensibility

### 10.1 Site-Specific Configuration

**Clarification**:
- **Extraction selectors**: Allow site-specific CSS selectors in config
- **URL patterns**: Allow regex patterns for bike page detection
- **Field mappings**: Allow custom field name mappings per site
- **Image selectors**: Allow custom selectors for image containers

**Config Example**:
```yaml
site_specific:
  example_oem_com:
    bike_page_patterns:
      - "/motorcycles/.*/.*/"
    spec_table_selectors:
      - ".spec-table"
      - "#technical-specs table"
    image_containers:
      - ".product-gallery"
      - ".bike-images"
    exclude_selectors:
      - ".header img"
      - ".footer img"
```

### 10.2 Schema Extensions

**Clarification**:
- **Extra fields**: Store unmapped fields in `extra_fields` dict
- **Schema versioning**: Include schema version in output files
- **Backward compatibility**: When schema evolves, maintain ability to read old format

---

## Summary of Key Decisions

1. ✅ **URL Normalization**: Remove fragments, normalize trailing slashes, treat query params as different pages
2. ✅ **Bike Page Definition**: Must focus on single model/year; skip listing/comparison pages
3. ✅ **Required Fields**: Manufacturer, model, and year are mandatory; skip if any missing
4. ✅ **Missing Data**: Use `None` for missing fields, never guess or use placeholders
5. ✅ **Image Deduplication**: Global hash registry, download once, copy to each bike folder
6. ✅ **Relative Paths**: Calculate dynamically using `os.path.relpath()`
7. ✅ **Partial Data**: Create output files even with partial data, clearly mark missing sections
8. ✅ **State Management**: Save after each bike, resume by skipping processed bikes
9. ✅ **Memory Efficiency**: Stream processing, don't accumulate all data in memory
10. ✅ **Site-Specific Config**: Allow custom selectors and patterns per target site

---

**Version**: 1.0  
**Last Updated**: 2024  
**Status**: Active Clarifications


