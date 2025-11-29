"""
Page Discovery Engine for motorcycle OEM web-crawler.

Implements comprehensive page discovery using multiple strategies:
- Sitemap parsing
- Dropdown navigation
- Search-based discovery
- Link following
- Post-crawl search
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Set, List, Dict, Any, Optional, AsyncIterator
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime
from collections import deque

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
import aiohttp
try:
    from playwright_stealth.stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    Stealth = None
from src.utils.cookie_handler import CookieHandler, NavigationHandler
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PageDiscoveryEngine:
    """
    Discover all internal pages within the target domain using multiple strategies.
    """

    def __init__(
        self,
        base_url: str,
        max_depth: Optional[int] = None,
        rate_limit_seconds: float = 2.0,
        max_concurrent: int = 3,
        respect_robots: bool = True,
        state_file: Optional[str] = None,
        proxy: Optional[Dict[str, str]] = None
    ):
        """
        Initialize page discovery engine.

        Args:
            base_url: Base URL of the website to crawl
            max_depth: Maximum depth for recursive link following (None = unlimited)
            rate_limit_seconds: Seconds to wait between requests
            max_concurrent: Maximum concurrent requests
            respect_robots: Whether to respect robots.txt
            state_file: Path to state file for resumption (default: state/crawl_state.json)
        """
        self.base_url = base_url.rstrip('/')
        self.base_domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        # Increase default rate limit to be more respectful (3-5 seconds between actions)
        self.rate_limit_seconds = max(rate_limit_seconds, 3.0)
        self.max_concurrent = max_concurrent
        self.respect_robots = respect_robots

        # State tracking
        self.visited_urls: Set[str] = set()
        self.pending_urls: deque = deque()
        self.discovered_urls: Set[str] = set()

        # State persistence
        self.state_file = Path(state_file) if state_file else Path("state/crawl_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Browser instances
        self.playwright = None  # Playwright instance
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Handlers
        self.cookie_handler: Optional[CookieHandler] = None
        self.nav_handler: Optional[NavigationHandler] = None
        
        # Proxy configuration
        self.proxy = proxy

    async def initialize_browser(
        self,
        headless: bool = True,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Initialize Playwright browser with proper configuration.

        Args:
            headless: Whether to run in headless mode
            viewport: Viewport size dict with 'width' and 'height'
            user_agent: Custom user-agent string
        """
        if not viewport:
            viewport = {'width': 1920, 'height': 1080}

        if not user_agent:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        self.playwright = await async_playwright().start()
        # Launch with stealth options
        launch_options = {
            'headless': headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        }
        
        # Add proxy if configured
        if self.proxy:
            launch_options['proxy'] = self.proxy
            proxy_info = self.proxy.get('server', 'unknown')
            if 'username' in self.proxy:
                proxy_info += f" (user: {self.proxy['username']})"
            logger.info(f"Using proxy: {proxy_info}")
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        self.context = await self.browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
        )
        
        # Apply playwright-stealth plugin (equivalent to puppeteer-extra-plugin-stealth)
        if STEALTH_AVAILABLE:
            logger.info("Applying playwright-stealth plugin for enhanced bot detection evasion")
            stealth = Stealth()
            await stealth.apply_stealth_async(self.context)
        else:
            logger.warning("playwright-stealth not available - using manual stealth features only")
            logger.warning("Install with: pip install playwright-stealth")
        
        # Remove webdriver property and add more stealth features
        # (These are in addition to playwright-stealth for extra protection)
        await self.context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        self.page = await self.context.new_page()

        # Initialize handlers
        self.cookie_handler = CookieHandler(self.page)
        self.nav_handler = NavigationHandler(self.page)

        logger.info(f"Browser initialized (headless={headless})")

    async def close_browser(self) -> None:
        """Close browser and cleanup resources."""
        try:
            # Close page first
            if self.page:
                try:
                    await self.page.close()
                except Exception as e:
                    logger.debug(f"Error closing page: {e}")
                finally:
                    self.page = None
            
            # Close context
            if self.context:
                try:
                    await self.context.close()
                except Exception as e:
                    logger.debug(f"Error closing context: {e}")
                finally:
                    self.context = None
            
            # Close browser
            if self.browser:
                try:
                    await self.browser.close()
                except Exception as e:
                    logger.debug(f"Error closing browser: {e}")
                finally:
                    self.browser = None
            
            # Stop playwright instance (this stops subprocesses)
            # This must happen last and we need to ensure it completes
            if self.playwright:
                try:
                    # Give a moment for any pending operations
                    await asyncio.sleep(0.1)
                    await self.playwright.stop()
                except Exception as e:
                    logger.debug(f"Error stopping playwright: {e}")
                finally:
                    self.playwright = None
            
            logger.info("Browser and Playwright instance closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison and deduplication.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        parsed = urlparse(url)
        # Remove fragment and trailing slash
        path = parsed.path.rstrip('/')
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.lower()

    def is_internal_url(self, url: str) -> bool:
        """
        Check if URL is internal to the site.

        Args:
            url: URL to check

        Returns:
            True if URL is internal
        """
        parsed = urlparse(url)

        # Relative URL
        if not parsed.netloc:
            return True

        # Check if same domain (handles www.ducati.com, ducati.com, etc.)
        domain_parts = self.base_domain.split('.')
        url_domain_parts = parsed.netloc.split('.')

        # Match if ends with same domain
        return '.'.join(domain_parts[-2:]) in parsed.netloc or parsed.netloc == self.base_domain

    def get_visited_count(self) -> int:
        """
        Get count of visited URLs.

        Returns:
            Number of visited URLs
        """
        return len(self.visited_urls)

    def save_state(self) -> None:
        """Save current crawl state to file."""
        try:
            state = {
                'visited_urls': list(self.visited_urls),
                'discovered_urls': list(self.discovered_urls),
                'pending_urls': list(self.pending_urls),
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"State saved: {len(self.visited_urls)} visited URLs")
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def load_state(self) -> None:
        """Load previous crawl state from file."""
        if not self.state_file.exists():
            logger.info("No previous state found")
            return

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            # Verify it's the same base URL
            if state.get('base_url') != self.base_url:
                logger.warning("State file is for different base URL, ignoring")
                return

            self.visited_urls = set(state.get('visited_urls', []))
            self.discovered_urls = set(state.get('discovered_urls', []))
            self.pending_urls = deque(state.get('pending_urls', []))

            logger.info(f"Loaded state: {len(self.visited_urls)} visited URLs, {len(self.pending_urls)} pending")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")

    async def check_sitemap(self) -> List[str]:
        """
        Check for sitemap.xml and extract URLs.

        Returns:
            List of URLs from sitemap
        """
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
        ]

        urls = []
        async with aiohttp.ClientSession() as session:
            for sitemap_url in sitemap_urls:
                try:
                    async with session.get(sitemap_url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            # Simple XML parsing for URLs
                            url_matches = re.findall(r'<loc>(.*?)</loc>', content)
                            for url in url_matches:
                                if self.is_internal_url(url):
                                    normalized = self.normalize_url(url)
                                    urls.append(normalized)
                            logger.info(f"Found {len(url_matches)} URLs in {sitemap_url}")
                except Exception as e:
                    logger.debug(f"Could not fetch {sitemap_url}: {e}")

        return urls

    async def discover_all_pages(self) -> AsyncIterator[str]:
        """
        Discover all pages using all available strategies.

        Yields:
            Discovered URLs
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")

        # Load previous state
        self.load_state()

        # Step 1: Navigate to base URL and handle cookie consent
        # Note: Navigation happens in the loop above, cookie handling is done there too
        logger.info(f"Starting page discovery from {self.base_url}")
        
        # Try locale-specific URLs first (these often work better)
        # Start with /ca/en/home since that's what works in browser
        urls_to_try = [
            f"{self.base_url}/ca/en/home",
            f"{self.base_url}/us/en/home",
            f"{self.base_url}/ww/en/home",
            self.base_url,
        ]
        
        navigation_success = False
        for url in urls_to_try:
            try:
                logger.info(f"Attempting to navigate to {url}")
                
                # Add random mouse movement to appear more human-like
                await self.page.mouse.move(100, 100)
                await asyncio.sleep(0.5)
                
                response = await self.page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=60000
                )
                
                # Wait longer for page to fully load and any JS to execute
                await asyncio.sleep(3)
                
                # Handle cookie consent immediately
                await self.cookie_handler.accept_cookies(custom_selector="#onetrust-accept-btn-handler")
                await asyncio.sleep(1)
                
                # Scroll a bit to trigger lazy loading
                await self.page.evaluate("window.scrollTo(0, 100)")
                await asyncio.sleep(1)
                
                # Check if we got blocked
                title = await self.page.title()
                content = await self.page.content()
                
                if response and response.status == 403:
                    logger.warning(f"Got 403 Forbidden on {url}")
                    continue
                
                if "Access Denied" in title or "access denied" in content.lower():
                    logger.warning(f"Access Denied on {url}, trying next URL...")
                    continue
                
                # Success!
                logger.info(f"Successfully loaded {url}")
                navigation_success = True
                break
                
            except Exception as e:
                logger.debug(f"Error navigating to {url}: {e}")
                continue
        
        if not navigation_success:
            logger.error("Failed to access site. All URLs returned Access Denied or errors.")
            logger.error("The site may be blocking automated access. Possible solutions:")
            logger.error("  1. Use a VPN or different IP address")
            logger.error("  2. Add delays between requests")
            logger.error("  3. Use residential proxy")
            raise RuntimeError("Could not access website - all URLs blocked")

        # Accept cookies
        await self.cookie_handler.accept_cookies(custom_selector="#onetrust-accept-btn-handler")
        await self.page.wait_for_timeout(1000)

        # Step 2: Check sitemap (in background, doesn't require page navigation)
        logger.info("Checking sitemap...")
        sitemap_urls = await self.check_sitemap()
        for url in sitemap_urls:
            if url not in self.visited_urls:
                self.discovered_urls.add(url)
                yield url

        logger.info(f"Sitemap discovery: {len(sitemap_urls)} URLs")
        
        # Add delay before next step
        await asyncio.sleep(self.rate_limit_seconds)

        # Step 3: Discover from hamburger menu navigation (human-like)
        logger.info("Discovering from hamburger menu navigation...")
        hamburger_urls = await self._discover_via_hamburger_menu()
        for url in hamburger_urls:
            if url not in self.visited_urls:
                self.discovered_urls.add(url)
                yield url

        logger.info(f"Hamburger menu discovery: {len(hamburger_urls)} URLs")
        
        # Step 3a: Discover heritage bikes
        logger.info("Discovering heritage bikes...")
        heritage_urls = await self._discover_heritage_bikes()
        for url in heritage_urls:
            if url not in self.visited_urls:
                self.discovered_urls.add(url)
                yield url

        logger.info(f"Heritage bikes discovery: {len(heritage_urls)} URLs")
        
        # Step 3b: Discover from dropdown (fallback)
        logger.info("Discovering from MODELS dropdown...")
        dropdown_urls = await self._discover_from_dropdown()
        for url in dropdown_urls:
            if url not in self.visited_urls:
                self.discovered_urls.add(url)
                yield url

        logger.info(f"Dropdown discovery: {len(dropdown_urls)} URLs")

        # Step 4: Search-based discovery
        logger.info("Search-based discovery...")
        search_urls = await self._discover_via_search()
        for url in search_urls:
            if url not in self.visited_urls:
                self.discovered_urls.add(url)
                yield url

        logger.info(f"Search discovery: {len(search_urls)} URLs")

        # Step 5: Follow links from discovered bike pages
        logger.info("Following links from discovered bike pages...")
        if self.discovered_urls:
            # Take a sample of discovered URLs to follow links from
            sample_urls = list(self.discovered_urls)[:20]  # Limit to avoid too many requests
            link_urls = await self._follow_links_from_pages(sample_urls)
            for url in link_urls:
                if url not in self.visited_urls:
                    self.discovered_urls.add(url)
                    yield url
            logger.info(f"Link following from bike pages: {len(link_urls)} URLs")
        
        # Step 6: Link following from key pages (fallback)
        logger.info("Link following discovery from key pages...")
        link_urls = await self._discover_via_link_following()
        for url in link_urls:
            if url not in self.visited_urls:
                self.discovered_urls.add(url)
                yield url

        logger.info(f"Link following: {len(link_urls)} URLs")

        # Save final state
        self.save_state()

    async def _discover_via_hamburger_menu(self) -> Set[str]:
        """
        Discover URLs by clicking through hamburger menu like a human.
        Clicks hamburger -> BIKES -> expands categories -> collects links.
        """
        discovered = set()
        
        try:
            # Wait for page to be fully loaded
            await asyncio.sleep(2)
            
            # Step 1: Click hamburger menu
            logger.info("Clicking hamburger menu...")
            hamburger_selectors = [
                '.hamburger[data-js-navtoggle]',
                '[data-js-navtoggle]',
                '.hamburger',
                'button[aria-label*="menu" i]',
                'button[aria-label*="navigation" i]',
            ]
            
            hamburger_clicked = False
            for selector in hamburger_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        visible = await element.is_visible()
                        if visible:
                            # Human-like: move mouse to element first
                            box = await element.bounding_box()
                            if box:
                                await self.page.mouse.move(
                                    box['x'] + box['width'] / 2,
                                    box['y'] + box['height'] / 2
                                )
                                await asyncio.sleep(0.3)  # Pause before click
                            
                            await element.click()
                            logger.info(f"Clicked hamburger menu: {selector}")
                            hamburger_clicked = True
                            await asyncio.sleep(1.5)  # Wait for menu to open
                            break
                except Exception as e:
                    logger.debug(f"Error with hamburger selector {selector}: {e}")
                    continue
            
            if not hamburger_clicked:
                logger.warning("Could not find hamburger menu")
                return discovered
            
            # Step 2: Click BIKES link
            logger.info("Clicking BIKES link...")
            bikes_selectors = [
                'a[data-js-navlv2-trigger]:has-text("BIKES")',
                'a:has-text("BIKES")',
                '[data-js-navlv2-trigger]:has-text("BIKES")',
                'a[href*="bikes"]:has-text("BIKES")',
            ]
            
            bikes_clicked = False
            for selector in bikes_selectors:
                try:
                    # Wait for menu to be visible
                    await asyncio.sleep(0.5)
                    element = await self.page.query_selector(selector)
                    if element:
                        visible = await element.is_visible()
                        if visible:
                            # Scroll element into view
                            await element.scroll_into_view_if_needed()
                            await asyncio.sleep(0.3)
                            
                            # Human-like mouse movement
                            box = await element.bounding_box()
                            if box:
                                await self.page.mouse.move(
                                    box['x'] + box['width'] / 2,
                                    box['y'] + box['height'] / 2
                                )
                                await asyncio.sleep(0.2)
                            
                            await element.click()
                            logger.info(f"Clicked BIKES: {selector}")
                            bikes_clicked = True
                            await asyncio.sleep(2)  # Wait for submenu to expand
                            break
                except Exception as e:
                    logger.debug(f"Error with BIKES selector {selector}: {e}")
                    continue
            
            if not bikes_clicked:
                logger.warning("Could not find BIKES link")
                return discovered
            
            # Step 3: Expand all category titles (click titles to expand subcategories)
            logger.info("Expanding bike categories...")
            category_title_selectors = [
                '.title[data-js-navlv2-trigger]',
                '.title[class*="opened"]',
                'div.title',
                '[class*="title"]:has-text("DESERTX")',
                '[class*="title"]:has-text("XDIAVEL")',
                '[class*="title"]:has-text("MONSTER")',
            ]
            
            # Find all expandable titles
            titles = await self.page.query_selector_all('div.title')
            for title in titles:
                try:
                    # Check if it's expandable (has data-js-navlv2-trigger or similar)
                    has_trigger = await title.get_attribute('data-js-navlv2-trigger')
                    class_attr = await title.get_attribute('class') or ''
                    
                    # Skip if already opened
                    if '-opened' in class_attr:
                        continue
                    
                    # Click to expand
                    visible = await title.is_visible()
                    if visible:
                        await title.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        
                        box = await title.bounding_box()
                        if box:
                            await self.page.mouse.move(
                                box['x'] + box['width'] / 2,
                                box['y'] + box['height'] / 2
                            )
                            await asyncio.sleep(0.2)
                        
                        await title.click()
                        logger.debug(f"Expanded category: {await title.inner_text()}")
                        await asyncio.sleep(1.5)  # Wait for submenu to expand
                except Exception as e:
                    logger.debug(f"Error expanding category: {e}")
                    continue
            
            # Step 4: Collect all bike links from the menu
            logger.info("Collecting bike links from menu...")
            await asyncio.sleep(1)  # Final wait for all menus to be ready
            
            # Find all links in the navigation menu
            bike_link_selectors = [
                'a[href*="/bikes/"]',
                'a[href*="/ca/en/bikes/"]',
                'a[href*="/us/en/bikes/"]',
                'a[href*="/ww/en/bikes/"]',
            ]
            
            all_links = set()
            for selector in bike_link_selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                # Only include actual bike pages, not category pages
                                # Exclude common non-bike pages
                                if '/bikes/' in normalized and normalized not in all_links:
                                    # Filter out non-bike pages
                                    if not any(skip in normalized for skip in ['/compare', '/configurator', '/dealer']):
                                        all_links.add(normalized)
                        except Exception as e:
                            logger.debug(f"Error extracting link: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            # Step 4b: Extract links from ul.list elements (Ducati-specific menu structure)
            # These lists contain bike model names that may be clickable or contain links
            logger.info("Extracting links from ul.list elements...")
            try:
                list_elements = await self.page.query_selector_all('ul.list')
                logger.debug(f"Found {len(list_elements)} ul.list elements")
                
                for ul_list in list_elements:
                    try:
                        # Look for <a> tags within the list
                        links_in_list = await ul_list.query_selector_all('a[href]')
                        for link in links_in_list:
                            try:
                                href = await link.get_attribute('href')
                                if href and self.is_internal_url(href):
                                    full_url = urljoin(self.base_url, href)
                                    normalized = self.normalize_url(full_url)
                                    if '/bikes/' in normalized and normalized not in all_links:
                                        if not any(skip in normalized for skip in ['/compare', '/configurator', '/dealer']):
                                            all_links.add(normalized)
                                            logger.debug(f"Found link in ul.list: {normalized}")
                            except Exception as e:
                                logger.debug(f"Error extracting link from ul.list: {e}")
                                continue
                        
                        # Also check if the list items themselves are clickable
                        list_items = await ul_list.query_selector_all('li')
                        for li in list_items:
                            try:
                                # Check if li contains a link
                                link_in_li = await li.query_selector('a[href]')
                                if link_in_li:
                                    href = await link_in_li.get_attribute('href')
                                    if href and self.is_internal_url(href):
                                        full_url = urljoin(self.base_url, href)
                                        normalized = self.normalize_url(full_url)
                                        if '/bikes/' in normalized and normalized not in all_links:
                                            if not any(skip in normalized for skip in ['/compare', '/configurator', '/dealer']):
                                                all_links.add(normalized)
                                                logger.debug(f"Found link in li: {normalized}")
                                
                                # Check if li itself is clickable (has onclick or data attributes)
                                onclick = await li.get_attribute('onclick')
                                data_href = await li.get_attribute('data-href')
                                if onclick or data_href:
                                    # Try to extract URL from onclick or data-href
                                    if data_href:
                                        href = data_href
                                    elif onclick and '/bikes/' in onclick:
                                        # Extract URL from onclick handler
                                        import re
                                        url_match = re.search(r'["\']([^"\']*\/bikes\/[^"\']*)["\']', onclick)
                                        if url_match:
                                            href = url_match.group(1)
                                        else:
                                            continue
                                    else:
                                        continue
                                    
                                    if href and self.is_internal_url(href):
                                        full_url = urljoin(self.base_url, href)
                                        normalized = self.normalize_url(full_url)
                                        if '/bikes/' in normalized and normalized not in all_links:
                                            if not any(skip in normalized for skip in ['/compare', '/configurator', '/dealer']):
                                                all_links.add(normalized)
                                                logger.debug(f"Found clickable li link: {normalized}")
                            except Exception as e:
                                logger.debug(f"Error checking li for links: {e}")
                                continue
                    except Exception as e:
                        logger.debug(f"Error processing ul.list: {e}")
                        continue
                
                logger.info(f"Found {len(all_links)} total links from menu (including ul.list)")
            except Exception as e:
                logger.debug(f"Error extracting from ul.list elements: {e}")
            
            logger.info(f"Collected {len(all_links)} initial bike links from menu")
            
            discovered.update(all_links)
            logger.info(f"Found {len(all_links)} bike links from hamburger menu")
            
            # Step 5: Also try to find links by scrolling through the menu
            # Some links might be lazy-loaded
            try:
                menu_container = await self.page.query_selector('nav, [class*="nav"], [class*="menu"]')
                if menu_container:
                    # Scroll through menu to trigger lazy loading
                    for i in range(5):  # Increased scrolls
                        await self.page.evaluate(f"window.scrollBy(0, 200)")
                        await asyncio.sleep(0.5)
                    
                    # Collect links again after scrolling
                    for selector in bike_link_selectors:
                        links = await self.page.query_selector_all(selector)
                        for link in links:
                            try:
                                href = await link.get_attribute('href')
                                if href and self.is_internal_url(href):
                                    full_url = urljoin(self.base_url, href)
                                    normalized = self.normalize_url(full_url)
                                    if '/bikes/' in normalized:
                                        discovered.add(normalized)
                            except:
                                continue
            except Exception as e:
                logger.debug(f"Error scrolling menu: {e}")
            
            # Step 6: Visit bike pages to find sister/related links
            # This discovers specs, gallery, variants, related models, etc.
            if all_links:
                logger.info(f"Visiting {min(len(all_links), 30)} bike pages to discover sister links...")
                sample_links = list(all_links)[:30]  # Visit first 30 to find patterns
                
                for i, bike_url in enumerate(sample_links, 1):
                    try:
                        logger.debug(f"Visiting bike page {i}/{len(sample_links)}: {bike_url}")
                        await self._discover_sister_links_from_page(bike_url, discovered)
                        await asyncio.sleep(self.rate_limit_seconds)  # Rate limiting
                    except Exception as e:
                        logger.debug(f"Error visiting {bike_url}: {e}")
                        continue
                
                logger.info(f"Discovered {len(discovered)} total links (including sister links)")
            
        except Exception as e:
            logger.error(f"Error in hamburger menu discovery: {e}", exc_info=True)
        
        return discovered
    
    async def _discover_sister_links_from_page(self, bike_url: str, discovered: Set[str]) -> None:
        """
        Visit a bike page and discover all related/sister links:
        - Specs pages
        - Gallery pages
        - Features pages
        - Variants (V2, V4, SP, etc.)
        - Related models
        - Tabs and navigation within the page
        """
        try:
            logger.debug(f"Visiting {bike_url} to find sister links...")
            
            # Navigate to bike page
            await self.page.goto(bike_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)  # Wait for page to load
            
            # Scroll to trigger lazy loading
            await self.page.evaluate("window.scrollTo(0, 300)")
            await asyncio.sleep(1)
            await self.page.evaluate("window.scrollTo(0, 600)")
            await asyncio.sleep(1)
            await self.page.evaluate("window.scrollTo(0, 900)")
            await asyncio.sleep(1)
            
            # 1. Find tabs/navigation within the page
            tab_selectors = [
                'a[href*="/specs"]',
                'a[href*="/gallery"]',
                'a[href*="/features"]',
                'a[href*="/technical"]',
                'a[href*="/tech-data"]',
                'a[href*="/equipment"]',
                'a[href*="/accessories"]',
                'a[href*="/configurator"]',
                '[role="tab"] a',
                '.tabs a',
                '[class*="tab"] a',
                'nav[class*="tab"] a',
            ]
            
            for selector in tab_selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                if '/bikes/' in normalized or any(kw in normalized for kw in ['/specs', '/gallery', '/features', '/technical']):
                                    discovered.add(normalized)
                        except:
                            continue
                except:
                    continue
            
            # 2. Find variant links (V2, V4, SP, etc.) - usually in model selector or related section
            variant_selectors = [
                'a[href*="/v2"]',
                'a[href*="/v4"]',
                'a[href*="/sp"]',
                'a[href*="/rs"]',
                'a[href*="/r"]',
                '[class*="variant"] a',
                '[class*="model-selector"] a',
                '[class*="related-models"] a',
                '[class*="sister"] a',
            ]
            
            for selector in variant_selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                if '/bikes/' in normalized:
                                    discovered.add(normalized)
                        except:
                            continue
                except:
                    continue
            
            # 3. Find "View all models" or "See more" links
            view_all_selectors = [
                'a:has-text("View all")',
                'a:has-text("See all")',
                'a:has-text("All models")',
                'a:has-text("Explore")',
                'a:has-text("Discover")',
                'a[href*="/bikes/"]:not([href*="specs"]):not([href*="gallery"])',
            ]
            
            for selector in view_all_selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                if '/bikes/' in normalized:
                                    discovered.add(normalized)
                        except:
                            continue
                except:
                    continue
            
            # 4. Find related bikes section (usually at bottom of page)
            related_sections = [
                '[class*="related"] a[href*="/bikes/"]',
                '[class*="similar"] a[href*="/bikes/"]',
                '[class*="recommended"] a[href*="/bikes/"]',
                '[class*="you-may-like"] a[href*="/bikes/"]',
                '[class*="also-interest"] a[href*="/bikes/"]',
            ]
            
            for selector in related_sections:
                try:
                    links = await self.page.query_selector_all(selector)
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                if '/bikes/' in normalized:
                                    discovered.add(normalized)
                        except:
                            continue
                except:
                    continue
            
            # 5. Look for any bike links in the page content
            all_bike_links = await self.page.query_selector_all('a[href*="/bikes/"]')
            for link in all_bike_links:
                try:
                    href = await link.get_attribute('href')
                    if href and self.is_internal_url(href):
                        full_url = urljoin(self.base_url, href)
                        normalized = self.normalize_url(full_url)
                        # Exclude current page
                        if '/bikes/' in normalized and normalized != self.normalize_url(bike_url):
                            discovered.add(normalized)
                except:
                    continue
            
            # 6. Try hovering over elements to reveal hidden links (some sites use hover menus)
            try:
                hoverable_elements = await self.page.query_selector_all('[class*="hover"], [class*="dropdown"], [data-hover]')
                for element in hoverable_elements[:10]:  # Limit to avoid too many
                    try:
                        # Hover to reveal
                        await element.hover()
                        await asyncio.sleep(0.5)
                        
                        # Look for links that appeared
                        revealed_links = await self.page.query_selector_all('a[href*="/bikes/"]')
                        for link in revealed_links:
                            try:
                                href = await link.get_attribute('href')
                                if href and self.is_internal_url(href):
                                    full_url = urljoin(self.base_url, href)
                                    normalized = self.normalize_url(full_url)
                                    if '/bikes/' in normalized:
                                        discovered.add(normalized)
                            except:
                                continue
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Error with hover discovery: {e}")
            
            # 7. Look for pagination or "Load more" buttons
            pagination_selectors = [
                'a:has-text("Load more")',
                'a:has-text("Show more")',
                'button:has-text("Load more")',
                '[class*="pagination"] a',
                '[class*="load-more"]',
            ]
            
            for selector in pagination_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for elem in elements:
                        try:
                            # Try clicking to load more content
                            if await elem.is_visible():
                                await elem.click()
                                await asyncio.sleep(2)  # Wait for content to load
                                
                                # Collect new links that appeared
                                new_links = await self.page.query_selector_all('a[href*="/bikes/"]')
                                for link in new_links:
                                    try:
                                        href = await link.get_attribute('href')
                                        if href and self.is_internal_url(href):
                                            full_url = urljoin(self.base_url, href)
                                            normalized = self.normalize_url(full_url)
                                            if '/bikes/' in normalized:
                                                discovered.add(normalized)
                                    except:
                                        continue
                        except:
                            continue
                except:
                    continue
            
            # 8. Find d-button links (insights, stories, travel pages)
            logger.debug("Looking for d-button links (insights, stories)...")
            d_button_selectors = [
                'a.d-button[href]',
                'a[class*="d-button"][href]',
            ]
            
            for selector in d_button_selectors:
                try:
                    buttons = await self.page.query_selector_all(selector)
                    for button in buttons:
                        try:
                            href = await button.get_attribute('href')
                            text = await button.inner_text()
                            
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                
                                # Include insights pages, stories pages, and other related pages
                                if any(pattern in normalized for pattern in [
                                    '/insights',
                                    '/stories',
                                    '/travel',
                                    '/news',
                                    '/events',
                                ]) or '/bikes/' in normalized:
                                    discovered.add(normalized)
                                    logger.debug(f"Found d-button link: {normalized} (text: {text[:50]})")
                        except Exception as e:
                            logger.debug(f"Error extracting d-button link: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Error with d-button selector {selector}: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"Error discovering sister links from {bike_url}: {e}")

    async def _discover_heritage_bikes(self) -> Set[str]:
        """
        Discover heritage bike pages by navigating to heritage/bikes page,
        clicking tabs (ROAD, RACING, etc.), and extracting links from images.
        
        Returns:
            Set of discovered heritage bike URLs
        """
        discovered = set()
        
        try:
            # Navigate to heritage bikes page
            heritage_urls = [
                f"{self.base_url}/ww/en/heritage/bikes",
                f"{self.base_url}/ca/en/heritage/bikes",
                f"{self.base_url}/us/en/heritage/bikes",
            ]
            
            navigation_success = False
            for heritage_url in heritage_urls:
                try:
                    logger.info(f"Navigating to heritage bikes page: {heritage_url}")
                    await self.page.goto(heritage_url, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Check if page loaded successfully
                    title = await self.page.title()
                    if "Access Denied" not in title:
                        navigation_success = True
                        break
                except Exception as e:
                    logger.debug(f"Error navigating to {heritage_url}: {e}")
                    continue
            
            if not navigation_success:
                logger.warning("Could not access heritage bikes page")
                return discovered
            
            # Handle cookies if needed
            await self.cookie_handler.accept_cookies()
            await asyncio.sleep(1)
            
            # Find all tabs (ROAD, RACING, etc.)
            logger.info("Finding heritage bike tabs...")
            tab_selectors = [
                'a.d-tab',
                'a[class*="tab"]',
                '[role="tab"]',
                '.tabs a',
            ]
            
            tabs = []
            for selector in tab_selectors:
                try:
                    found_tabs = await self.page.query_selector_all(selector)
                    for tab in found_tabs:
                        text = await tab.inner_text()
                        if text and text.strip():
                            tabs.append((tab, text.strip()))
                except Exception as e:
                    logger.debug(f"Error with tab selector {selector}: {e}")
                    continue
            
            logger.info(f"Found {len(tabs)} tabs: {[text for _, text in tabs]}")
            
            # Click each tab and extract links
            for tab_element, tab_text in tabs:
                try:
                    logger.info(f"Clicking tab: {tab_text}")
                    
                    # Scroll tab into view
                    await tab_element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    
                    # Human-like mouse movement
                    box = await tab_element.bounding_box()
                    if box:
                        await self.page.mouse.move(
                            box['x'] + box['width'] / 2,
                            box['y'] + box['height'] / 2
                        )
                        await asyncio.sleep(0.2)
                    
                    # Click tab
                    await tab_element.click()
                    await asyncio.sleep(2)  # Wait for content to load
                    
                    # Extract links from images in div.body
                    body_divs = await self.page.query_selector_all('div.body')
                    for body_div in body_divs:
                        # Find all images in this body div
                        images = await body_div.query_selector_all('img')
                        for img in images:
                            try:
                                # Check if image is inside a link - get href from closest anchor
                                parent_href = await img.evaluate('el => { const a = el.closest("a"); return a ? a.href : null; }')
                                if parent_href and parent_href != 'javascript:void(0);':
                                    if self.is_internal_url(parent_href):
                                        normalized = self.normalize_url(parent_href)
                                        if '/heritage/' in normalized and normalized not in discovered:
                                            discovered.add(normalized)
                                            logger.debug(f"Found heritage bike link: {normalized}")
                                
                                # Also check if image has onclick or data-href
                                onclick = await img.get_attribute('onclick')
                                data_href = await img.get_attribute('data-href')
                                if onclick or data_href:
                                    if data_href:
                                        href = data_href
                                    elif onclick and '/heritage/' in onclick:
                                        import re
                                        url_match = re.search(r'["\']([^"\']*\/heritage\/[^"\']*)["\']', onclick)
                                        if url_match:
                                            href = url_match.group(1)
                                        else:
                                            continue
                                    else:
                                        continue
                                    
                                    if href and self.is_internal_url(href):
                                        full_url = urljoin(self.base_url, href)
                                        normalized = self.normalize_url(full_url)
                                        if '/heritage/' in normalized and normalized not in discovered:
                                            discovered.add(normalized)
                                            logger.debug(f"Found heritage bike link (from data): {normalized}")
                            except Exception as e:
                                logger.debug(f"Error extracting link from image: {e}")
                                continue
                    
                    # Also check for links directly in body div
                    links_in_body = await body_div.query_selector_all('a[href]')
                    for link in links_in_body:
                        try:
                            href = await link.get_attribute('href')
                            if href and href != 'javascript:void(0);' and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                if '/heritage/' in normalized and normalized not in discovered:
                                    discovered.add(normalized)
                                    logger.debug(f"Found heritage bike link (direct): {normalized}")
                        except Exception as e:
                            logger.debug(f"Error extracting direct link: {e}")
                            continue
                    
                    await asyncio.sleep(self.rate_limit_seconds)
                    
                except Exception as e:
                    logger.debug(f"Error processing tab {tab_text}: {e}")
                    continue
            
            logger.info(f"Discovered {len(discovered)} heritage bike URLs")
            
        except Exception as e:
            logger.error(f"Error in heritage bikes discovery: {e}", exc_info=True)
        
        return discovered

    async def _discover_from_dropdown(self) -> Set[str]:
        """Discover URLs from MODELS dropdown."""
        discovered = set()

        try:
            # Click MODELS dropdown
            models_clicked = await self.nav_handler.click_dropdown(
                selector='a[data-js-shortcutnav=""]:has-text("MODELS")',
                wait_for_visible=True
            )

            if not models_clicked:
                # Try alternative selector
                models_clicked = await self.nav_handler.click_dropdown(
                    selector='a:has-text("MODELS")',
                    wait_for_visible=True
                )

            if not models_clicked:
                logger.warning("Could not click MODELS dropdown")
                return discovered

            await self.page.wait_for_timeout(1000)

            # Extract all bike links
            discover_links = await self.page.query_selector_all(
                'a[href*="/bikes/"], a[href*="/model"], a[href*="/heritage/"]'
            )

            for link in discover_links:
                try:
                    href = await link.get_attribute('href')
                    if href and self.is_internal_url(href):
                        full_url = urljoin(self.base_url, href)
                        normalized = self.normalize_url(full_url)
                        discovered.add(normalized)
                except Exception as e:
                    logger.debug(f"Error extracting link: {e}")

        except Exception as e:
            logger.error(f"Error in dropdown discovery: {e}")

        return discovered

    async def _discover_via_search(self) -> Set[str]:
        """Discover URLs using site search."""
        discovered = set()

        try:
            # Navigate back to homepage
            await self.page.goto(self.base_url, wait_until='domcontentloaded')
            await self.page.wait_for_timeout(1000)

            # Find search button
            search_selectors = [
                'button[aria-label*="search" i]',
                'a[href*="search"]',
                'button:has-text("Search")',
                '[class*="search"] button',
            ]

            search_button = None
            for selector in search_selectors:
                try:
                    search_button = await self.page.query_selector(selector)
                    if search_button and await search_button.is_visible():
                        break
                except:
                    continue

            if not search_button:
                logger.info("No search button found")
                return discovered

            # Click search
            await search_button.click()
            await self.page.wait_for_timeout(1000)

            # Find search input
            search_input_selectors = [
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[name*="search" i]',
            ]

            search_input = None
            for selector in search_input_selectors:
                try:
                    search_input = await self.page.query_selector(selector)
                    if search_input and await search_input.is_visible():
                        break
                except:
                    continue

            if not search_input:
                logger.warning("Search button found but no search input")
                return discovered

            # Perform searches
            search_terms = ["bike", "motorcycle", "model"]

            for term in search_terms:
                try:
                    await search_input.fill('')
                    await search_input.type(term, delay=100)
                    await search_input.press('Enter')
                    await self.page.wait_for_timeout(2000)

                    # Extract result links
                    result_links = await self.page.query_selector_all(
                        'a[href*="/bikes/"], a[href*="/heritage/"], .search-result a'
                    )

                    for link in result_links:
                        try:
                            href = await link.get_attribute('href')
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                discovered.add(normalized)
                        except:
                            continue

                    # Go back
                    await self.page.go_back()
                    await self.page.wait_for_timeout(1000)

                except Exception as e:
                    logger.debug(f"Error searching for '{term}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in search discovery: {e}")

        return discovered

    async def _follow_links_from_pages(self, page_urls: List[str]) -> Set[str]:
        """
        Follow links from discovered bike pages to find related pages (specs, gallery, etc.).
        Navigates like a human with proper delays.
        """
        discovered = set()
        
        for url in page_urls:
            try:
                logger.debug(f"Following links from {url}")
                
                # Navigate to page
                await self.page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)  # Human-like delay
                
                # Scroll page to trigger lazy loading
                await self.page.evaluate("window.scrollTo(0, 300)")
                await asyncio.sleep(1)
                await self.page.evaluate("window.scrollTo(0, 600)")
                await asyncio.sleep(1)
                
                # Find related links (specs, gallery, features, etc.)
                related_selectors = [
                    'a[href*="/specs"]',
                    'a[href*="/gallery"]',
                    'a[href*="/features"]',
                    'a[href*="/technical"]',
                    'a[href*="/tech-data"]',
                    'a[href*="/equipment"]',
                    'a[href*="/accessories"]',
                    'a[href*="/configurator"]',
                    # Also look for links in navigation or tabs
                    'nav a[href*="/bikes/"]',
                    '.tabs a[href*="/bikes/"]',
                    '[class*="tab"] a[href*="/bikes/"]',
                ]
                
                for selector in related_selectors:
                    try:
                        links = await self.page.query_selector_all(selector)
                        for link in links:
                            try:
                                href = await link.get_attribute('href')
                                if href and self.is_internal_url(href):
                                    full_url = urljoin(self.base_url, href)
                                    normalized = self.normalize_url(full_url)
                                    
                                    # Only include bike-related pages
                                    if any(kw in normalized for kw in ['/bikes/', '/heritage/', '/model']):
                                        discovered.add(normalized)
                            except:
                                continue
                    except:
                        continue
                
                # Also look for "View all models" or similar links
                view_all_selectors = [
                    'a:has-text("View all")',
                    'a:has-text("All models")',
                    'a:has-text("See all")',
                    'a[href*="/bikes/"]:not([href*="specs"]):not([href*="gallery"])',
                ]
                
                for selector in view_all_selectors:
                    try:
                        links = await self.page.query_selector_all(selector)
                        for link in links:
                            try:
                                href = await link.get_attribute('href')
                                if href and self.is_internal_url(href):
                                    full_url = urljoin(self.base_url, href)
                                    normalized = self.normalize_url(full_url)
                                    if '/bikes/' in normalized:
                                        discovered.add(normalized)
                            except:
                                continue
                    except:
                        continue
                
                # Rate limiting - be respectful
                await asyncio.sleep(self.rate_limit_seconds)
                
            except Exception as e:
                logger.debug(f"Error following links from {url}: {e}")
                continue
        
        return discovered

    async def _discover_via_link_following(self, max_depth: int = 2) -> Set[str]:
        """Recursively follow links from key pages."""
        discovered = set()

        # Key pages to start from
        key_urls = [
            f"{self.base_url}/ww/en/heritage/bikes/",
            f"{self.base_url}/ca/en/home",
        ]

        to_visit = [(url, 0) for url in key_urls]
        visited_in_pass = set()

        while to_visit:
            url, depth = to_visit.pop(0)

            if depth > max_depth or url in visited_in_pass:
                continue

            visited_in_pass.add(url)

            try:
                await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await self.page.wait_for_timeout(1000)

                # Extract all links
                links = await self.page.query_selector_all('a[href]')
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        if href and self.is_internal_url(href):
                            full_url = urljoin(self.base_url, href)
                            normalized = self.normalize_url(full_url)

                            # Only follow bike/heritage related URLs
                            if any(kw in normalized for kw in ['/bikes/', '/heritage/', '/model']):
                                discovered.add(normalized)
                                if depth < max_depth:
                                    to_visit.append((normalized, depth + 1))
                    except:
                        continue

                await asyncio.sleep(self.rate_limit_seconds)

            except Exception as e:
                logger.debug(f"Error following links from {url}: {e}")
                continue

        return discovered
