"""
Bike Page Classifier for motorcycle OEM web-crawler.

Identifies which pages contain bike model information and classifies page types.
"""

import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BikePageClassifier:
    """
    Classify pages as bike-related and determine page types.
    """

    def __init__(self, manufacturer: str):
        """
        Initialize bike page classifier.

        Args:
            manufacturer: Manufacturer/OEM name
        """
        self.manufacturer = manufacturer

        # URL patterns that indicate bike pages
        self.bike_url_patterns = [
            r'/bikes?/',
            r'/motorcycles?/',
            r'/models?/',
            r'/heritage/',
            r'/insights',
            r'/stories',
        ]

        # Page type indicators
        self.page_type_indicators = {
            'specs': ['specification', 'spec', 'technical', 'tech-data'],
            'gallery': ['gallery', 'photos', 'images'],
            'features': ['features', 'equipment', 'technology'],
            'insights': ['insights', 'insight'],
            'stories': ['stories', 'story', 'travel'],
            'main': ['overview', 'details', 'home'],
        }

    def is_bike_page(self, url: str, page_content: str) -> bool:
        """
        Determine if page contains bike model information.

        Args:
            url: Page URL
            page_content: Page HTML content or text

        Returns:
            True if page is a bike page
        """
        # Check URL patterns
        url_lower = url.lower()
        for pattern in self.bike_url_patterns:
            if re.search(pattern, url_lower):
                # Exclude listing/comparison pages
                if any(exclude in url_lower for exclude in ['/compare', '/list', '/all', '/browse']):
                    return False
                return True

        # Check content for bike indicators
        if not page_content:
            return False

        content_lower = page_content.lower()

        # Look for specification-related keywords
        spec_keywords = [
            'displacement', 'horsepower', 'torque', 'wheelbase',
            'fuel capacity', 'seat height', 'dry weight', 'wet weight',
            'engine type', 'bore', 'stroke', 'compression'
        ]

        spec_count = sum(1 for keyword in spec_keywords if keyword in content_lower)

        # If we find 3+ spec keywords, likely a bike page
        if spec_count >= 3:
            return True

        return False

    def get_page_type(self, url: str, content: str) -> str:
        """
        Classify page type: 'main', 'specs', 'gallery', 'features', 'other'.

        Args:
            url: Page URL
            content: Page HTML content or text

        Returns:
            Page type string
        """
        url_lower = url.lower()
        content_lower = content.lower() if content else ""

        # Check URL and content for type indicators
        for page_type, indicators in self.page_type_indicators.items():
            for indicator in indicators:
                if indicator in url_lower or indicator in content_lower:
                    return page_type

        # Default to main if it's a bike page
        return 'main'

    def extract_model_info(self, url: str, page_content: str) -> Optional[Dict[str, Any]]:
        """
        Extract preliminary model, year, variant from page.

        Args:
            url: Page URL
            page_content: Page HTML content or text

        Returns:
            Dict with 'model', 'year', 'variant' or None if extraction fails
        """
        result = {
            'model': None,
            'year': None,
            'variant': None
        }

        # Extract model from URL
        model = self._extract_model_from_url(url)
        if model:
            result['model'] = model

        # Extract year from URL or content
        year = self._extract_year_from_url(url)
        if not year:
            year = self._extract_year_from_content(page_content)

        if year:
            result['year'] = year

        # Extract variant if present
        variant = self._extract_variant(url, page_content)
        if variant:
            result['variant'] = variant

        # Only return if we have at least a model
        if result['model']:
            return result

        return None

    def _extract_model_from_url(self, url: str) -> Optional[str]:
        """Extract model name from URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')

        # Look for path segment after bikes/motorcycles/models
        for i, part in enumerate(path_parts):
            if part.lower() in ['bikes', 'motorcycles', 'models', 'heritage']:
                if i + 1 < len(path_parts):
                    model_slug = path_parts[i + 1]
                    # Skip year-like segments
                    if not re.match(r'^\d{4}$', model_slug):
                        # Convert slug to title case
                        model_name = model_slug.replace('-', ' ').replace('_', ' ').title()
                        return model_name

        return None

    def _extract_year_from_url(self, url: str) -> Optional[int]:
        """Extract year from URL."""
        # Look for 4-digit year pattern
        year_match = re.search(r'/(\d{4})(?:/|$)', url)
        if year_match:
            year = int(year_match.group(1))
            # Validate it's a reasonable motorcycle year
            if 1900 <= year <= 2030:
                return year

        return None

    def _extract_year_from_content(self, content: str) -> Optional[int]:
        """Extract year from page content."""
        if not content:
            return None

        # Look for year patterns in content
        patterns = [
            r'(\d{4})\s+model',
            r'model\s+year[:\s]+(\d{4})',
            r'MY\s*(\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2030:
                    return year

        return None

    def _extract_variant(self, url: str, content: str) -> Optional[str]:
        """Extract variant/submodel name."""
        # Common variant indicators
        variant_patterns = [
            r'/(s|r|sp|rs|rr|abs|se|limited|edition)',
            r'\b(S|R|SP|RS|RR|ABS|SE|Limited Edition)\b',
        ]

        url_lower = url.lower()
        for pattern in variant_patterns:
            match = re.search(pattern, url_lower)
            if match:
                return match.group(1).upper()

        # Look in content
        if content:
            content_lower = content.lower()
            for pattern in variant_patterns:
                match = re.search(pattern, content_lower)
                if match:
                    return match.group(1).upper()

        return None

    def group_related_pages(self, pages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group pages by (manufacturer, model, year, variant).

        Args:
            pages: List of page dicts with 'url', 'model_info', 'page_type'

        Returns:
            Dict mapping (manufacturer, model, year, variant) to list of pages
        """
        grouped = {}

        for page in pages:
            model_info = page.get('model_info')
            if not model_info:
                continue

            # Create grouping key
            key = (
                self.manufacturer,
                model_info.get('model'),
                model_info.get('year'),
                model_info.get('variant')
            )

            if key not in grouped:
                grouped[key] = []

            grouped[key].append(page)

        logger.info(f"Grouped {len(pages)} pages into {len(grouped)} bike groups")
        return grouped
