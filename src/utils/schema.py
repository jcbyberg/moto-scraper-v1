"""
Pydantic schema models for motorcycle data validation.

All models follow the constitution requirement that measurements must be in metric units.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class EngineSpecs(BaseModel):
    """Engine specifications (all in metric units)."""

    type: Optional[str] = Field(None, description="Engine type (e.g., 'Inline-4', 'V-Twin')")
    displacement_cc: Optional[float] = Field(None, description="Displacement in cubic centimeters")
    bore_mm: Optional[float] = Field(None, description="Bore in millimeters")
    stroke_mm: Optional[float] = Field(None, description="Stroke in millimeters")
    compression_ratio: Optional[float] = Field(None, description="Compression ratio (e.g., 12.5:1)")
    max_power_kw: Optional[float] = Field(None, description="Maximum power in kilowatts")
    max_power_rpm: Optional[int] = Field(None, description="RPM at maximum power")
    max_torque_nm: Optional[float] = Field(None, description="Maximum torque in Newton-meters")
    max_torque_rpm: Optional[int] = Field(None, description="RPM at maximum torque")
    fuel_system: Optional[str] = Field(None, description="Fuel system type")
    ignition: Optional[str] = Field(None, description="Ignition system")
    starter: Optional[str] = Field(None, description="Starter type")
    lubrication: Optional[str] = Field(None, description="Lubrication system")


class TransmissionSpecs(BaseModel):
    """Transmission specifications."""

    type: Optional[str] = Field(None, description="Transmission type (e.g., '6-speed manual')")
    clutch: Optional[str] = Field(None, description="Clutch type")
    final_drive: Optional[str] = Field(None, description="Final drive type")


class ChassisSpecs(BaseModel):
    """Chassis specifications."""

    frame_type: Optional[str] = Field(None, description="Frame type")
    front_suspension: Optional[str] = Field(None, description="Front suspension")
    rear_suspension: Optional[str] = Field(None, description="Rear suspension")
    front_brake: Optional[str] = Field(None, description="Front brake")
    rear_brake: Optional[str] = Field(None, description="Rear brake")
    front_tire: Optional[str] = Field(None, description="Front tire specification")
    rear_tire: Optional[str] = Field(None, description="Rear tire specification")


class DimensionSpecs(BaseModel):
    """Dimension specifications (all in metric units)."""

    length_mm: Optional[float] = Field(None, description="Length in millimeters")
    width_mm: Optional[float] = Field(None, description="Width in millimeters")
    height_mm: Optional[float] = Field(None, description="Height in millimeters")
    wheelbase_mm: Optional[float] = Field(None, description="Wheelbase in millimeters")
    ground_clearance_mm: Optional[float] = Field(None, description="Ground clearance in millimeters")
    seat_height_mm: Optional[float] = Field(None, description="Seat height in millimeters")
    dry_weight_kg: Optional[float] = Field(None, description="Dry weight in kilograms")
    wet_weight_kg: Optional[float] = Field(None, description="Wet weight in kilograms")
    fuel_capacity_liters: Optional[float] = Field(None, description="Fuel capacity in liters")


class PerformanceSpecs(BaseModel):
    """Performance specifications (all in metric units)."""

    top_speed_kmh: Optional[float] = Field(None, description="Top speed in km/h")
    acceleration_0_100_kmh_sec: Optional[float] = Field(None, description="0-100 km/h acceleration time in seconds")
    fuel_consumption_liters_per_100km: Optional[float] = Field(None, description="Fuel consumption in L/100km")


class ElectricalSpecs(BaseModel):
    """Electrical specifications."""

    battery_voltage: Optional[int] = Field(None, description="Battery voltage")
    alternator: Optional[str] = Field(None, description="Alternator specification")
    headlight: Optional[str] = Field(None, description="Headlight type")
    tail_light: Optional[str] = Field(None, description="Tail light type")


class BikeSpecifications(BaseModel):
    """Complete bike specifications."""

    engine: Optional[EngineSpecs] = Field(default_factory=EngineSpecs)
    transmission: Optional[TransmissionSpecs] = Field(default_factory=TransmissionSpecs)
    chassis: Optional[ChassisSpecs] = Field(default_factory=ChassisSpecs)
    dimensions: Optional[DimensionSpecs] = Field(default_factory=DimensionSpecs)
    performance: Optional[PerformanceSpecs] = Field(default_factory=PerformanceSpecs)
    electrical: Optional[ElectricalSpecs] = Field(default_factory=ElectricalSpecs)


class PriceInfo(BaseModel):
    """Price information."""

    currency: str = Field(..., description="Currency code (e.g., 'USD')")
    amount: float = Field(..., description="Price amount")
    region: Optional[str] = Field(None, description="Region/market (e.g., 'US')")


class ImageInfo(BaseModel):
    """Image information."""

    url: str = Field(..., description="Original image URL")
    local_path: Optional[str] = Field(None, description="Local file path")
    alt_text: Optional[str] = Field(None, description="Image alt text")
    image_type: Optional[str] = Field(None, description="Image type (main, gallery, detail, etc.)")
    hash: Optional[str] = Field(None, description="SHA-256 hash for deduplication")


class BikeData(BaseModel):
    """
    Complete motorcycle data model.

    This is the unified schema that all extracted data must conform to.
    All measurements are in metric units as per constitution requirements.
    """

    # Required fields
    manufacturer: str = Field(..., description="OEM name")
    model: str = Field(..., description="Model name")
    year: int = Field(..., description="Model year")

    # Optional identification
    variant: Optional[str] = Field(None, description="Variant/submodel name")

    # Specifications
    specifications: BikeSpecifications = Field(default_factory=BikeSpecifications)

    # Descriptive content
    features: List[str] = Field(default_factory=list, description="List of features")
    description: Optional[str] = Field(None, description="Full description text")
    content_sections: Optional[Dict[str, str]] = Field(None, description="Structured content sections (header, title, text, content, description)")
    colors: List[str] = Field(default_factory=list, description="Available color options")

    # Pricing
    price: Optional[PriceInfo] = Field(None, description="Price information")

    # Images
    images: List[ImageInfo] = Field(default_factory=list, description="Image information")

    # Source tracking
    source_urls: List[str] = Field(default_factory=list, description="URLs where data was collected")
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="Extraction timestamp")

    @validator('year')
    def validate_year(cls, v):
        """Validate year is reasonable."""
        if v < 1900 or v > datetime.now().year + 2:
            raise ValueError(f"Year {v} is not valid")
        return v

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process."""

    timestamp: datetime = Field(default_factory=datetime.now)
    source_urls: List[str] = Field(default_factory=list)
    page_types: List[str] = Field(default_factory=list, description="Types of pages extracted from")
    extractor_version: str = Field(default="1.0", description="Extractor version")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BikeDataWithMetadata(BaseModel):
    """Bike data with extraction metadata."""

    bike_data: BikeData
    extraction: ExtractionMetadata

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
