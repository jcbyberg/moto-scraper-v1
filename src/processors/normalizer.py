"""
Data Normalizer for motorcycle OEM web-crawler.

Normalizes extracted data to unified schema with metric units.
"""

from typing import Dict, Any, Optional, Tuple
import re
from datetime import datetime

from src.utils.schema import (
    BikeData, BikeSpecifications, EngineSpecs, TransmissionSpecs,
    ChassisSpecs, DimensionSpecs, PerformanceSpecs, ElectricalSpecs,
    PriceInfo, ImageInfo
)
from src.utils.units import parse_spec_value, convert_to_metric
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataNormalizer:
    """
    Normalize extracted data to standard schema with metric units.
    """

    def __init__(self):
        """Initialize data normalizer."""
        # Field name mappings (source field -> schema field)
        self.field_mappings = {
            # Engine
            'engine size': 'displacement_cc',
            'displacement': 'displacement_cc',
            'capacity': 'displacement_cc',
            'bore': 'bore_mm',
            'stroke': 'stroke_mm',
            'compression': 'compression_ratio',
            'compression ratio': 'compression_ratio',
            'power': 'max_power_kw',
            'max power': 'max_power_kw',
            'maximum power': 'max_power_kw',
            'horsepower': 'max_power_kw',
            'torque': 'max_torque_nm',
            'max torque': 'max_torque_nm',
            'maximum torque': 'max_torque_nm',
            'fuel system': 'fuel_system',
            'ignition': 'ignition',
            'starter': 'starter',
            'lubrication': 'lubrication',
            'engine type': 'type',

            # Transmission
            'transmission': 'type',
            'gearbox': 'type',
            'clutch': 'clutch',
            'final drive': 'final_drive',

            # Chassis
            'frame': 'frame_type',
            'frame type': 'frame_type',
            'front suspension': 'front_suspension',
            'rear suspension': 'rear_suspension',
            'front brake': 'front_brake',
            'rear brake': 'rear_brake',
            'front tire': 'front_tire',
            'front tyre': 'front_tire',
            'rear tire': 'rear_tire',
            'rear tyre': 'rear_tire',

            # Dimensions
            'length': 'length_mm',
            'width': 'width_mm',
            'height': 'height_mm',
            'wheelbase': 'wheelbase_mm',
            'ground clearance': 'ground_clearance_mm',
            'seat height': 'seat_height_mm',
            'dry weight': 'dry_weight_kg',
            'wet weight': 'wet_weight_kg',
            'fuel capacity': 'fuel_capacity_liters',
            'tank capacity': 'fuel_capacity_liters',

            # Performance
            'top speed': 'top_speed_kmh',
            'max speed': 'top_speed_kmh',
            'maximum speed': 'top_speed_kmh',
            '0-100': 'acceleration_0_100_kmh_sec',
            '0-100 km/h': 'acceleration_0_100_kmh_sec',
            'fuel consumption': 'fuel_consumption_liters_per_100km',

            # Electrical
            'battery': 'battery_voltage',
            'alternator': 'alternator',
            'headlight': 'headlight',
            'tail light': 'tail_light',
        }

    def normalize(
        self,
        raw_data: Dict[str, Any],
        manufacturer: str,
        model: str,
        year: int,
        source_url: str
    ) -> BikeData:
        """
        Normalize raw extracted data to standard schema.

        Args:
            raw_data: Raw extracted data
            manufacturer: Manufacturer name
            model: Model name
            year: Model year
            source_url: Source URL

        Returns:
            Normalized BikeData object
        """
        logger.info(f"Normalizing data for {manufacturer} {model} {year}")

        # Extract and normalize specifications
        specs = self._normalize_specifications(raw_data.get('specifications', {}))

        # Normalize images
        images = []
        for img_data in raw_data.get('images', []):
            try:
                img_info = ImageInfo(
                    url=img_data['url'],
                    alt_text=img_data.get('alt', ''),
                    image_type=img_data.get('type', 'gallery'),
                    local_path=img_data.get('local_path'),
                    hash=img_data.get('hash')
                )
                images.append(img_info)
            except Exception as e:
                logger.debug(f"Error normalizing image: {e}")

        # Normalize price
        price = None
        if raw_data.get('price'):
            try:
                price = PriceInfo(**raw_data['price'])
            except Exception as e:
                logger.debug(f"Error normalizing price: {e}")

        # Merge content_sections into description if available
        description = raw_data.get('description', '')
        content_sections = raw_data.get('content_sections', {})
        
        if content_sections:
            # Build enhanced description from content sections
            description_parts = []
            if description:
                description_parts.append(description)
            
            # Add header if available
            if content_sections.get('header'):
                description_parts.append(f"\n\n{content_sections['header']}")
            
            # Add title if available
            if content_sections.get('title'):
                description_parts.append(f"\n\n{content_sections['title']}")
            
            # Add top section if available
            if content_sections.get('top'):
                description_parts.append(f"\n\n{content_sections['top']}")
            
            # Add text content
            if content_sections.get('text'):
                description_parts.append(f"\n\n{content_sections['text']}")
            
            # Add content
            if content_sections.get('content'):
                description_parts.append(f"\n\n{content_sections['content']}")
            
            # Add description from content_sections
            if content_sections.get('description'):
                description_parts.append(f"\n\n{content_sections['description']}")
            
            # Add tooltips if available (as additional context)
            if content_sections.get('tooltips'):
                description_parts.append(f"\n\nAdditional Information:\n{content_sections['tooltips']}")
            
            # Add disclaimer if available
            if content_sections.get('disclaimer'):
                description_parts.append(f"\n\nNote: {content_sections['disclaimer']}")
            
            # Join all parts
            if description_parts:
                description = '\n'.join(description_parts).strip()

        # Create BikeData object
        bike_data = BikeData(
            manufacturer=manufacturer,
            model=model,
            year=year,
            variant=raw_data.get('variant'),
            specifications=specs,
            features=raw_data.get('features', []),
            description=description,
            content_sections=content_sections if content_sections else None,
            colors=raw_data.get('colors', []),
            price=price,
            images=images,
            source_urls=[source_url],
            extraction_timestamp=datetime.now()
        )

        logger.info(f"Normalization complete for {manufacturer} {model} {year}")
        return bike_data

    def _normalize_specifications(self, raw_specs: Dict[str, str]) -> BikeSpecifications:
        """Normalize specifications to schema structure."""
        # Initialize spec objects
        engine = EngineSpecs()
        transmission = TransmissionSpecs()
        chassis = ChassisSpecs()
        dimensions = DimensionSpecs()
        performance = PerformanceSpecs()
        electrical = ElectricalSpecs()

        # Process each raw spec
        for raw_key, raw_value in raw_specs.items():
            # Normalize key
            key_lower = raw_key.lower().strip()

            # Find mapped field
            mapped_field = self.field_mappings.get(key_lower)

            if not mapped_field:
                # Try fuzzy matching
                mapped_field = self._fuzzy_match_field(key_lower)

            if not mapped_field:
                logger.debug(f"No mapping for field: {raw_key}")
                continue

            # Parse value and convert to metric
            normalized_value = self._normalize_value(raw_value, mapped_field)

            # Assign to appropriate spec object
            self._assign_to_spec(
                mapped_field, normalized_value,
                engine, transmission, chassis, dimensions, performance, electrical
            )

        return BikeSpecifications(
            engine=engine,
            transmission=transmission,
            chassis=chassis,
            dimensions=dimensions,
            performance=performance,
            electrical=electrical
        )

    def _fuzzy_match_field(self, key: str) -> Optional[str]:
        """Fuzzy match field name to known mappings."""
        for known_key, mapped_field in self.field_mappings.items():
            if known_key in key or key in known_key:
                return mapped_field
        return None

    def _normalize_value(self, raw_value: str, field_name: str) -> Any:
        """
        Normalize and convert value to metric units.

        Args:
            raw_value: Raw value string
            field_name: Target field name

        Returns:
            Normalized value in appropriate type and units
        """
        if not raw_value or not isinstance(raw_value, str):
            return None

        # Parse value and unit
        value, unit = parse_spec_value(raw_value)

        if value is None:
            # Try to return as string if it's descriptive
            return raw_value.strip()

        # Determine target unit based on field name
        target_unit = self._get_target_unit(field_name)

        # Convert if needed
        if unit and target_unit:
            converted = convert_to_metric(value, unit, target_unit)
            if converted is not None:
                return converted

        # Return value as-is if already metric or no conversion needed
        return value

    def _get_target_unit(self, field_name: str) -> Optional[str]:
        """Get target metric unit for a field."""
        unit_map = {
            'displacement_cc': 'cc',
            'bore_mm': 'mm',
            'stroke_mm': 'mm',
            'max_power_kw': 'kW',
            'max_torque_nm': 'Nm',
            'length_mm': 'mm',
            'width_mm': 'mm',
            'height_mm': 'mm',
            'wheelbase_mm': 'mm',
            'ground_clearance_mm': 'mm',
            'seat_height_mm': 'mm',
            'dry_weight_kg': 'kg',
            'wet_weight_kg': 'kg',
            'fuel_capacity_liters': 'L',
            'top_speed_kmh': 'km/h',
            'fuel_consumption_liters_per_100km': 'L/100km',
        }
        return unit_map.get(field_name)

    def _assign_to_spec(
        self,
        field_name: str,
        value: Any,
        engine: EngineSpecs,
        transmission: TransmissionSpecs,
        chassis: ChassisSpecs,
        dimensions: DimensionSpecs,
        performance: PerformanceSpecs,
        electrical: ElectricalSpecs
    ) -> None:
        """Assign normalized value to appropriate spec object."""
        # Engine fields
        engine_fields = [
            'type', 'displacement_cc', 'bore_mm', 'stroke_mm', 'compression_ratio',
            'max_power_kw', 'max_power_rpm', 'max_torque_nm', 'max_torque_rpm',
            'fuel_system', 'ignition', 'starter', 'lubrication'
        ]
        if field_name in engine_fields:
            setattr(engine, field_name, value)
            return

        # Transmission fields
        transmission_fields = ['type', 'clutch', 'final_drive']
        if field_name in transmission_fields:
            setattr(transmission, field_name, value)
            return

        # Chassis fields
        chassis_fields = [
            'frame_type', 'front_suspension', 'rear_suspension',
            'front_brake', 'rear_brake', 'front_tire', 'rear_tire'
        ]
        if field_name in chassis_fields:
            setattr(chassis, field_name, value)
            return

        # Dimension fields
        dimension_fields = [
            'length_mm', 'width_mm', 'height_mm', 'wheelbase_mm',
            'ground_clearance_mm', 'seat_height_mm', 'dry_weight_kg',
            'wet_weight_kg', 'fuel_capacity_liters'
        ]
        if field_name in dimension_fields:
            setattr(dimensions, field_name, value)
            return

        # Performance fields
        performance_fields = [
            'top_speed_kmh', 'acceleration_0_100_kmh_sec',
            'fuel_consumption_liters_per_100km'
        ]
        if field_name in performance_fields:
            setattr(performance, field_name, value)
            return

        # Electrical fields
        electrical_fields = ['battery_voltage', 'alternator', 'headlight', 'tail_light']
        if field_name in electrical_fields:
            setattr(electrical, field_name, value)
            return
