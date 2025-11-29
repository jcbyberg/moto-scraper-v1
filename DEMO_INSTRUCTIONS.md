# Demo Instructions - Visible Browser Scraping

This guide shows you how to run the scraper with a visible browser so you can watch it work in real-time.

## Quick Start

### Option 1: Run with Default URL
```bash
python3 demo_scraper.py
```

This will:
- Show a menu of demo pages
- Let you choose which page to scrape
- Open a visible browser window
- Show the scraping process step-by-step

### Option 2: Run with Specific URL
```bash
python3 demo_scraper.py "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally"
```

### Option 3: Run with Different Demo Pages
```bash
# Hypermotard V2
python3 demo_scraper.py "https://www.ducati.com/ww/en/bikes/hypermotard/hypermotard-v2"

# Scrambler Category
python3 demo_scraper.py "https://www.ducati.com/ww/en/bikes/scrambler"

# Travel Story
python3 demo_scraper.py "https://www.ducati.com/ww/en/stories/travel/road-to-olympus-multistrada-v4-rally"

# Desmo250 MX
python3 demo_scraper.py "https://www.ducati.com/ww/en/bikes/offroad/desmo250-mx"
```

## What You'll See

When you run the demo, you'll see:

1. **Browser Window Opens** - A Chromium browser window will open
2. **Navigation** - The browser navigates to the target page
3. **Cookie Handling** - Automatically accepts cookies
4. **Content Extraction** - Extracts:
   - Specifications
   - Features
   - Descriptions
   - Content sections (headers, titles, text, tooltips)
   - Accordion content (if present)
5. **Image Extraction** - Extracts:
   - Regular images
   - Carousel images (navigates through carousels)
   - Accordion images (expands accordions)
   - Video poster images
   - Background images
   - Picture elements
6. **Console Output** - Shows progress in the terminal:
   - Number of specifications found
   - Number of features found
   - Number of images found
   - Content previews

## Features Demonstrated

### 1. Carousel Navigation
- The scraper will click arrow buttons to navigate through carousels
- You'll see it clicking "next" buttons multiple times
- All carousel images will be extracted

### 2. Accordion Expansion
- The scraper will find and click accordion triggers
- You'll see accordions expanding to reveal hidden content
- Content and images from accordions will be extracted

### 3. Tab Navigation (Insights Pages)
- On insights pages, the scraper will click through tabs
- You'll see it clicking "Design", "Technology", etc.
- Content from each tab will be extracted

### 4. Image Extraction
- The scraper extracts images from multiple sources:
  - Regular `<img>` tags
  - `<picture>` elements
  - Video poster images
  - Background images from `data-bg` attributes
  - Images in cards and sections

### 5. Content Extraction
- Extracts structured content:
  - Headers, titles, text
  - Tooltips and data-js-tip elements
  - Accordion content
  - Story content
  - Specifications from various formats

## Browser Behavior

The browser will:
- Stay open for 10 seconds after scraping completes (so you can inspect)
- Stay open for 30 seconds if there's an error (for debugging)
- Run in slow-motion mode (500ms delay between actions) so you can see what's happening

## Requirements

- Python 3.9+
- Playwright installed: `playwright install chromium`
- All dependencies from `requirements.txt`

## Troubleshooting

### Browser doesn't open
- Make sure you have a display/X server running
- On headless servers, use: `xvfb-run python3 demo_scraper.py`

### Access Denied errors
- The site may be blocking automated access
- Try using a proxy (see README.md for proxy configuration)
- The demo will show the error in the browser window

### Images not loading
- Some images are lazy-loaded and may take time
- The scraper waits for images to load
- Check the console output for image extraction status

## Example Output

```
🚀 DUCATI SCRAPER DEMO

📍 Navigating to https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally...
🍪 Handling cookies...

📝 Extracting content...
   ✓ Extracted 15 specifications
   ✓ Extracted 8 features
   ✓ Description length: 2345 chars
   ✓ Content sections: ['header', 'title', 'text', 'content', 'tooltips']

🖼️  Extracting images...
   ✓ Found 23 images

   Sample images:
   1. https://images.ctfassets.net/x7j9qwvpvr5s/.../desertX-hero-short-1600x1000.jpg...
   2. https://images.ctfassets.net/x7j9qwvpvr5s/.../DesertX-V2-dual-media-card-800x924-01.jpg...
   ...

📄 Content Preview:
-------------------------------------------------------------------------------
Designed to take you anywhere Multistrada V4 Rally is your definitive travel
companion, taking you on a journey to unexplored lands, with a focus on comfort
and versatility...
```

Enjoy watching the scraper in action! 🎬


