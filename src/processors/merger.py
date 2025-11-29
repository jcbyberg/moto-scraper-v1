"""
Data Merger for motorcycle OEM web-crawler.

Merges data from multiple pages for the same bike model/year.
"""

from typing import List, Dict, Any, Tuple
from src.utils.schema import BikeData
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataMerger:
    """
    Merge data from multiple pages for same bike.
    """

    def __init__(self):
        """Initialize data merger."""
        # Priority order for page types (higher priority = more authoritative)
        self.page_type_priority = {
            'specs': 3,
            'main': 2,
            'features': 1,
            'gallery': 0,
            'other': 0
        }

    def merge_bike_data(
        self,
        pages_data: List[Dict[str, Any]]
    ) -> BikeData:
        """
        Merge data from multiple pages for same bike.

        Args:
            pages_data: List of dicts with 'bike_data' (BikeData) and 'page_type'

        Returns:
            Merged BikeData object
        """
        if not pages_data:
            raise ValueError("No pages data to merge")

        if len(pages_data) == 1:
            return pages_data[0]['bike_data']

        logger.info(f"Merging data from {len(pages_data)} pages")

        # Sort by page type priority
        pages_data.sort(
            key=lambda x: self.page_type_priority.get(x.get('page_type', 'other'), 0),
            reverse=True
        )

        # Start with highest priority page
        merged = pages_data[0]['bike_data'].model_copy(deep=True)

        # Merge specifications from all pages
        for page_info in pages_data[1:]:
            bike_data = page_info['bike_data']
            page_type = page_info.get('page_type', 'other')

            # Merge engine specs
            merged.specifications.engine = self._merge_specs(
                merged.specifications.engine,
                bike_data.specifications.engine,
                page_type
            )

            # Merge transmission specs
            merged.specifications.transmission = self._merge_specs(
                merged.specifications.transmission,
                bike_data.specifications.transmission,
                page_type
            )

            # Merge chassis specs
            merged.specifications.chassis = self._merge_specs(
                merged.specifications.chassis,
                bike_data.specifications.chassis,
                page_type
            )

            # Merge dimensions
            merged.specifications.dimensions = self._merge_specs(
                merged.specifications.dimensions,
                bike_data.specifications.dimensions,
                page_type
            )

            # Merge performance
            merged.specifications.performance = self._merge_specs(
                merged.specifications.performance,
                bike_data.specifications.performance,
                page_type
            )

            # Merge electrical
            merged.specifications.electrical = self._merge_specs(
                merged.specifications.electrical,
                bike_data.specifications.electrical,
                page_type
            )

            # Combine features (deduplicate)
            merged.features = self.combine_features([merged.features, bike_data.features])

            # Use longer description
            if not merged.description or len(bike_data.description) > len(merged.description):
                merged.description = bike_data.description

            # Combine colors
            merged.colors = list(set(merged.colors + bike_data.colors))

            # Combine images
            merged.images.extend(bike_data.images)

            # Aggregate source URLs
            merged.source_urls.extend(bike_data.source_urls)

        # Deduplicate source URLs
        merged.source_urls = list(set(merged.source_urls))

        # Deduplicate images by URL
        seen_urls = set()
        unique_images = []
        for img in merged.images:
            if img.url not in seen_urls:
                seen_urls.add(img.url)
                unique_images.append(img)
        merged.images = unique_images

        logger.info(f"Merge complete: {len(merged.source_urls)} source URLs, {len(merged.images)} images")
        return merged

    def _merge_specs(self, spec1: Any, spec2: Any, page_type2: str) -> Any:
        """
        Merge two specification objects.

        Fills in None values from spec2 into spec1.

        Args:
            spec1: First spec object (higher priority)
            spec2: Second spec object
            page_type2: Page type of spec2

        Returns:
            Merged spec object
        """
        if not spec1:
            return spec2
        if not spec2:
            return spec1

        # Get all fields
        for field_name in spec1.model_fields.keys():
            value1 = getattr(spec1, field_name, None)
            value2 = getattr(spec2, field_name, None)

            # If spec1 is None but spec2 has value, use spec2
            if value1 is None and value2 is not None:
                setattr(spec1, field_name, value2)

        return spec1

    def resolve_conflict(
        self,
        values: List[Tuple[Any, str]],
        page_types: List[str]
    ) -> Any:
        """
        Resolve conflicts when same field has different values.

        Priority: specs > main > features > gallery

        Args:
            values: List of (value, source_url) tuples
            page_types: List of page types corresponding to values

        Returns:
            Resolved value
        """
        if not values:
            return None

        if len(values) == 1:
            return values[0][0]

        # Find highest priority value
        max_priority = -1
        best_value = None

        for (value, source_url), page_type in zip(values, page_types):
            priority = self.page_type_priority.get(page_type, 0)
            if priority > max_priority:
                max_priority = priority
                best_value = value

        return best_value

    def combine_features(self, features_lists: List[List[str]]) -> List[str]:
        """
        Combine and deduplicate feature lists.

        Args:
            features_lists: List of feature lists

        Returns:
            Combined and deduplicated feature list
        """
        all_features = []
        for features in features_lists:
            all_features.extend(features)

        # Deduplicate while preserving order
        seen = set()
        unique_features = []
        for feature in all_features:
            feature_clean = feature.strip()
            if feature_clean and feature_clean not in seen:
                seen.add(feature_clean)
                unique_features.append(feature_clean)

        return unique_features

    def aggregate_source_urls(
        self,
        pages_data: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Collect all source URLs from pages.

        Args:
            pages_data: List of page data dicts

        Returns:
            List of unique source URLs
        """
        urls = []
        for page_info in pages_data:
            bike_data = page_info.get('bike_data')
            if bike_data:
                urls.extend(bike_data.source_urls)

        return list(set(urls))
