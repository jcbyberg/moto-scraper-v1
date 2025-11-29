# Crawler Changelog

## Latest Updates

### Search-Based Discovery
- Added `discover_pages_via_search()` method that:
  - Finds and clicks the site search button
  - Performs searches for bike-related terms (bike, motorcycle, model, heritage, racing, etc.)
  - Extracts URLs from search results
  - Discovers pages that might not be in dropdowns or sitemaps

### Link Following Discovery
- Added `discover_pages_via_link_following()` method that:
  - Recursively follows links from key pages (like heritage pages)
  - Discovers pages up to a configurable depth (default: 2 levels)
  - Handles different URL patterns and locales

### Post-Crawl Search
- Added `post_crawl_search()` method that:
  - Checks specific URLs mentioned by user (e.g., `/ca/en/home`, `/ww/en/heritage/bikes/`)
  - Tests pattern-based URLs across different locales (ca/en, ww/en, us/en, etc.)
  - Extracts additional links from discovered pages
  - Ensures no pages are missed

### Improved URL Handling
- Enhanced `is_internal_url()` to handle:
  - Different subdomains (www.ducati.com, ducati.com)
  - Different locale patterns (ca/en, ww/en, etc.)
  - Relative URLs

### Multi-Method Discovery
The crawler now uses multiple discovery methods:
1. **Sitemap** - Checks sitemap.xml for URLs
2. **Dropdown Navigation** - Clicks MODELS dropdown and extracts links
3. **Search-Based** - Uses site search to find pages
4. **Link Following** - Recursively follows links from key pages
5. **Post-Crawl Search** - Final pass to catch any missed pages

## Usage

```bash
python scripts/full_site_crawler.py https://www.ducati.com/ca/en/home --output-dir /mnt/seagate4tb/moto-scraper-v1
```

The crawler will:
1. Navigate to the base URL
2. Accept cookies
3. Check sitemap
4. Discover pages via dropdown
5. Discover pages via search
6. Follow links from heritage pages
7. Crawl all discovered pages
8. Run post-crawl search for missed pages
9. Crawl any additional pages found

## Output

All discovered pages are crawled and saved as markdown files in the output directory, with images saved to the images subdirectory.


