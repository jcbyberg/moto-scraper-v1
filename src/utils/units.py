"""
Unit conversion utilities for normalizing motorcycle specifications to metric units.

All conversion functions preserve precision and follow the constitution requirement
that ALL measurements MUST be in metric units.
"""

from typing import Optional, Tuple
import re


# Conversion constants
HP_TO_KW = 0.7457  # 1 hp = 0.7457 kW
LBFT_TO_NM = 1.3558  # 1 lb-ft = 1.3558 Nm
INCH_TO_MM = 25.4  # 1 inch = 25.4 mm
FOOT_TO_MM = 304.8  # 1 foot = 304.8 mm
LBS_TO_KG = 0.453592  # 1 lb = 0.453592 kg
MPH_TO_KMH = 1.60934  # 1 mph = 1.60934 km/h
GALLON_TO_LITER = 3.78541  # 1 US gallon = 3.78541 liters


def convert_power_hp_to_kw(horsepower: float) -> float:
    """
    Convert power from horsepower to kilowatts.

    Args:
        horsepower: Power in horsepower (hp)

    Returns:
        Power in kilowatts (kW)

    Example:
        >>> convert_power_hp_to_kw(100)
        74.57
    """
    return round(horsepower * HP_TO_KW, 2)


def convert_torque_lbft_to_nm(torque_lbft: float) -> float:
    """
    Convert torque from pound-feet to Newton-meters.

    Args:
        torque_lbft: Torque in pound-feet (lb-ft)

    Returns:
        Torque in Newton-meters (Nm)

    Example:
        >>> convert_torque_lbft_to_nm(73.8)
        100.06
    """
    return round(torque_lbft * LBFT_TO_NM, 2)


def convert_length_inches_to_mm(inches: float) -> float:
    """
    Convert length from inches to millimeters.

    Args:
        inches: Length in inches

    Returns:
        Length in millimeters (mm)

    Example:
        >>> convert_length_inches_to_mm(10)
        254.0
    """
    return round(inches * INCH_TO_MM, 1)


def convert_length_feet_to_mm(feet: float) -> float:
    """
    Convert length from feet to millimeters.

    Args:
        feet: Length in feet

    Returns:
        Length in millimeters (mm)

    Example:
        >>> convert_length_feet_to_mm(5)
        1524.0
    """
    return round(feet * FOOT_TO_MM, 1)


def convert_weight_lbs_to_kg(pounds: float) -> float:
    """
    Convert weight from pounds to kilograms.

    Args:
        pounds: Weight in pounds (lbs)

    Returns:
        Weight in kilograms (kg)

    Example:
        >>> convert_weight_lbs_to_kg(440)
        199.58
    """
    return round(pounds * LBS_TO_KG, 2)


def convert_speed_mph_to_kmh(mph: float) -> float:
    """
    Convert speed from miles per hour to kilometers per hour.

    Args:
        mph: Speed in miles per hour

    Returns:
        Speed in kilometers per hour (km/h)

    Example:
        >>> convert_speed_mph_to_kmh(100)
        160.93
    """
    return round(mph * MPH_TO_KMH, 2)


def convert_volume_gallons_to_liters(gallons: float) -> float:
    """
    Convert volume from US gallons to liters.

    Args:
        gallons: Volume in US gallons

    Returns:
        Volume in liters (L)

    Example:
        >>> convert_volume_gallons_to_liters(5)
        18.93
    """
    return round(gallons * GALLON_TO_LITER, 2)


def convert_fuel_consumption_mpg_to_l100km(mpg: float) -> float:
    """
    Convert fuel consumption from miles per gallon to liters per 100 kilometers.

    Args:
        mpg: Fuel consumption in miles per gallon (US)

    Returns:
        Fuel consumption in liters per 100 kilometers (L/100km)

    Example:
        >>> convert_fuel_consumption_mpg_to_l100km(50)
        4.70
    """
    if mpg <= 0:
        return 0.0
    return round(235.214 / mpg, 2)


def parse_spec_value(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse numeric value and unit from text string.

    Handles various formats:
    - "100 hp" -> (100.0, "hp")
    - "73.8 lb-ft" -> (73.8, "lb-ft")
    - "~450 lbs" -> (450.0, "lbs")
    - "150-200 kg" -> (175.0, "kg")  # Takes midpoint of range

    Args:
        text: Text containing numeric value and unit

    Returns:
        Tuple of (value, unit) or (None, None) if parsing fails

    Example:
        >>> parse_spec_value("100 hp @ 9000 rpm")
        (100.0, 'hp')
        >>> parse_spec_value("73.8 lb-ft")
        (73.8, 'lb-ft')
        >>> parse_spec_value("150-200 kg")
        (175.0, 'kg')
    """
    if not text or not isinstance(text, str):
        return (None, None)

    # Remove approximate indicators
    text = text.replace('~', '').replace('approx.', '').replace('approximately', '').strip()

    # Pattern to match number with optional decimal, optional range, and unit
    # Examples: "100 hp", "73.8 lb-ft", "150-200 kg", "5.5 L"
    pattern = r'([\d.]+)(?:\s*[-–]\s*([\d.]+))?\s*([a-zA-Z][a-zA-Z./\-]*)'

    match = re.search(pattern, text)
    if match:
        value1 = float(match.group(1))
        value2 = match.group(2)
        unit = match.group(3).strip()

        # If range, take midpoint
        if value2:
            value = (value1 + float(value2)) / 2
        else:
            value = value1

        return (value, unit)

    # Try to extract just a number if unit is not found
    number_pattern = r'([\d.]+)'
    match = re.search(number_pattern, text)
    if match:
        return (float(match.group(1)), None)

    return (None, None)


def convert_to_metric(value: float, unit: str, target_unit: str) -> Optional[float]:
    """
    Convert value from source unit to metric target unit.

    Args:
        value: Numeric value to convert
        unit: Source unit (e.g., "hp", "lb-ft", "lbs")
        target_unit: Target metric unit (e.g., "kW", "Nm", "kg")

    Returns:
        Converted value in target unit, or None if conversion not supported

    Example:
        >>> convert_to_metric(100, "hp", "kW")
        74.57
        >>> convert_to_metric(440, "lbs", "kg")
        199.58
    """
    # Normalize unit strings
    unit = unit.lower().strip()
    target_unit = target_unit.lower().strip()

    # Power conversions
    if unit in ['hp', 'horsepower', 'bhp'] and target_unit in ['kw', 'kilowatt', 'kilowatts']:
        return convert_power_hp_to_kw(value)

    # Torque conversions
    if unit in ['lb-ft', 'lbft', 'lb.ft', 'ft-lb', 'ft.lb'] and target_unit in ['nm', 'n-m', 'newton-meter']:
        return convert_torque_lbft_to_nm(value)

    # Length conversions
    if unit in ['in', 'inch', 'inches', '"'] and target_unit in ['mm', 'millimeter', 'millimeters']:
        return convert_length_inches_to_mm(value)
    if unit in ['ft', 'foot', 'feet', "'"] and target_unit in ['mm', 'millimeter', 'millimeters']:
        return convert_length_feet_to_mm(value)

    # Weight conversions
    if unit in ['lb', 'lbs', 'pound', 'pounds'] and target_unit in ['kg', 'kilogram', 'kilograms']:
        return convert_weight_lbs_to_kg(value)

    # Speed conversions
    if unit in ['mph', 'mi/h'] and target_unit in ['km/h', 'kmh', 'kph']:
        return convert_speed_mph_to_kmh(value)

    # Volume conversions
    if unit in ['gal', 'gallon', 'gallons'] and target_unit in ['l', 'liter', 'liters', 'litre', 'litres']:
        return convert_volume_gallons_to_liters(value)

    # Fuel consumption conversions
    if unit in ['mpg', 'mi/gal'] and target_unit in ['l/100km', 'l/100 km']:
        return convert_fuel_consumption_mpg_to_l100km(value)

    # If already in metric or no conversion needed
    if unit == target_unit:
        return value

    return None
