"""Unit tests for unit conversion functions."""
import pytest
from src.utils.units import (
    convert_power_hp_to_kw,
    convert_torque_lbft_to_nm,
    convert_length_inches_to_mm,
    convert_weight_lbs_to_kg,
    convert_speed_mph_to_kmh,
    convert_volume_gallons_to_liters,
    convert_fuel_consumption_mpg_to_l100km,
    parse_spec_value,
    convert_to_metric
)


def test_convert_power_hp_to_kw():
    assert convert_power_hp_to_kw(100) == 74.57
    assert convert_power_hp_to_kw(50) == 37.29


def test_convert_torque_lbft_to_nm():
    assert convert_torque_lbft_to_nm(73.8) == 100.06
    assert convert_torque_lbft_to_nm(50) == 67.79


def test_convert_length_inches_to_mm():
    assert convert_length_inches_to_mm(10) == 254.0
    assert convert_length_inches_to_mm(1) == 25.4


def test_convert_weight_lbs_to_kg():
    assert convert_weight_lbs_to_kg(440) == 199.58
    assert convert_weight_lbs_to_kg(100) == 45.36


def test_convert_speed_mph_to_kmh():
    assert convert_speed_mph_to_kmh(100) == 160.93
    assert convert_speed_mph_to_kmh(60) == 96.56


def test_parse_spec_value():
    assert parse_spec_value("100 hp") == (100.0, "hp")
    assert parse_spec_value("73.8 lb-ft") == (73.8, "lb-ft")
    assert parse_spec_value("~450 lbs") == (450.0, "lbs")
    assert parse_spec_value("150-200 kg") == (175.0, "kg")
    assert parse_spec_value("invalid") == (None, None)


def test_convert_to_metric():
    assert convert_to_metric(100, "hp", "kW") == 74.57
    assert convert_to_metric(440, "lbs", "kg") == 199.58
    assert convert_to_metric(100, "mph", "km/h") == 160.93
    assert convert_to_metric(5, "gallons", "L") == 18.93
