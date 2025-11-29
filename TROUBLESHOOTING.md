# Troubleshooting Guide

## Issue: No URLs Discovered (0 URLs found)

### Symptoms
- All discovery methods return 0 URLs
- Logs show:
  - "Sitemap discovery: 0 URLs"
  - "Dropdown discovery: 0 URLs"
  - "Search discovery: 0 URLs"
  - "Link following: 0 URLs"

### Root Causes

#### 1. Bot Detection / Access Denied (Most Common)

**Symptoms:**
- Page title: "Access Denied"
- HTTP status: 403 Forbidden
- Error message: "You don't have permission to access..."

**Why it happens:**
- Cloudflare or similar bot protection
- IP-based blocking
- Server-side detection of automated browsers

**Solutions:**

1. **Check if site is accessible manually:**
   ```bash
   curl -I https://www.ducati.com
   ```
   If this returns 403, the site is blocking your IP.

2. **Use VPN or different IP:**
   - Connect to a VPN
   - Use a different server/location
   - Try from a residential IP

3. **Increase delays:**
   ```bash
   python run_crawler.py ... --rate-limit 5.0
   ```

4. **Use proxy (advanced):**
   Modify `src/crawler/discovery.py` to add proxy configuration:
   ```python
   self.browser = await self.playwright.chromium.launch(
       headless=headless,
       proxy={"server": "http://proxy-server:port"}
   )
   ```

5. **Test with non-headless mode:**
   ```bash
   python run_crawler.py ... --no-headless
   ```
   (Requires X server - won't work on headless servers)

#### 2. Selectors Not Matching Page Structure

**Symptoms:**
- Page loads successfully (no 403)
- But dropdown/search selectors don't find elements
- "Dropdown not found" warnings

**Why it happens:**
- Website structure changed
- Site uses different navigation patterns
- JavaScript-heavy site that needs more time to load

**Solutions:**

1. **Inspect page structure:**
   ```bash
   python debug_page_structure.py
   ```
   This will show what selectors actually exist on the page.

2. **Update selectors in `src/crawler/discovery.py`:**
   - Check `_discover_from_dropdown()` method
   - Update selectors to match actual page structure
   - Add more fallback selectors

3. **Increase wait times:**
   - Add `await page.wait_for_timeout(3000)` after navigation
   - Wait for specific elements: `await page.wait_for_selector('.menu')`

#### 3. Sitemap Not Available

**Symptoms:**
- "Sitemap discovery: 0 URLs"
- No sitemap.xml found

**Why it happens:**
- Site doesn't have a sitemap
- Sitemap is at different location
- Sitemap requires authentication

**Solutions:**

1. **Check sitemap manually:**
   ```bash
   curl https://www.ducati.com/sitemap.xml
   ```

2. **Try alternative sitemap locations:**
   - `/sitemap_index.xml`
   - `/sitemaps/sitemap.xml`
   - `/robots.txt` (may list sitemap location)

3. **Rely on other discovery methods:**
   - The crawler uses multiple strategies
   - If sitemap fails, dropdown/search/link-following should still work

## Issue: Browser Launch Fails

### Symptoms
- `TargetClosedError: BrowserType.launch: Target page, context or browser has been closed`
- "Missing X server or $DISPLAY"

### Solution

Run in headless mode (default):
```bash
python run_crawler.py ...  # headless=True by default
```

Or if you need GUI, use xvfb:
```bash
xvfb-run python run_crawler.py ... --no-headless
```

## Issue: Event Loop Closed Warning

### Symptoms
- `RuntimeError: Event loop is closed` (harmless warning)
- Appears at end of execution

### Solution

This is a harmless warning from asyncio cleanup. It's been suppressed in the code. If it persists, it doesn't affect functionality.

## Debugging Tips

### 1. Enable Debug Logging
```bash
python run_crawler.py ... --log-level DEBUG
```

### 2. Use Debug Script
```bash
python debug_page_structure.py
```
This will:
- Take a screenshot
- Show all found selectors
- Display page structure
- List all links

### 3. Test Individual Components
```python
# Test discovery only
from src.crawler.discovery import PageDiscoveryEngine
engine = PageDiscoveryEngine("https://www.ducati.com")
await engine.initialize_browser()
async for url in engine.discover_all_pages():
    print(url)
```

### 4. Check Network Activity
Enable network logging in Playwright:
```python
self.context.on("request", lambda req: logger.debug(f"Request: {req.url}"))
self.context.on("response", lambda resp: logger.debug(f"Response: {resp.status} {resp.url}"))
```

## Getting Help

If you're still stuck:
1. Check the logs with `--log-level DEBUG`
2. Run `debug_page_structure.py` to inspect the page
3. Verify the site is accessible manually
4. Check if the site structure has changed
5. Review the error messages for specific clues


