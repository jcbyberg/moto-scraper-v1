"""
Image Extractor for motorcycle OEM web-crawler.

Extracts and filters relevant images from bike pages.
"""

import asyncio
from typing import List, Dict, Any
from urllib.parse import urljoin
from playwright.async_api import Page
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ImageExtractor:
    """
    Extract all relevant images from bike pages.
    """

    def __init__(self):
        """Initialize image extractor."""
        # Minimum image dimensions (filter out small icons/logos)
        self.min_width = 200
        self.min_height = 200

        # Patterns to exclude (logos, icons, UI elements)
        self.exclude_patterns = [
            'logo',
            'icon',
            'favicon',
            'sprite',
            'button',
            'arrow',
            'social',
            'badge',
        ]

    async def extract_images(
        self,
        page: Page,
        model: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """
        Extract all relevant images from page.

        Args:
            page: Playwright page object
            model: Bike model name
            year: Model year

        Returns:
            List of image dicts with url, alt, type, dimensions
        """
        images = []

        # Wait for lazy-loaded images
        await page.wait_for_timeout(2000)
        
        # Expand accordions to reveal hidden images
        await self._expand_accordions(page)
        
        # Navigate carousels/sliders to reveal all images
        await self._navigate_carousels(page)
        
        # Scroll to trigger lazy loading
        await self.wait_for_lazy_images(page)

        # Find all img elements
        img_elements = await page.query_selector_all('img')
        
        # Also find images in picture elements
        picture_elements = await page.query_selector_all('picture')
        
        # Extract video poster images and video URLs
        video_elements = await page.query_selector_all('video')

        for img in img_elements:
            try:
                img_info = await self._extract_image_info(img, page)
                if img_info:
                    images.append(img_info)
            except Exception as e:
                logger.debug(f"Error extracting image: {e}")
                continue
        
        # Extract images from picture elements
        try:
            found_urls = {img['url'] for img in images if img and img.get('url')}
            
            for picture in picture_elements:
                try:
                    # Look for img inside picture
                    img_in_picture = await picture.query_selector('img')
                    if img_in_picture:
                        img_info = await self._extract_image_info(img_in_picture, page)
                        if img_info and img_info.get('url') and img_info['url'] not in found_urls:
                            images.append(img_info)
                            found_urls.add(img_info['url'])
                    
                    # Also check for source elements with srcset
                    sources = await picture.query_selector_all('source')
                    for source in sources:
                        try:
                            srcset = await source.get_attribute('srcset')
                            if srcset:
                                # Extract URL from srcset
                                urls = srcset.split(',')
                                if urls:
                                    img_url = urls[-1].strip().split()[0]  # Get highest res URL
                                    if img_url and img_url not in found_urls:
                                        # Convert to full URL if needed
                                        if img_url.startswith('//'):
                                            img_url = f"https:{img_url}"
                                        elif img_url.startswith('/'):
                                            img_url = urljoin(page.url, img_url)
                                        elif not img_url.startswith('http'):
                                            img_url = urljoin(page.url, img_url)
                                        
                                        images.append({
                                            'url': img_url,
                                            'alt': '',
                                            'type': 'gallery',
                                            'width': None,
                                            'height': None
                                        })
                                        found_urls.add(img_url)
                        except Exception as e:
                            logger.debug(f"Error extracting from source element: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Error extracting from picture element: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Error extracting images from picture elements: {e}")
        
        # Also check for images in div.card elements (Ducati-specific structure)
        # These divs might contain img elements or have background images
        try:
            # Track URLs we've already found to avoid duplicates
            found_urls = {img['url'] for img in images if img and img.get('url')}
            
            card_divs = await page.query_selector_all('div.card')
            for card in card_divs:
                # Look for img elements within the card
                card_imgs = await card.query_selector_all('img')
                for img in card_imgs:
                    try:
                        img_info = await self._extract_image_info(img, page)
                        if img_info and img_info.get('url') and img_info['url'] not in found_urls:
                            images.append(img_info)
                            found_urls.add(img_info['url'])
                    except Exception as e:
                        logger.debug(f"Error extracting image from card: {e}")
                        continue
        except Exception as e:
            logger.debug(f"Error extracting images from card divs: {e}")
        
        # Also check for images in section.body elements (story pages)
        try:
            found_urls = {img['url'] for img in images if img and img.get('url')}
            
            body_sections = await page.query_selector_all('section.body')
            for section in body_sections:
                # Look for img elements within the section
                section_imgs = await section.query_selector_all('img')
                for img in section_imgs:
                    try:
                        img_info = await self._extract_image_info(img, page)
                        if img_info and img_info.get('url') and img_info['url'] not in found_urls:
                            images.append(img_info)
                            found_urls.add(img_info['url'])
                    except Exception as e:
                        logger.debug(f"Error extracting image from section.body: {e}")
                        continue
        except Exception as e:
            logger.debug(f"Error extracting images from section.body: {e}")
        
        # Extract video poster images and video URLs
        try:
            found_urls = {img['url'] for img in images if img and img.get('url')}
            
            for video in video_elements:
                try:
                    # Get poster image (thumbnail)
                    poster = await video.get_attribute('poster')
                    if poster:
                        # Convert to full URL if needed
                        if poster.startswith('//'):
                            poster = f"https:{poster}"
                        elif poster.startswith('/'):
                            poster = urljoin(page.url, poster)
                        elif not poster.startswith('http'):
                            poster = urljoin(page.url, poster)
                        
                        if poster not in found_urls:
                            images.append({
                                'url': poster,
                                'alt': 'Video poster',
                                'type': 'video_poster',
                                'width': None,
                                'height': None
                            })
                            found_urls.add(poster)
                    
                    # Get video source URL
                    video_src = await video.get_attribute('src')
                    if not video_src:
                        # Check for source elements inside video
                        source = await video.query_selector('source')
                        if source:
                            video_src = await source.get_attribute('src')
                    
                    if video_src:
                        # Convert to full URL if needed
                        if video_src.startswith('//'):
                            video_src = f"https:{video_src}"
                        elif video_src.startswith('/'):
                            video_src = urljoin(page.url, video_src)
                        elif not video_src.startswith('http'):
                            video_src = urljoin(page.url, video_src)
                        
                        # Store video URL (we'll add it to a separate videos list in data)
                        # For now, we can note it in the image metadata
                        logger.debug(f"Found video: {video_src}")
                except Exception as e:
                    logger.debug(f"Error extracting video info: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Error extracting videos: {e}")
        
        # Extract background images from div.bg[data-bg]
        try:
            found_urls = {img['url'] for img in images if img and img.get('url')}
            
            bg_divs = await page.query_selector_all('div.bg[data-bg], div[data-bg]')
            for bg_div in bg_divs:
                try:
                    bg_url = await bg_div.get_attribute('data-bg')
                    if bg_url:
                        # Convert to full URL if needed
                        if bg_url.startswith('//'):
                            bg_url = f"https:{bg_url}"
                        elif bg_url.startswith('/'):
                            bg_url = urljoin(page.url, bg_url)
                        elif not bg_url.startswith('http'):
                            bg_url = urljoin(page.url, bg_url)
                        
                        if bg_url not in found_urls:
                            images.append({
                                'url': bg_url,
                                'alt': 'Background image',
                                'type': 'background',
                                'width': None,
                                'height': None
                            })
                            found_urls.add(bg_url)
                except Exception as e:
                    logger.debug(f"Error extracting background image: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Error extracting background images: {e}")

        # Filter relevant images
        relevant_images = self.filter_relevant_images(images, model)

        logger.info(f"Extracted {len(relevant_images)} relevant images (filtered from {len(images)})")
        return relevant_images

    async def _extract_image_info(self, img, page: Page) -> Dict[str, Any]:
        """Extract information from an image element."""
        # Try data-src first (lazy loading), then src
        img_url = await img.get_attribute('data-src')
        
        # Try data-srcset (lazy loading with responsive images)
        if not img_url:
            data_srcset = await img.get_attribute('data-srcset')
            if data_srcset:
                # Extract the largest/highest quality URL from srcset
                # Format: "url1 size1, url2 size2, ..." or "url1 1x, url2 2x"
                urls = data_srcset.split(',')
                if urls:
                    # Take the last URL (usually highest resolution) or first if only one
                    last_url = urls[-1].strip().split()[0]  # Get URL part before size descriptor
                    img_url = last_url
        
        # Try srcset attribute
        if not img_url:
            srcset = await img.get_attribute('srcset')
            if srcset:
                # Extract the largest/highest quality URL from srcset
                urls = srcset.split(',')
                if urls:
                    # Take the last URL (usually highest resolution) or first if only one
                    last_url = urls[-1].strip().split()[0]  # Get URL part before size descriptor
                    img_url = last_url
        
        # Fallback to src attribute
        if not img_url:
            img_url = await img.get_attribute('src')
        
        # Fallback to data-src (alternative lazy loading attribute)
        if not img_url:
            img_url = await img.get_attribute('data-src')

        if not img_url:
            return None

        # Convert to full URL
        if img_url.startswith('//'):
            img_url = f"https:{img_url}"
        elif img_url.startswith('/'):
            base_url = page.url
            img_url = urljoin(base_url, img_url)
        elif not img_url.startswith('http'):
            base_url = page.url
            img_url = urljoin(base_url, img_url)

        # Get alt text
        alt = await img.get_attribute('alt') or ''

        # Get dimensions
        width = await img.get_attribute('width')
        height = await img.get_attribute('height')

        # Try to get actual rendered dimensions if attributes not present
        if not width or not height:
            try:
                box = await img.bounding_box()
                if box:
                    width = str(int(box['width']))
                    height = str(int(box['height']))
            except:
                pass

        # Determine image type from context
        img_type = await self._determine_image_type(img)

        return {
            'url': img_url,
            'alt': alt,
            'type': img_type,
            'width': width,
            'height': height
        }

    async def _determine_image_type(self, img) -> str:
        """Determine image type from surrounding context."""
        try:
            # Get parent classes
            parent_class = await img.evaluate('el => el.closest("section, div")?.className || ""')

            parent_class_lower = parent_class.lower() if parent_class else ""

            if 'hero' in parent_class_lower or 'main' in parent_class_lower:
                return 'main'
            elif 'gallery' in parent_class_lower:
                return 'gallery'
            elif 'detail' in parent_class_lower or 'feature' in parent_class_lower:
                return 'detail'
            elif 'spec' in parent_class_lower or 'technical' in parent_class_lower:
                return 'specs'
            else:
                return 'gallery'  # Default
        except:
            return 'gallery'

    def filter_relevant_images(
        self,
        images: List[Dict[str, Any]],
        model: str
    ) -> List[Dict[str, Any]]:
        """
        Filter out non-bike images (logos, icons, UI elements).

        Args:
            images: List of image dicts
            model: Model name for context

        Returns:
            Filtered list of relevant images
        """
        relevant = []

        for img in images:
            # Filter by URL patterns (exclude logos, icons, etc.)
            url_lower = img['url'].lower()
            if any(pattern in url_lower for pattern in self.exclude_patterns):
                continue

            # Filter by alt text (exclude UI elements)
            alt_lower = img.get('alt', '').lower()
            if any(pattern in alt_lower for pattern in self.exclude_patterns):
                continue

            # Filter by dimensions
            try:
                width = int(img.get('width', 0))
                height = int(img.get('height', 0))

                if width > 0 and height > 0:
                    if width < self.min_width or height < self.min_height:
                        continue
            except (ValueError, TypeError):
                # If we can't parse dimensions, include it anyway
                pass

            relevant.append(img)

        return relevant

    async def _expand_accordions(self, page: Page) -> None:
        """
        Expand accordion sections to reveal hidden images and content.
        
        Args:
            page: Playwright page object
        """
        try:
            # Find accordion triggers
            accordion_selectors = [
                'dt[data-js-accordiontoggle-trigger]',
                '[data-js-accordiontoggle-trigger]',
                '[class*="accordion"] [class*="trigger"]',
                '[class*="accordion"] [class*="toggle"]',
                'dt.term',
                '[role="button"][aria-expanded="false"]',
            ]
            
            for selector in accordion_selectors:
                try:
                    accordion_triggers = await page.query_selector_all(selector)
                    logger.debug(f"Found {len(accordion_triggers)} accordion triggers with selector: {selector}")
                    
                    for trigger in accordion_triggers:
                        try:
                            # Check if already expanded
                            aria_expanded = await trigger.get_attribute('aria-expanded')
                            if aria_expanded == 'true':
                                continue
                            
                            # Check if visible
                            is_visible = await trigger.is_visible()
                            if not is_visible:
                                continue
                            
                            # Scroll into view
                            await trigger.scroll_into_view_if_needed()
                            await asyncio.sleep(0.3)
                            
                            # Click to expand
                            await trigger.click()
                            await asyncio.sleep(1)  # Wait for content to load
                            
                            logger.debug(f"Expanded accordion: {await trigger.inner_text()[:50]}")
                        except Exception as e:
                            logger.debug(f"Error expanding accordion: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Error with accordion selector {selector}: {e}")
                    continue
            
            # Wait a bit for all accordion content to load
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            logger.debug(f"Error expanding accordions: {e}")

    async def _navigate_carousels(self, page: Page) -> None:
        """
        Navigate through carousels/sliders to reveal all images.
        Clicks arrow buttons and drags sliders to access hidden images.
        
        Args:
            page: Playwright page object
        """
        try:
            # Find carousel containers
            carousel_selectors = [
                '[class*="carousel"]',
                '[class*="slider"]',
                '[class*="swiper"]',
                '.card.-withzoom',  # Ducati-specific carousel cards
            ]
            
            for selector in carousel_selectors:
                try:
                    carousels = await page.query_selector_all(selector)
                    if not carousels:
                        continue
                    
                    logger.debug(f"Found {len(carousels)} carousel elements with selector: {selector}")
                    
                    for carousel in carousels:
                        # Try to find arrow buttons
                        arrow_selectors = [
                            'button[aria-label*="next" i]',
                            'button[aria-label*="right" i]',
                            'button[aria-label*="forward" i]',
                            '[class*="arrow"][class*="next"]',
                            '[class*="arrow"][class*="right"]',
                            '.arrow-right',
                            '.next',
                            '[data-direction="next"]',
                            '[data-action="next"]',
                        ]
                        
                        # Try clicking next arrow multiple times to reveal all images
                        for arrow_selector in arrow_selectors:
                            try:
                                arrow = await carousel.query_selector(arrow_selector)
                                if not arrow:
                                    # Try finding arrow in parent container or page level
                                    arrow = await page.query_selector(arrow_selector)
                                
                                if arrow:
                                    visible = await arrow.is_visible()
                                    if visible:
                                        # Click arrow multiple times to navigate through carousel
                                        for i in range(10):  # Max 10 clicks per carousel
                                            try:
                                                # Check if arrow is still visible and enabled
                                                is_visible = await arrow.is_visible()
                                                is_enabled = await arrow.is_enabled()
                                                
                                                if not is_visible or not is_enabled:
                                                    break
                                                
                                                # Scroll arrow into view
                                                await arrow.scroll_into_view_if_needed()
                                                await asyncio.sleep(0.3)
                                                
                                                # Click arrow
                                                await arrow.click()
                                                await asyncio.sleep(1)  # Wait for image to load
                                                
                                                logger.debug(f"Clicked carousel arrow {i+1} times")
                                            except Exception as e:
                                                logger.debug(f"Error clicking carousel arrow: {e}")
                                                break
                                        
                                        break  # Found working arrow, move to next carousel
                            except Exception as e:
                                logger.debug(f"Error with arrow selector {arrow_selector}: {e}")
                                continue
                        
                        # Also try dragging the carousel (for touch-enabled sliders)
                        try:
                            box = await carousel.bounding_box()
                            if box:
                                # Simulate drag/swipe right
                                await page.mouse.move(
                                    box['x'] + box['width'] * 0.2,
                                    box['y'] + box['height'] / 2
                                )
                                await page.mouse.down()
                                await asyncio.sleep(0.1)
                                await page.mouse.move(
                                    box['x'] + box['width'] * 0.8,
                                    box['y'] + box['height'] / 2
                                )
                                await asyncio.sleep(0.1)
                                await page.mouse.up()
                                await asyncio.sleep(1)
                                
                                logger.debug("Dragged carousel to reveal images")
                        except Exception as e:
                            logger.debug(f"Error dragging carousel: {e}")
                            
                except Exception as e:
                    logger.debug(f"Error processing carousel with selector {selector}: {e}")
                    continue
            
            # Wait a bit for all images to load after carousel navigation
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            logger.debug(f"Error navigating carousels: {e}")

    async def wait_for_lazy_images(self, page: Page) -> None:
        """
        Wait for lazy-loaded images to load.

        Args:
            page: Playwright page object
        """
        try:
            # Scroll to bottom to trigger lazy loading
            await page.evaluate("""
                () => {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            """)
            await page.wait_for_timeout(1000)

            # Scroll back to top
            await page.evaluate("""
                () => {
                    window.scrollTo(0, 0);
                }
            """)
            await page.wait_for_timeout(1000)

            # Wait for any images with loading="lazy" attribute
            await page.wait_for_load_state('networkidle', timeout=5000)

        except Exception as e:
            logger.debug(f"Error waiting for lazy images: {e}")
