"""
Full-site crawler for motorcycle OEM website.
Discovers all bike pages, extracts content, downloads images, and creates markdown files.
"""

import asyncio
import sys
import re
import json
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime
from typing import Set, List, Dict, Any, Optional
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from src.utils.cookie_handler import CookieHandler, NavigationHandler
import logging
import aiohttp
import aiofiles

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SiteCrawler:
    """Full-site crawler for motorcycle OEM website."""
    
    def __init__(
        self,
        base_url: str,
        output_dir: str = "/mnt/seagate4tb/moto-scraper-v1",
        images_dir: str = None,
        rate_limit: float = 2.0
    ):
        """
        Initialize crawler.
        
        Args:
            base_url: Base URL of the website
            output_dir: Directory for markdown files and images
            images_dir: Subdirectory for images (default: output_dir/images)
            rate_limit: Seconds to wait between requests
        """
        self.base_url = base_url.rstrip('/')
        self.base_domain = urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.images_dir = Path(images_dir) if images_dir else self.output_dir / "images"
        self.rate_limit = rate_limit
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.visited_urls: Set[str] = set()
        self.bike_pages: List[Dict[str, Any]] = []
        self.image_hashes: Set[str] = set()  # For deduplication
        
        # Load state if exists
        self.state_file = self.output_dir / "crawl_state.json"
        self.load_state()
    
    def load_state(self):
        """Load previous crawl state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.visited_urls = set(state.get('visited_urls', []))
                    logger.info(f"Loaded state: {len(self.visited_urls)} visited URLs")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
    
    def save_state(self):
        """Save current crawl state."""
        try:
            state = {
                'visited_urls': list(self.visited_urls),
                'bike_pages': len(self.bike_pages),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        parsed = urlparse(url)
        # Remove fragment and trailing slash
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.lower()
    
    def is_internal_url(self, url: str) -> bool:
        """Check if URL is internal to the site."""
        parsed = urlparse(url)
        # Handle different subdomains and paths (ca/en, ww/en, etc.)
        if not parsed.netloc:
            return True  # Relative URL
        # Check if same domain (handles www.ducati.com, ducati.com, etc.)
        domain_parts = self.base_domain.split('.')
        url_domain_parts = parsed.netloc.split('.')
        # Match if ends with same domain (e.g., www.ducati.com and ducati.com)
        return '.'.join(domain_parts[-2:]) in parsed.netloc or parsed.netloc == self.base_domain
    
    async def check_sitemap(self) -> List[str]:
        """Check for sitemap.xml and extract URLs."""
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
                                    urls.append(self.normalize_url(url))
                            logger.info(f"Found {len(url_matches)} URLs in {sitemap_url}")
                except Exception as e:
                    logger.debug(f"Could not fetch {sitemap_url}: {e}")
        
        return urls
    
    async def discover_pages_via_search(self, page: Page) -> List[str]:
        """Discover pages using site search functionality."""
        discovered_urls = set()
        
        try:
            # Look for search button/link
            search_selectors = [
                'button[aria-label*="search" i]',
                'a[href*="search"]',
                'button:has-text("Search")',
                '[class*="search"] button',
                '[data-search]',
            ]
            
            search_button = None
            for selector in search_selectors:
                try:
                    search_button = await page.query_selector(selector)
                    if search_button and await search_button.is_visible():
                        logger.info(f"Found search button with selector: {selector}")
                        break
                except:
                    continue
            
            if not search_button:
                logger.info("No search button found, skipping search-based discovery")
                return list(discovered_urls)
            
            # Click search button
            await search_button.click()
            await page.wait_for_timeout(1000)
            
            # Try to find search input
            search_input_selectors = [
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[name*="search" i]',
                '[class*="search"] input',
            ]
            
            search_input = None
            for selector in search_input_selectors:
                try:
                    search_input = await page.query_selector(selector)
                    if search_input and await search_input.is_visible():
                        break
                except:
                    continue
            
            if not search_input:
                logger.warning("Search button found but no search input")
                return list(discovered_urls)
            
            # Perform searches for common bike-related terms
            search_terms = [
                "bike", "motorcycle", "model", "heritage", "racing",
                "desert", "diavel", "monster", "panigale", "multistrada",
                "scrambler", "streetfighter", "hypermotard", "supersport"
            ]
            
            for term in search_terms:
                try:
                    # Clear and type search term
                    await search_input.fill('')
                    await search_input.type(term, delay=100)
                    await page.wait_for_timeout(500)
                    
                    # Submit search (try Enter key or submit button)
                    await search_input.press('Enter')
                    await page.wait_for_timeout(2000)
                    
                    # Extract URLs from search results
                    result_links = await page.query_selector_all(
                        'a[href*="/bikes/"], '
                        'a[href*="/heritage/"], '
                        '.search-result a, '
                        '[class*="result"] a'
                    )
                    
                    for link in result_links:
                        try:
                            href = await link.get_attribute('href')
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                discovered_urls.add(normalized)
                        except:
                            continue
                    
                    # Go back to search page
                    await page.go_back()
                    await page.wait_for_timeout(1000)
                    
                    # Re-find search input
                    for selector in search_input_selectors:
                        search_input = await page.query_selector(selector)
                        if search_input:
                            break
                    
                except Exception as e:
                    logger.debug(f"Error searching for '{term}': {e}")
                    continue
            
            logger.info(f"Discovered {len(discovered_urls)} URLs via search")
            
        except Exception as e:
            logger.error(f"Error in search-based discovery: {e}")
        
        return list(discovered_urls)
    
    async def discover_pages_via_link_following(self, page: Page, start_url: str, max_depth: int = 2) -> Set[str]:
        """Recursively follow links from a page to discover more pages."""
        discovered = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        visited_in_this_pass = set()
        
        try:
            while to_visit:
                url, depth = to_visit.pop(0)
                
                if depth > max_depth or url in visited_in_this_pass:
                    continue
                
                visited_in_this_pass.add(url)
                
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(1000)
                    
                    # Extract all internal links
                    links = await page.query_selector_all('a[href]')
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            if href and self.is_internal_url(href):
                                full_url = urljoin(self.base_url, href)
                                normalized = self.normalize_url(full_url)
                                
                                # Look for bike-related or heritage pages
                                if any(keyword in normalized for keyword in ['/bikes/', '/heritage/', '/model']):
                                    discovered.add(normalized)
                                    if depth < max_depth:
                                        to_visit.append((normalized, depth + 1))
                        except:
                            continue
                    
                    await asyncio.sleep(self.rate_limit)
                    
                except Exception as e:
                    logger.debug(f"Error following links from {url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in link following discovery: {e}")
        
        return discovered
    
    async def post_crawl_search(self, page: Page, discovered_urls: Set[str]) -> Set[str]:
        """Post-crawl search to find any missed pages."""
        missed_urls = set()
        
        logger.info("Starting post-crawl search for missed pages...")
        
        # Extract base domain without locale
        base_domain = urlparse(self.base_url).netloc
        base_scheme = urlparse(self.base_url).scheme
        
        # Known specific URLs to check (from user requirements)
        specific_urls = [
            f"{base_scheme}://{base_domain}/ca/en/home",
            f"{base_scheme}://{base_domain}/ww/en/heritage/bikes/",
        ]
        
        # Known patterns to check
        patterns_to_check = [
            '/heritage/bikes/',
            '/heritage/',
            '/bikes/',
            '/models/',
            '/motorcycles/',
            '/home',
        ]
        
        # Check different locale patterns
        locales = ['ca/en', 'ww/en', 'us/en', 'uk/en', 'de/de', 'it/it', 'fr/fr']
        
        # First, check specific URLs mentioned by user
        for url in specific_urls:
            normalized = self.normalize_url(url)
            if normalized not in discovered_urls:
                try:
                    response = await page.goto(normalized, wait_until='domcontentloaded', timeout=10000)
                    if response and response.status < 400:
                        missed_urls.add(normalized)
                        logger.info(f"Found missed specific page: {normalized}")
                        
                        # Extract links from this page
                        await page.wait_for_timeout(1000)
                        links = await page.query_selector_all('a[href]')
                        for link in links:
                            try:
                                href = await link.get_attribute('href')
                                if href and self.is_internal_url(href):
                                    full_url = urljoin(self.base_url, href)
                                    url_normalized = self.normalize_url(full_url)
                                    if url_normalized not in discovered_urls and url_normalized not in missed_urls:
                                        # Only add bike/heritage related URLs
                                        if any(kw in url_normalized for kw in ['/bikes/', '/heritage/', '/model']):
                                            missed_urls.add(url_normalized)
                            except:
                                continue
                except Exception as e:
                    logger.debug(f"Could not access {normalized}: {e}")
        
        # Then check pattern-based URLs
        for locale in locales:
            for pattern in patterns_to_check:
                # Construct URL
                test_url = f"{base_scheme}://{base_domain}/{locale}{pattern}"
                normalized = self.normalize_url(test_url)
                
                if normalized not in discovered_urls and normalized not in missed_urls:
                    try:
                        response = await page.goto(normalized, wait_until='domcontentloaded', timeout=10000)
                        if response and response.status < 400:
                            missed_urls.add(normalized)
                            logger.info(f"Found missed pattern page: {normalized}")
                            
                            # Extract links from this page
                            await page.wait_for_timeout(1000)
                            links = await page.query_selector_all('a[href]')
                            for link in links:
                                try:
                                    href = await link.get_attribute('href')
                                    if href and self.is_internal_url(href):
                                        full_url = urljoin(self.base_url, href)
                                        url_normalized = self.normalize_url(full_url)
                                        if url_normalized not in discovered_urls and url_normalized not in missed_urls:
                                            if any(kw in url_normalized for kw in ['/bikes/', '/heritage/', '/model']):
                                                missed_urls.add(url_normalized)
                                except:
                                    continue
                    except Exception as e:
                        logger.debug(f"Could not access {normalized}: {e}")
        
        logger.info(f"Post-crawl search found {len(missed_urls)} additional pages")
        return missed_urls
    
    async def discover_bike_pages_from_dropdown(self, page: Page) -> List[Dict[str, Any]]:
        """Discover bike pages by clicking MODELS dropdown and extracting links."""
        bike_links = []
        
        try:
            # Click MODELS dropdown
            nav_handler = NavigationHandler(page)
            models_clicked = await nav_handler.click_dropdown(
                selector='a[data-js-shortcutnav=""]:has-text("MODELS")',
                wait_for_visible=True
            )
            
            if not models_clicked:
                # Try alternative selector
                models_clicked = await nav_handler.click_dropdown(
                    selector='a:has-text("MODELS")',
                    wait_for_visible=True
                )
            
            if not models_clicked:
                logger.warning("Could not click MODELS dropdown")
                return bike_links
            
            # Wait for dropdown to fully load
            await page.wait_for_timeout(1000)
            
            # Find all bike links in dropdown
            # Look for "DISCOVER MORE" / "DISCOVER IT" links
            discover_links = await page.query_selector_all(
                'a.d-button.cta[href*="/bikes/"], '
                'a[href*="/bikes/"][class*="button"], '
                'a[href*="/bikes/"][class*="cta"]'
            )
            
            for link in discover_links:
                try:
                    href = await link.get_attribute('href')
                    if href and '/bikes/' in href:
                        full_url = urljoin(self.base_url, href)
                        normalized = self.normalize_url(full_url)
                        
                        # Get bike name from surrounding context
                        bike_name = await self._extract_bike_name_from_context(link, page)
                        
                        bike_links.append({
                            'url': normalized,
                            'name': bike_name,
                            'source': 'dropdown'
                        })
                except Exception as e:
                    logger.debug(f"Error extracting link: {e}")
            
            # Also check for bike list items with links
            bike_list_items = await page.query_selector_all('li.link.-cursor')
            for item in bike_list_items:
                try:
                    # Find link within the list item
                    link = await item.query_selector('a[href*="/bikes/"]')
                    if link:
                        href = await link.get_attribute('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            normalized = self.normalize_url(full_url)
                            
                            text = await item.inner_text()
                            bike_name = self._parse_bike_name_from_text(text)
                            
                            if normalized not in [b['url'] for b in bike_links]:
                                bike_links.append({
                                    'url': normalized,
                                    'name': bike_name,
                                    'source': 'dropdown_list'
                                })
                except Exception as e:
                    logger.debug(f"Error extracting from list item: {e}")
            
            logger.info(f"Found {len(bike_links)} bike links from dropdown")
            
        except Exception as e:
            logger.error(f"Error discovering bike pages from dropdown: {e}")
        
        return bike_links
    
    async def _extract_bike_name_from_context(self, link_element, page: Page) -> str:
        """Extract bike name from context around the link."""
        try:
            # Try to find model name in nearby elements
            parent = await link_element.evaluate_handle('el => el.closest("li, div, section")')
            if parent:
                text = await parent.as_element().inner_text() if hasattr(parent, 'as_element') else None
                if text:
                    return self._parse_bike_name_from_text(text)
            
            # Fallback: extract from URL
            href = await link_element.get_attribute('href')
            if href:
                parts = href.split('/')
                if 'bikes' in parts:
                    idx = parts.index('bikes')
                    if idx + 1 < len(parts):
                        return parts[idx + 1].replace('-', ' ').title()
        except Exception as e:
            logger.debug(f"Error extracting bike name: {e}")
        
        return "Unknown"
    
    def _parse_bike_name_from_text(self, text: str) -> str:
        """Parse bike name from text content."""
        # Remove common prefixes/suffixes
        text = re.sub(r'(DISCOVER MORE|DISCOVER IT|CONFIGURATOR|CONFIGURE)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Try to extract model name (usually first significant words)
        words = text.split()
        if words:
            # Look for patterns like "DesertX", "Diavel V4 RS"
            model_parts = []
            for word in words[:5]:  # Limit to first 5 words
                if word and not word.isdigit() and len(word) > 2:
                    model_parts.append(word)
                    if len(model_parts) >= 3:  # Usually model names are 1-3 words
                        break
            if model_parts:
                return ' '.join(model_parts)
        
        return text[:50] if text else "Unknown"
    
    async def extract_page_content(self, page: Page, url: str) -> Dict[str, Any]:
        """Extract all content from a bike page."""
        content = {
            'url': url,
            'title': '',
            'description': '',
            'specifications': {},
            'features': [],
            'images': [],
            'price': None,
            'colors': [],
            'raw_html_sections': {}
        }
        
        try:
            # Wait for page to load
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Extract title
            title = await page.title()
            content['title'] = title
            
            # Extract main heading
            h1 = await page.query_selector('h1')
            if h1:
                content['title'] = await h1.inner_text()
            
            # Extract description - look for common description selectors
            desc_selectors = [
                '.description',
                '.overview',
                '.intro',
                '[class*="description"]',
                '[class*="overview"]',
                'section p',
            ]
            
            for selector in desc_selectors:
                try:
                    desc_elem = await page.query_selector(selector)
                    if desc_elem:
                        text = await desc_elem.inner_text()
                        if len(text) > 50:  # Meaningful description
                            content['description'] = text
                            break
                except:
                    continue
            
            # Extract specifications
            content['specifications'] = await self._extract_specifications(page)
            
            # Extract features
            content['features'] = await self._extract_features(page)
            
            # Extract price
            content['price'] = await self._extract_price(page)
            
            # Extract colors
            content['colors'] = await self._extract_colors(page)
            
            # Extract all images
            content['images'] = await self._extract_all_images(page)
            
            # Extract raw text from key sections for fallback parsing
            sections = await page.query_selector_all('section, .specs, .features, .gallery')
            for section in sections[:10]:  # Limit to avoid too much data
                try:
                    section_class = await section.get_attribute('class') or 'unknown'
                    section_text = await section.inner_text()
                    if section_text:
                        content['raw_html_sections'][section_class] = section_text[:1000]  # Limit length
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
        
        return content
    
    async def _extract_specifications(self, page: Page) -> Dict[str, Any]:
        """Extract specifications from the page."""
        specs = {}
        
        # Look for specification tables
        spec_tables = await page.query_selector_all('table, .specs, .specifications, [class*="spec"]')
        
        for table in spec_tables:
            try:
                rows = await table.query_selector_all('tr, .spec-row, [class*="row"]')
                for row in rows:
                    cells = await row.query_selector_all('td, th, .spec-label, .spec-value')
                    if len(cells) >= 2:
                        label = await cells[0].inner_text()
                        value = await cells[1].inner_text()
                        if label and value:
                            specs[label.strip()] = value.strip()
            except:
                continue
        
        # Also look for key-value pairs in text
        text_content = await page.inner_text('body')
        
        # Extract power, torque, weight patterns
        power_match = re.search(r'(\d+)\s*(?:hp|HP|horsepower)', text_content)
        if power_match:
            specs['power_hp'] = power_match.group(1)
        
        torque_match = re.search(r'(\d+)\s*(?:lb-ft|lb\.ft|ft-lb)', text_content)
        if torque_match:
            specs['torque_lbft'] = torque_match.group(1)
        
        weight_match = re.search(r'(\d+)\s*kg\s*(?:WET WEIGHT|wet weight)', text_content, re.IGNORECASE)
        if weight_match:
            specs['wet_weight_kg'] = weight_match.group(1)
        
        return specs
    
    async def _extract_features(self, page: Page) -> List[str]:
        """Extract features list."""
        features = []
        
        # Look for feature lists
        feature_lists = await page.query_selector_all(
            'ul.features, .feature-list, [class*="feature"] ul, li[class*="feature"]'
        )
        
        for feature_list in feature_lists:
            items = await feature_list.query_selector_all('li')
            for item in items:
                text = await item.inner_text()
                if text and len(text.strip()) > 3:
                    features.append(text.strip())
        
        return list(set(features))  # Deduplicate
    
    async def _extract_price(self, page: Page) -> Optional[Dict[str, Any]]:
        """Extract price information."""
        text_content = await page.inner_text('body')
        
        # Look for price patterns
        price_match = re.search(r'\$([\d,]+)', text_content)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            try:
                return {
                    'amount': float(price_str),
                    'currency': 'USD',
                    'region': 'US'
                }
            except:
                pass
        
        return None
    
    async def _extract_colors(self, page: Page) -> List[str]:
        """Extract available colors."""
        colors = []
        
        # Look for color swatches or color names
        color_elements = await page.query_selector_all(
            '[class*="color"], .color-swatch, [data-color]'
        )
        
        for elem in color_elements:
            try:
                color_name = await elem.get_attribute('data-color') or await elem.get_attribute('title')
                if not color_name:
                    color_name = await elem.inner_text()
                if color_name and len(color_name.strip()) > 0:
                    colors.append(color_name.strip())
            except:
                continue
        
        return list(set(colors))
    
    async def _extract_all_images(self, page: Page) -> List[Dict[str, Any]]:
        """Extract all image URLs from the page."""
        images = []
        
        # Wait for lazy-loaded images
        await page.wait_for_timeout(2000)
        
        # Find all images
        img_elements = await page.query_selector_all('img')
        
        for img in img_elements:
            try:
                # Try data-src first (lazy loading), then src
                img_url = await img.get_attribute('data-src') or await img.get_attribute('src')
                
                if img_url:
                    # Convert to full URL
                    if img_url.startswith('//'):
                        img_url = f"https:{img_url}"
                    elif img_url.startswith('/'):
                        img_url = urljoin(self.base_url, img_url)
                    elif not img_url.startswith('http'):
                        img_url = urljoin(self.base_url, img_url)
                    
                    # Filter out small images (likely icons)
                    width = await img.get_attribute('width')
                    height = await img.get_attribute('height')
                    
                    # Get alt text
                    alt = await img.get_attribute('alt') or ''
                    
                    # Get image type from context
                    img_type = 'gallery'
                    parent_class = await img.evaluate('el => el.closest("section, div")?.className || ""')
                    if 'hero' in parent_class.lower() or 'main' in parent_class.lower():
                        img_type = 'main'
                    elif 'gallery' in parent_class.lower():
                        img_type = 'gallery'
                    
                    images.append({
                        'url': img_url,
                        'alt': alt,
                        'type': img_type,
                        'width': width,
                        'height': height
                    })
            except Exception as e:
                logger.debug(f"Error extracting image: {e}")
        
        # Also check for background images in CSS
        # This is more complex and can be added later if needed
        
        return images
    
    async def download_image(
        self,
        img_url: str,
        bike_name: str,
        index: int,
        session: aiohttp.ClientSession
    ) -> Optional[str]:
        """Download an image and return local path."""
        try:
            # Check if already downloaded (by hash)
            async with session.get(img_url, timeout=30) as response:
                if response.status != 200:
                    return None
                
                image_data = await response.read()
                image_hash = hashlib.sha256(image_data).hexdigest()
                
                if image_hash in self.image_hashes:
                    logger.debug(f"Skipping duplicate image: {img_url}")
                    return None
                
                self.image_hashes.add(image_hash)
                
                # Determine file extension
                ext = 'jpg'
                if '.png' in img_url.lower():
                    ext = 'png'
                elif '.webp' in img_url.lower():
                    ext = 'webp'
                
                # Sanitize bike name for filename
                safe_name = re.sub(r'[^\w\s-]', '', bike_name).strip().replace(' ', '_')
                
                # Create filename
                filename = f"{safe_name}_{index:03d}.{ext}"
                
                # Create bike-specific directory
                bike_dir = self.images_dir / safe_name
                bike_dir.mkdir(parents=True, exist_ok=True)
                
                # Save image
                filepath = bike_dir / filename
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(image_data)
                
                logger.info(f"Downloaded image: {filename}")
                return str(filepath.relative_to(self.output_dir))
                
        except Exception as e:
            logger.error(f"Error downloading image {img_url}: {e}")
            return None
    
    def sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename."""
        # Remove special characters
        text = re.sub(r'[<>:"/\\|?*]', '_', text)
        # Replace spaces with underscores
        text = re.sub(r'\s+', '_', text)
        # Remove multiple underscores
        text = re.sub(r'_+', '_', text)
        return text.strip('_')
    
    async def create_markdown_file(self, bike_data: Dict[str, Any], image_paths: List[str]) -> str:
        """Create markdown file for a bike."""
        bike_name = self.sanitize_filename(bike_data.get('name', 'Unknown'))
        filename = f"{bike_name}.md"
        filepath = self.output_dir / filename
        
        # Calculate relative paths for images
        relative_image_paths = []
        for img_path in image_paths:
            if img_path:
                rel_path = os.path.relpath(
                    self.output_dir / img_path,
                    self.output_dir
                )
                relative_image_paths.append(rel_path)
        
        # Generate markdown content
        md_content = self._generate_markdown(bike_data, relative_image_paths)
        
        # Write file
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(md_content)
        
        logger.info(f"Created markdown file: {filename}")
        return str(filepath)
    
    def _generate_markdown(self, bike_data: Dict[str, Any], image_paths: List[str]) -> str:
        """Generate markdown content from bike data."""
        lines = []
        
        # Title
        title = bike_data.get('title') or bike_data.get('name', 'Unknown Bike')
        lines.append(f"# {title}\n")
        
        # Overview
        if bike_data.get('description'):
            lines.append("## Overview\n")
            lines.append(f"{bike_data['description']}\n")
        
        # Specifications
        if bike_data.get('specifications'):
            lines.append("## Specifications\n")
            for key, value in bike_data['specifications'].items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        # Features
        if bike_data.get('features'):
            lines.append("## Features\n")
            for feature in bike_data['features']:
                lines.append(f"- {feature}")
            lines.append("")
        
        # Price
        if bike_data.get('price'):
            price = bike_data['price']
            lines.append("## Price\n")
            lines.append(f"- **Amount**: ${price.get('amount', 'N/A')}")
            lines.append(f"- **Currency**: {price.get('currency', 'USD')}")
            lines.append(f"- **Region**: {price.get('region', 'US')}\n")
        
        # Colors
        if bike_data.get('colors'):
            lines.append("## Colors\n")
            for color in bike_data['colors']:
                lines.append(f"- {color}")
            lines.append("")
        
        # Images
        if image_paths:
            lines.append("## Images\n")
            for img_path in image_paths:
                img_name = Path(img_path).name
                lines.append(f"![{img_name}]({img_path})")
            lines.append("")
        
        # Source
        lines.append("## Source Information\n")
        lines.append(f"- **Source URL**: {bike_data.get('url', 'N/A')}")
        lines.append(f"- **Extracted**: {datetime.now().isoformat()}\n")
        
        return "\n".join(lines)
    
    async def crawl(self):
        """Main crawl function."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True for production
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Step 1: Navigate to base URL
                logger.info(f"Navigating to {self.base_url}")
                await page.goto(self.base_url, wait_until='domcontentloaded')
                
                # Step 2: Handle cookie consent
                cookie_handler = CookieHandler(page)
                await cookie_handler.accept_cookies(custom_selector="#onetrust-accept-btn-handler")
                await page.wait_for_timeout(1000)
                
                # Step 3: Check sitemap
                logger.info("Checking sitemap...")
                sitemap_urls = await self.check_sitemap()
                logger.info(f"Found {len(sitemap_urls)} URLs in sitemap")
                
                # Step 4: Discover bike pages from dropdown
                logger.info("Discovering bike pages from MODELS dropdown...")
                bike_links = await self.discover_bike_pages_from_dropdown(page)
                
                # Step 5: Discover pages via search
                logger.info("Discovering pages via site search...")
                search_urls = await self.discover_pages_via_search(page)
                logger.info(f"Found {len(search_urls)} URLs via search")
                
                # Step 6: Follow links from key pages (heritage, etc.)
                logger.info("Following links from key pages...")
                heritage_url = f"{self.base_url}/ww/en/heritage/bikes/"
                link_following_urls = await self.discover_pages_via_link_following(
                    page, 
                    heritage_url, 
                    max_depth=2
                )
                logger.info(f"Found {len(link_following_urls)} URLs via link following")
                
                # Combine all discovered URLs
                all_bike_urls = set()
                
                # Add dropdown links
                for link in bike_links:
                    all_bike_urls.add(link['url'])
                
                # Add sitemap URLs (filter for bike/heritage pages)
                for url in sitemap_urls:
                    if any(keyword in url for keyword in ['/bikes/', '/heritage/', '/model']):
                        all_bike_urls.add(url)
                
                # Add search URLs
                all_bike_urls.update(search_urls)
                
                # Add link-following URLs
                all_bike_urls.update(link_following_urls)
                
                logger.info(f"Total unique pages discovered: {len(all_bike_urls)}")
                
                # Step 5: Crawl each bike page
                async with aiohttp.ClientSession() as session:
                    for i, bike_url in enumerate(all_bike_urls, 1):
                        if bike_url in self.visited_urls:
                            logger.info(f"Skipping already visited: {bike_url}")
                            continue
                        
                        logger.info(f"[{i}/{len(all_bike_urls)}] Crawling: {bike_url}")
                        
                        try:
                            await page.goto(bike_url, wait_until='domcontentloaded', timeout=30000)
                            await page.wait_for_timeout(2000)  # Wait for dynamic content
                            
                            # Extract content
                            content = await self.extract_page_content(page, bike_url)
                            
                            # Get bike name from URL or content
                            bike_name = content.get('title') or self._extract_name_from_url(bike_url)
                            
                            # Download images
                            image_paths = []
                            for idx, img_info in enumerate(content.get('images', [])):
                                img_path = await self.download_image(
                                    img_info['url'],
                                    bike_name,
                                    idx,
                                    session
                                )
                                if img_path:
                                    image_paths.append(img_path)
                                
                                # Rate limit image downloads
                                await asyncio.sleep(0.5)
                            
                            # Create markdown file
                            bike_data = {
                                'name': bike_name,
                                'url': bike_url,
                                **content
                            }
                            
                            await self.create_markdown_file(bike_data, image_paths)
                            
                            # Mark as visited
                            self.visited_urls.add(bike_url)
                            self.bike_pages.append(bike_data)
                            
                            # Save state periodically
                            if i % 5 == 0:
                                self.save_state()
                            
                            # Rate limit
                            await asyncio.sleep(self.rate_limit)
                            
                        except Exception as e:
                            logger.error(f"Error crawling {bike_url}: {e}")
                            continue
                
                # Step 6: Post-crawl search for missed pages
                logger.info("Starting post-crawl search for missed pages...")
                missed_urls = await self.post_crawl_search(page, all_bike_urls)
                
                if missed_urls:
                    logger.info(f"Found {len(missed_urls)} missed pages, crawling them now...")
                    
                    # Crawl missed pages
                    async with aiohttp.ClientSession() as session:
                        for i, missed_url in enumerate(missed_urls, 1):
                            if missed_url in self.visited_urls:
                                continue
                            
                            logger.info(f"[Missed {i}/{len(missed_urls)}] Crawling: {missed_url}")
                            
                            try:
                                await page.goto(missed_url, wait_until='domcontentloaded', timeout=30000)
                                await page.wait_for_timeout(2000)
                                
                                # Extract content
                                content = await self.extract_page_content(page, missed_url)
                                
                                # Get bike name from URL or content
                                bike_name = content.get('title') or self._extract_name_from_url(missed_url)
                                
                                # Download images
                                image_paths = []
                                for idx, img_info in enumerate(content.get('images', [])):
                                    img_path = await self.download_image(
                                        img_info['url'],
                                        bike_name,
                                        idx,
                                        session
                                    )
                                    if img_path:
                                        image_paths.append(img_path)
                                    await asyncio.sleep(0.5)
                                
                                # Create markdown file
                                bike_data = {
                                    'name': bike_name,
                                    'url': missed_url,
                                    **content
                                }
                                
                                await self.create_markdown_file(bike_data, image_paths)
                                
                                # Mark as visited
                                self.visited_urls.add(missed_url)
                                self.bike_pages.append(bike_data)
                                
                                await asyncio.sleep(self.rate_limit)
                                
                            except Exception as e:
                                logger.error(f"Error crawling missed page {missed_url}: {e}")
                                continue
                
                # Final state save
                self.save_state()
                logger.info(f"Crawl complete! Processed {len(self.bike_pages)} pages total")
                logger.info(f"Total unique URLs discovered: {len(self.visited_urls)}")
                
            finally:
                await browser.close()
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract bike name from URL."""
        parts = url.split('/')
        if 'bikes' in parts:
            idx = parts.index('bikes')
            if idx + 1 < len(parts):
                name = parts[idx + 1].replace('-', ' ').title()
                return name
        return "Unknown"


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Full-site motorcycle crawler")
    parser.add_argument("url", help="Base URL of the motorcycle OEM website")
    parser.add_argument(
        "--output-dir",
        default="/mnt/seagate4tb/moto-scraper-v1",
        help="Output directory for markdown files and images"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=2.0,
        help="Seconds to wait between requests"
    )
    
    args = parser.parse_args()
    
    # Ensure URL has protocol
    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    crawler = SiteCrawler(
        base_url=url,
        output_dir=args.output_dir,
        rate_limit=args.rate_limit
    )
    
    await crawler.crawl()


if __name__ == "__main__":
    asyncio.run(main())

