# Using Cursor IDE Browser for Scraping

## Current Status

✅ **Browser is open** in Cursor IDE  
✅ **Page loaded**: https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally  
✅ **Page title**: "New Multistrada V4 Rally - Designed to take you anywhere"  
✅ **Cookies accepted**

## How It Works

The Cursor IDE browser uses MCP (Model Context Protocol) tools that allow me to:
- Navigate to URLs
- Take snapshots of pages
- Click buttons and links
- Extract content
- Take screenshots

## Available Browser Actions

### 1. Navigation
```python
# Navigate to any URL
browser_navigate(url="https://www.ducati.com/ww/en/bikes/...")
```

### 2. Taking Snapshots
```python
# Get current page structure
browser_snapshot()
```

### 3. Clicking Elements
```python
# Click any button, link, or interactive element
browser_click(element="Button name", ref="ref-xxx")
```

### 4. Extracting Content
The snapshot files contain the full page structure in YAML format, which can be parsed to extract:
- Text content
- Images
- Links
- Form elements
- Specifications

## Integration with Your Scraper

Your existing extraction code (`src/extractors/`) can work with:

1. **Snapshot Files**: Parse the YAML snapshot files to extract data
2. **Direct DOM Access**: Use browser tools to query specific elements
3. **Hybrid Approach**: Use Cursor browser for navigation/interaction, then extract via Playwright

## Example Workflow

1. **Navigate to page** → `browser_navigate()`
2. **Accept cookies** → `browser_click()` on accept button
3. **Take snapshot** → `browser_snapshot()` to see page structure
4. **Click carousel arrows** → Navigate through images
5. **Expand accordions** → Reveal hidden content
6. **Extract data** → Parse snapshot or use extractors
7. **Save results** → Write to markdown/JSON files

## Next Steps

I can now:
- Click through carousel images to reveal all photos
- Expand accordion sections to show specifications
- Navigate to related pages (specs, gallery, etc.)
- Extract all content and images
- Save everything to your output directory

Would you like me to:
1. **Start extracting data** from the current page?
2. **Navigate to more bike pages**?
3. **Click through carousels** to get all images?
4. **Expand accordions** to reveal specifications?

## Snapshot Files

All snapshots are saved to:
```
C:\Users\jcbyb\.cursor\browser-logs\snapshot-*.log
```

These files contain the full page structure and can be parsed programmatically.

## Running the Scraper

To use the Cursor browser scraper:

```bash
# Basic usage
python scrape_with_cursor_browser.py

# With specific URL
python scrape_with_cursor_browser.py https://www.ducati.com/ww/en/bikes/panigale/panigale-v4

# Extract from existing snapshot
python scrape_with_cursor_browser.py --snapshot "C:\Users\jcbyb\.cursor\browser-logs\snapshot-*.log"
```

The browser is ready to use! Just tell me what you'd like to scrape next.


