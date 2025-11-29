"""
Data Extractor for motorcycle OEM web-crawler.

Extracts specifications, features, descriptions, colors, and pricing from pages.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from playwright.async_api import Page
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataExtractor:
    """
    Extract all available data from bike pages.
    """

    def __init__(self):
        """Initialize data extractor."""
        # Common specification table selectors
        self.spec_table_selectors = [
            'table.specifications',
            'table.tech-specs',
            '.specifications table',
            '.spec-table',
            '[class*="spec"] table',
            'table[class*="technical"]',
        ]

        # Common feature list selectors
        self.feature_selectors = [
            'ul.features',
            '.feature-list',
            '[class*="feature"] ul',
            '.features li',
        ]

    async def extract_from_page(
        self,
        page: Page,
        page_type: str
    ) -> Dict[str, Any]:
        """
        Extract all available data from a page.

        Args:
            page: Playwright page object
            page_type: Type of page ('main', 'specs', 'gallery', 'features')

        Returns:
            Dict with extracted data
        """
        data = {
            'specifications': {},
            'features': [],
            'description': '',
            'colors': [],
            'price': None,
            'content_sections': {},  # Ducati-specific content sections (includes tooltips, top, etc.)
        }

        try:
            # Extract based on page type
            if page_type in ['specs', 'main', 'insights']:
                data['specifications'] = await self.extract_specifications(page)

            if page_type in ['features', 'main', 'insights']:
                data['features'] = await self.extract_features(page)

            if page_type in ['main', 'insights', 'stories']:
                data['description'] = await self.extract_description(page)
                data['colors'] = await self.extract_colors(page)
                data['price'] = await self.extract_pricing(page)
                
                # Extract Ducati-specific content sections
                data['content_sections'] = await self.extract_content_sections(page)
            
            # Handle insights pages with tabs
            if page_type == 'insights':
                await self._handle_insights_tabs(page, data)
            
            # Handle stories/travel pages
            if page_type == 'stories':
                # Stories pages may have additional content
                await self._extract_story_content(page, data)

        except Exception as e:
            logger.error(f"Error extracting data: {e}")

        return data

    async def extract_specifications(self, page: Page) -> Dict[str, Any]:
        """
        Extract specification tables/data.

        Args:
            page: Playwright page object

        Returns:
            Dict of specification key-value pairs
        """
        specs = {}

        # Strategy 1: Try to find spec tables
        for selector in self.spec_table_selectors:
            try:
                tables = await page.query_selector_all(selector)
                for table in tables:
                    table_specs = await self._extract_table_specs(table)
                    specs.update(table_specs)
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue

        # Strategy 2: Look for dl/dt/dd patterns
        try:
            dl_elements = await page.query_selector_all('dl')
            for dl in dl_elements:
                dl_specs = await self._extract_dl_specs(dl)
                specs.update(dl_specs)
        except Exception as e:
            logger.debug(f"Error extracting dl specs: {e}")
        
        # Strategy 2b: Extract from dl.list (Ducati-specific format)
        try:
            dl_lists = await page.query_selector_all('dl.list')
            for dl_list in dl_lists:
                text = await dl_list.inner_text()
                if text:
                    # Parse specs from text like "DISPLACEMENT 890 cc POWER 120,4 hp..."
                    list_specs = self._extract_specs_from_dl_list(text)
                    specs.update(list_specs)
        except Exception as e:
            logger.debug(f"Error extracting dl.list specs: {e}")

        # Strategy 3: Extract from d-table-responsive (Ducati heritage pages)
        try:
            table_responsive = await page.query_selector_all('div.d-table-responsive')
            for div in table_responsive:
                text = await div.inner_text()
                if text:
                    # Parse specs from text like "Displacement 98 cc Maximum power 9 hp at 9000 rpm..."
                    responsive_specs = self._extract_specs_from_table_responsive(text)
                    specs.update(responsive_specs)
        except Exception as e:
            logger.debug(f"Error extracting d-table-responsive specs: {e}")

        # Strategy 4: Extract from text patterns
        try:
            body_text = await page.inner_text('body')
            text_specs = self._extract_specs_from_text(body_text)
            specs.update(text_specs)
        except Exception as e:
            logger.debug(f"Error extracting text specs: {e}")

        logger.info(f"Extracted {len(specs)} specifications")
        return specs

    async def _extract_table_specs(self, table) -> Dict[str, str]:
        """Extract specs from an HTML table."""
        specs = {}

        try:
            rows = await table.query_selector_all('tr')
            for row in rows:
                cells = await row.query_selector_all('td, th')
                if len(cells) >= 2:
                    label = await cells[0].inner_text()
                    value = await cells[1].inner_text()
                    if label and value:
                        specs[label.strip()] = value.strip()
        except Exception as e:
            logger.debug(f"Error extracting table specs: {e}")

        return specs

    async def _extract_dl_specs(self, dl) -> Dict[str, str]:
        """Extract specs from definition list (dl/dt/dd)."""
        specs = {}

        try:
            dts = await dl.query_selector_all('dt')
            dds = await dl.query_selector_all('dd')

            for dt, dd in zip(dts, dds):
                label = await dt.inner_text()
                value = await dd.inner_text()
                if label and value:
                    specs[label.strip()] = value.strip()
        except Exception as e:
            logger.debug(f"Error extracting dl specs: {e}")

        return specs
    
    def _extract_specs_from_dl_list(self, text: str) -> Dict[str, str]:
        """
        Extract specs from dl.list text format.
        Format: "DISPLACEMENT 890 cc (54,3 cu in) POWER 120,4 hp (88,5 kW) @ 10.750 rpm..."
        """
        specs = {}
        
        # Pattern to match "LABEL value unit (alternative) additional_info"
        # Examples: "DISPLACEMENT 890 cc (54,3 cu in)", "POWER 120,4 hp (88,5 kW) @ 10.750 rpm"
        pattern = r'([A-Z][A-Z\s]+?)\s+(\d+(?:[.,]\d+)?)\s+([a-zA-Z/]+(?:\s*\([^)]+\))?(?:\s+@\s+\d+[^A-Z]*)?)'
        
        matches = re.finditer(pattern, text)
        for match in matches:
            label = match.group(1).strip()
            value = match.group(2)
            unit = match.group(3).strip()
            
            # Normalize label (remove extra spaces)
            label_normalized = re.sub(r'\s+', ' ', label).strip()
            
            # Store as "Label: value unit"
            specs[label_normalized] = f"{value} {unit}"
        
        return specs

    def _extract_specs_from_table_responsive(self, text: str) -> Dict[str, str]:
        """
        Extract specs from d-table-responsive div text.
        Format: "Displacement 98 cc Maximum power 9 hp at 9000 rpm Maximum speed 115 km/h Dry weight 80 Kg"
        """
        specs = {}
        
        # Pattern to match "Label value unit" or "Label value unit additional_info"
        # Examples: "Displacement 98 cc", "Maximum power 9 hp at 9000 rpm"
        pattern = r'([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?)\s+([a-zA-Z/]+(?:\s+at\s+\d+\s+[a-zA-Z/]+)?)'
        
        matches = re.finditer(pattern, text)
        for match in matches:
            label = match.group(1).strip()
            value = match.group(2)
            unit = match.group(3).strip()
            
            # Normalize label
            label_normalized = label.strip()
            
            # Store as "Label: value unit"
            specs[label_normalized] = f"{value} {unit}"
        
        return specs

    def _extract_specs_from_text(self, text: str) -> Dict[str, str]:
        """Extract common specs from text using regex patterns."""
        specs = {}

        # Power patterns
        power_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hp|HP|horsepower|bhp|kW)', text)
        if power_match:
            specs['Power'] = power_match.group(0)

        # Torque patterns
        torque_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lb-ft|lb\.ft|ft-lb|Nm|N-m)', text)
        if torque_match:
            specs['Torque'] = torque_match.group(0)

        # Weight patterns
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|lbs|pounds)\s*(?:wet|dry)?\s*(?:weight)?', text, re.IGNORECASE)
        if weight_match:
            specs['Weight'] = weight_match.group(0)

        # Displacement patterns
        displacement_match = re.search(r'(\d+)\s*(?:cc|cm³|cm3)', text, re.IGNORECASE)
        if displacement_match:
            specs['Displacement'] = displacement_match.group(0)

        # Fuel capacity
        fuel_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:L|liters|litres|gallons)\s*(?:fuel|tank)?', text, re.IGNORECASE)
        if fuel_match:
            specs['Fuel Capacity'] = fuel_match.group(0)

        return specs

    async def extract_features(self, page: Page) -> List[str]:
        """
        Extract feature list.

        Args:
            page: Playwright page object

        Returns:
            List of feature strings
        """
        features = []

        # Try common feature list patterns
        for selector in self.feature_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.inner_text()
                    if text and len(text.strip()) > 3:
                        features.append(text.strip())
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue

        # Also look for bullet points with feature-like content
        try:
            bullets = await page.query_selector_all('li')
            for bullet in bullets:
                text = await bullet.inner_text()
                # Features are usually short descriptive phrases
                if text and 10 < len(text.strip()) < 200:
                    # Check if it looks like a feature (not navigation, etc.)
                    if not any(skip in text.lower() for skip in ['home', 'about', 'contact', 'menu']):
                        features.append(text.strip())
        except Exception as e:
            logger.debug(f"Error extracting bullet features: {e}")

        # Deduplicate while preserving order
        seen = set()
        unique_features = []
        for feature in features:
            if feature not in seen:
                seen.add(feature)
                unique_features.append(feature)

        logger.info(f"Extracted {len(unique_features)} features")
        return unique_features[:50]  # Limit to top 50

    async def extract_description(self, page: Page) -> str:
        """
        Extract main description text.

        Args:
            page: Playwright page object

        Returns:
            Description string
        """
        description = ""

        # Try common description selectors
        desc_selectors = [
            '.description',
            '.overview',
            '.intro',
            '[class*="description"]',
            '[class*="overview"]',
            'section p',
            '.content p',
            'p.description',  # Ducati-specific
        ]

        for selector in desc_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    if len(text) > len(description):
                        description = text
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue

        # Fallback: get first substantial paragraph
        if not description or len(description) < 50:
            try:
                paragraphs = await page.query_selector_all('p')
                for p in paragraphs:
                    text = await p.inner_text()
                    if len(text) > 100:  # Substantial paragraph
                        description = text
                        break
            except Exception as e:
                logger.debug(f"Error extracting paragraphs: {e}")
        
        # Also extract accordion content (dt.term and following p elements)
        try:
            accordion_content = await self._extract_accordion_content(page)
            if accordion_content:
                if description:
                    description += '\n\n' + accordion_content
                else:
                    description = accordion_content
        except Exception as e:
            logger.debug(f"Error extracting accordion content: {e}")

        return description.strip()
    
    async def _extract_accordion_content(self, page: Page) -> str:
        """
        Extract content from accordion sections (dt.term and following p elements).
        
        Args:
            page: Playwright page object
            
        Returns:
            Combined accordion content text
        """
        accordion_texts = []
        
        try:
            # Find all accordion terms (triggers)
            accordion_terms = await page.query_selector_all('dt.term, dt[data-js-accordiontoggle-trigger]')
            
            for term in accordion_terms:
                try:
                    # Get term text
                    term_text = await term.inner_text()
                    if term_text and len(term_text.strip()) > 3:
                        # Find following p elements (accordion content)
                        # Use evaluate to find next sibling p elements
                        content_texts = await term.evaluate('''
                            (el) => {
                                const contents = [];
                                let next = el.nextElementSibling;
                                while (next && (next.tagName === 'P' || next.tagName === 'DD')) {
                                    const text = next.innerText?.trim();
                                    if (text && text.length > 10) {
                                        contents.push(text);
                                    }
                                    next = next.nextElementSibling;
                                }
                                return contents;
                            }
                        ''')
                        
                        if content_texts:
                            # Combine term and content
                            accordion_item = f"{term_text.strip()}\n{chr(10).join(content_texts)}"
                            accordion_texts.append(accordion_item)
                except Exception as e:
                    logger.debug(f"Error extracting accordion item: {e}")
                    continue
            
            # Also extract standalone p elements that might be accordion content
            # (in case accordions are already expanded)
            try:
                all_ps = await page.query_selector_all('p')
                for p in all_ps:
                    text = await p.inner_text()
                    if text and len(text.strip()) > 50:
                        # Check if it's near an accordion term
                        parent_section = await p.evaluate('''
                            (el) => {
                                let parent = el.parentElement;
                                while (parent && parent !== document.body) {
                                    if (parent.querySelector('dt.term, dt[data-js-accordiontoggle-trigger]')) {
                                        return true;
                                    }
                                    parent = parent.parentElement;
                                }
                                return false;
                            }
                        ''')
                        if parent_section and text.strip() not in accordion_texts:
                            accordion_texts.append(text.strip())
            except Exception as e:
                logger.debug(f"Error extracting standalone accordion paragraphs: {e}")
        
        except Exception as e:
            logger.debug(f"Error extracting accordion content: {e}")
        
        return '\n\n'.join(accordion_texts) if accordion_texts else ''
    
    async def extract_content_sections(self, page: Page) -> Dict[str, str]:
        """
        Extract content sections with specific class names (Ducati-specific).
        Extracts: .content, .header, .text, .title, .description

        Args:
            page: Playwright page object

        Returns:
            Dict with keys: content, header, text, title, description
        """
        sections = {
            'content': '',
            'header': '',
            'text': '',
            'title': '',
            'description': '',
        }
        
        # Extract .content divs
        try:
            content_divs = await page.query_selector_all('div.content')
            content_texts = []
            for div in content_divs:
                text = await div.inner_text()
                if text and len(text.strip()) > 10:
                    content_texts.append(text.strip())
            if content_texts:
                sections['content'] = ' '.join(content_texts)
        except Exception as e:
            logger.debug(f"Error extracting .content: {e}")
        
        # Extract p.content paragraphs
        try:
            p_content = await page.query_selector_all('p.content')
            p_texts = []
            for p in p_content:
                text = await p.inner_text()
                if text and len(text.strip()) > 10:
                    p_texts.append(text.strip())
            if p_texts:
                if sections.get('content'):
                    sections['content'] += ' ' + ' '.join(p_texts)
                else:
                    sections['content'] = ' '.join(p_texts)
        except Exception as e:
            logger.debug(f"Error extracting p.content: {e}")
        
        # Extract div.d-editor-text (Ducati-specific editor content)
        try:
            editor_texts = await page.query_selector_all('div.d-editor-text')
            editor_contents = []
            for div in editor_texts:
                text = await div.inner_text()
                if text and len(text.strip()) > 10:
                    editor_contents.append(text.strip())
            if editor_contents:
                if sections.get('content'):
                    sections['content'] += ' ' + ' '.join(editor_contents)
                else:
                    sections['content'] = ' '.join(editor_contents)
        except Exception as e:
            logger.debug(f"Error extracting div.d-editor-text: {e}")
        
        # Extract div.d-dual-media (Ducati-specific dual media content)
        try:
            dual_media_divs = await page.query_selector_all('div.d-dual-media')
            dual_media_contents = []
            for div in dual_media_divs:
                text = await div.inner_text()
                if text and len(text.strip()) > 20:
                    dual_media_contents.append(text.strip())
            if dual_media_contents:
                if sections.get('content'):
                    sections['content'] += ' ' + ' '.join(dual_media_contents)
                else:
                    sections['content'] = ' '.join(dual_media_contents)
        except Exception as e:
            logger.debug(f"Error extracting div.d-dual-media: {e}")
        
        # Extract em elements (disclaimers, notes)
        try:
            em_elements = await page.query_selector_all('em')
            em_texts = []
            for em in em_elements:
                text = await em.inner_text()
                if text and len(text.strip()) > 20:
                    em_texts.append(text.strip())
            if em_texts:
                sections['disclaimer'] = ' | '.join(em_texts)
        except Exception as e:
            logger.debug(f"Error extracting em elements: {e}")
        
        # Extract .header divs
        try:
            header_divs = await page.query_selector_all('div.header')
            header_texts = []
            for div in header_divs:
                text = await div.inner_text()
                if text and len(text.strip()) > 5:
                    header_texts.append(text.strip())
            if header_texts:
                sections['header'] = ' | '.join(header_texts)  # Join multiple headers
        except Exception as e:
            logger.debug(f"Error extracting .header: {e}")
        
        # Extract .text divs
        try:
            text_divs = await page.query_selector_all('div.text')
            text_contents = []
            for div in text_divs:
                text = await div.inner_text()
                if text and len(text.strip()) > 10:
                    text_contents.append(text.strip())
            if text_contents:
                sections['text'] = ' '.join(text_contents)
        except Exception as e:
            logger.debug(f"Error extracting .text: {e}")
        
        # Extract h2.title (section titles, e.g., "Watch the presentation...")
        try:
            h2_titles = await page.query_selector_all('h2.title')
            h2_title_texts = []
            for h2 in h2_titles:
                text = await h2.inner_text()
                if text and len(text.strip()) > 5:
                    h2_title_texts.append(text.strip())
            if h2_title_texts:
                if sections.get('title'):
                    sections['title'] += ' | ' + ' | '.join(h2_title_texts)
                else:
                    sections['title'] = ' | '.join(h2_title_texts)
        except Exception as e:
            logger.debug(f"Error extracting h2.title: {e}")
        
        # Extract .title divs
        try:
            title_divs = await page.query_selector_all('div.title')
            title_texts = []
            for div in title_divs:
                text = await div.inner_text()
                if text and len(text.strip()) > 3:
                    # Skip navigation titles (usually short like "BIKES", "MODELS")
                    if len(text.strip()) > 10:
                        title_texts.append(text.strip())
            if title_texts:
                sections['title'] = ' | '.join(title_texts)  # Join multiple titles
        except Exception as e:
            logger.debug(f"Error extracting .title: {e}")
        
        # Extract .description paragraphs
        try:
            desc_paras = await page.query_selector_all('p.description')
            desc_texts = []
            for p in desc_paras:
                text = await p.inner_text()
                if text and len(text.strip()) > 20:
                    desc_texts.append(text.strip())
            if desc_texts:
                sections['description'] = ' '.join(desc_texts)
        except Exception as e:
            logger.debug(f"Error extracting p.description: {e}")
        
        # Extract .text-inner divs (heritage pages)
        try:
            text_inner_divs = await page.query_selector_all('div.text-inner')
            text_inner_contents = []
            for div in text_inner_divs:
                text = await div.inner_text()
                if text and len(text.strip()) > 10:
                    text_inner_contents.append(text.strip())
            if text_inner_contents:
                # Add to text section or create new section
                if sections.get('text'):
                    sections['text'] += ' ' + ' '.join(text_inner_contents)
                else:
                    sections['text'] = ' '.join(text_inner_contents)
        except Exception as e:
            logger.debug(f"Error extracting div.text-inner: {e}")
        
        # Extract .top divs (Ducati-specific)
        try:
            top_divs = await page.query_selector_all('div.top')
            top_contents = []
            for div in top_divs:
                text = await div.inner_text()
                if text and len(text.strip()) > 5:
                    top_contents.append(text.strip())
            if top_contents:
                sections['top'] = ' | '.join(top_contents)
        except Exception as e:
            logger.debug(f"Error extracting div.top: {e}")
        
        # Extract tooltip content (div.tooltip and div[data-js-tip])
        try:
            tooltip_texts = []
            
            # Extract from div.tooltip elements
            tooltip_divs = await page.query_selector_all('div.tooltip[role="tooltip"]')
            for tooltip in tooltip_divs:
                text = await tooltip.inner_text()
                if text and len(text.strip()) > 10:
                    tooltip_texts.append(text.strip())
            
            # Extract from div[data-js-tip] elements (hover tooltips)
            data_tip_divs = await page.query_selector_all('div[data-js-tip]')
            for tip_div in data_tip_divs:
                # Get the tooltip text (might be in title attribute or inner text)
                title = await tip_div.get_attribute('title')
                if title and len(title.strip()) > 5:
                    tooltip_texts.append(title.strip())
                
                # Also check inner text
                text = await tip_div.inner_text()
                if text and len(text.strip()) > 10:
                    tooltip_texts.append(text.strip())
            
            # Also try to find associated tooltip divs by ID
            for tip_div in data_tip_divs:
                try:
                    tip_id = await tip_div.get_attribute('data-js-tip')
                    if tip_id:
                        # Look for tooltip with matching ID
                        tooltip = await page.query_selector(f'div.tooltip#{tip_id}, div[role="tooltip"]#{tip_id}')
                        if tooltip:
                            text = await tooltip.inner_text()
                            if text and len(text.strip()) > 10:
                                tooltip_texts.append(text.strip())
                except Exception as e:
                    logger.debug(f"Error finding tooltip by ID: {e}")
                    continue
            
            if tooltip_texts:
                # Deduplicate tooltips
                unique_tooltips = []
                seen = set()
                for tooltip in tooltip_texts:
                    if tooltip not in seen:
                        seen.add(tooltip)
                        unique_tooltips.append(tooltip)
                sections['tooltips'] = ' | '.join(unique_tooltips)
        except Exception as e:
            logger.debug(f"Error extracting tooltips: {e}")
        
        return sections
    
    async def _handle_insights_tabs(self, page: Page, data: Dict[str, Any]) -> None:
        """
        Handle insights pages with tabs (Design, Technology, etc.).
        Clicks through tabs to extract all content.
        
        Args:
            page: Playwright page object
            data: Data dict to update
        """
        try:
            # Find tab buttons/links
            tab_selectors = [
                'a[href*="?tab="]',
                'a[href*="tab="]',
                '[role="tab"]',
                '.tabs a',
                '[class*="tab"] a',
                'button[data-tab]',
                '[data-js-tab]',
            ]
            
            tabs_found = []
            for selector in tab_selectors:
                try:
                    tabs = await page.query_selector_all(selector)
                    for tab in tabs:
                        try:
                            text = await tab.inner_text()
                            href = await tab.get_attribute('href')
                            tab_id = await tab.get_attribute('data-tab') or await tab.get_attribute('data-js-tab')
                            
                            if text and text.strip():
                                tabs_found.append({
                                    'element': tab,
                                    'text': text.strip(),
                                    'href': href,
                                    'tab_id': tab_id
                                })
                        except:
                            continue
                except:
                    continue
            
            if not tabs_found:
                logger.debug("No tabs found on insights page")
                return
            
            logger.info(f"Found {len(tabs_found)} tabs on insights page")
            
            # Extract content from each tab
            tab_contents = {}
            for tab_info in tabs_found:
                try:
                    tab_element = tab_info['element']
                    tab_text = tab_info['text']
                    
                    # Scroll tab into view
                    await tab_element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    
                    # Click tab
                    await tab_element.click()
                    await asyncio.sleep(2)  # Wait for content to load
                    
                    # Extract content from active tab
                    tab_content = await self.extract_content_sections(page)
                    if tab_content:
                        tab_contents[tab_text] = tab_content
                    
                    logger.debug(f"Extracted content from tab: {tab_text}")
                    
                except Exception as e:
                    logger.debug(f"Error extracting tab {tab_info.get('text', 'unknown')}: {e}")
                    continue
            
            # Merge tab contents into data
            if tab_contents:
                # Add tab contents to content_sections
                if 'content_sections' not in data:
                    data['content_sections'] = {}
                
                data['content_sections']['tabs'] = tab_contents
                
                # Also merge tab descriptions into main description
                tab_descriptions = []
                for tab_name, tab_data in tab_contents.items():
                    if tab_data.get('content'):
                        tab_descriptions.append(f"{tab_name}: {tab_data['content']}")
                    if tab_data.get('text'):
                        tab_descriptions.append(f"{tab_name}: {tab_data['text']}")
                
                if tab_descriptions:
                    if data.get('description'):
                        data['description'] += '\n\n' + '\n\n'.join(tab_descriptions)
                    else:
                        data['description'] = '\n\n'.join(tab_descriptions)
        
        except Exception as e:
            logger.debug(f"Error handling insights tabs: {e}")
    
    async def _extract_story_content(self, page: Page, data: Dict[str, Any]) -> None:
        """
        Extract additional content from stories/travel pages.
        
        Args:
            page: Playwright page object
            data: Data dict to update
        """
        try:
            story_parts = []
            
            # Extract h1.title (main story title)
            try:
                title_elem = await page.query_selector('h1.title')
                if title_elem:
                    title_text = await title_elem.inner_text()
                    if title_text and len(title_text.strip()) > 3:
                        story_parts.append(f"# {title_text.strip()}")
                        # Also add to content_sections
                        if 'content_sections' not in data:
                            data['content_sections'] = {}
                        data['content_sections']['story_title'] = title_text.strip()
            except Exception as e:
                logger.debug(f"Error extracting h1.title: {e}")
            
            # Extract div.txt (introductory text)
            try:
                txt_divs = await page.query_selector_all('div.txt')
                txt_texts = []
                for div in txt_divs:
                    text = await div.inner_text()
                    if text and len(text.strip()) > 10:
                        txt_texts.append(text.strip())
                if txt_texts:
                    story_parts.extend(txt_texts)
                    if 'content_sections' not in data:
                        data['content_sections'] = {}
                    data['content_sections']['story_intro'] = ' '.join(txt_texts)
            except Exception as e:
                logger.debug(f"Error extracting div.txt: {e}")
            
            # Extract section.body (story section headers/intro)
            try:
                body_sections = await page.query_selector_all('section.body')
                body_texts = []
                for section in body_sections:
                    text = await section.inner_text()
                    if text and len(text.strip()) > 10:
                        body_texts.append(text.strip())
                if body_texts:
                    story_parts.extend(body_texts)
            except Exception as e:
                logger.debug(f"Error extracting section.body: {e}")
            
            # Extract div.content (main story content)
            try:
                content_divs = await page.query_selector_all('div.content')
                content_texts = []
                for div in content_divs:
                    text = await div.inner_text()
                    if text and len(text.strip()) > 20:
                        content_texts.append(text.strip())
                if content_texts:
                    story_parts.extend(content_texts)
            except Exception as e:
                logger.debug(f"Error extracting div.content from story: {e}")
            
            # Extract all paragraphs (story narrative)
            try:
                paragraphs = await page.query_selector_all('p')
                para_texts = []
                for p in paragraphs:
                    text = await p.inner_text()
                    # Filter out very short paragraphs (likely navigation/UI)
                    if text and 50 < len(text.strip()) < 2000:
                        # Check if it looks like story content (not navigation)
                        if not any(skip in text.lower() for skip in ['cookie', 'privacy', 'menu', 'home', 'about']):
                            para_texts.append(text.strip())
                if para_texts:
                    story_parts.extend(para_texts)
            except Exception as e:
                logger.debug(f"Error extracting story paragraphs: {e}")
            
            # Stories pages may have special content sections
            story_selectors = [
                '.story-content',
                '.article-content',
                '[class*="story"]',
                '[class*="article"]',
                '.travel-content',
            ]
            
            for selector in story_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for elem in elements:
                        text = await elem.inner_text()
                        if text and len(text.strip()) > 50:
                            story_parts.append(text.strip())
                except:
                    continue
            
            if story_parts:
                # Combine all story parts
                story_content = '\n\n'.join(story_parts)
                
                # Add to description
                if data.get('description'):
                    data['description'] += '\n\n' + story_content
                else:
                    data['description'] = story_content
                
                # Also add to content_sections
                if 'content_sections' not in data:
                    data['content_sections'] = {}
                data['content_sections']['story'] = story_content
        
        except Exception as e:
            logger.debug(f"Error extracting story content: {e}")

    async def extract_colors(self, page: Page) -> List[str]:
        """
        Extract available color options.

        Args:
            page: Playwright page object

        Returns:
            List of color names
        """
        colors = []

        # Try color-specific selectors
        color_selectors = [
            '[class*="color"]',
            '.color-swatch',
            '[data-color]',
            '.colours',
        ]

        for selector in color_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    # Try to get color name from data attribute
                    color_name = await elem.get_attribute('data-color')
                    if not color_name:
                        color_name = await elem.get_attribute('title')
                    if not color_name:
                        color_name = await elem.inner_text()

                    if color_name and len(color_name.strip()) > 0:
                        colors.append(color_name.strip())
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue

        # Deduplicate
        colors = list(set(colors))

        logger.info(f"Extracted {len(colors)} colors")
        return colors

    async def extract_pricing(self, page: Page) -> Optional[Dict[str, Any]]:
        """
        Extract price information.

        Args:
            page: Playwright page object

        Returns:
            Price dict or None
        """
        try:
            # Get page text
            text_content = await page.inner_text('body')

            # Look for price patterns
            # USD pattern
            usd_match = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', text_content)
            if usd_match:
                price_str = usd_match.group(1).replace(',', '')
                return {
                    'amount': float(price_str),
                    'currency': 'USD',
                    'region': 'US'
                }

            # EUR pattern
            eur_match = re.search(r'€\s*([\d,]+(?:\.\d{2})?)', text_content)
            if eur_match:
                price_str = eur_match.group(1).replace(',', '')
                return {
                    'amount': float(price_str),
                    'currency': 'EUR',
                    'region': 'EU'
                }

            # GBP pattern
            gbp_match = re.search(r'£\s*([\d,]+(?:\.\d{2})?)', text_content)
            if gbp_match:
                price_str = gbp_match.group(1).replace(',', '')
                return {
                    'amount': float(price_str),
                    'currency': 'GBP',
                    'region': 'UK'
                }

        except Exception as e:
            logger.debug(f"Error extracting price: {e}")

        return None
