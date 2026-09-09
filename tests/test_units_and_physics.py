"""
Unit tests for AirSync physical unit sanity, box model mass balance, and physical sensitivity rules.
"""

import pytest
from app.physics.box_model import integrate_box_model_step
from app.physics.diagnostics import calculate_ventilation_coefficient, calculate_accumulation_potential


def test_ventilation_coefficient_increases_with_wind():
    """Sanity Check: Higher wind speed MUST increase ventilation coefficient."""
    vc_low = calculate_ventilation_coefficient(
        speed_ms=1.0, pbl_height_m=500.0)
    vc_high = calculate_ventilation_coefficient(
        speed_ms=5.0, pbl_height_m=500.0)

    assert vc_low == 500.0
    assert vc_high == 2500.0
    assert vc_high > vc_low


def test_accumulation_potential_higher_for_lower_pbl():
    """Sanity Check: Lower PBL height MUST increase accumulation potential score."""
    acc_high_pbl = calculate_accumulation_potential(
        speed_ms=2.0, pbl_height_m=1200.0)
    acc_low_pbl = calculate_accumulation_potential(
        speed_ms=2.0, pbl_height_m=200.0)

    assert acc_low_pbl["accumulation_potential_score"] > acc_high_pbl["accumulation_potential_score"]
    assert acc_low_pbl["poor_ventilation"] is True


def test_rainfall_scavenging_reduces_pm25_concentration():
    """Sanity Check: Rainfall MUST reduce PM2.5 concentration via wet scavenging."""
    step_no_rain = integrate_box_model_step(
        c_current=150.0,
        pollutant="pm25",
        wind_speed_ms=2.0,
        pbl_height_m=500.0,
        precipitation_mm_h=0.0)
    step_heavy_rain = integrate_box_model_step(
        c_current=150.0,
        pollutant="pm25",
        wind_speed_ms=2.0,
        pbl_height_m=500.0,
        precipitation_mm_h=10.0)

    assert step_heavy_rain["c_next"] < step_no_rain["c_next"]
    assert step_heavy_rain["wet_scav_rate_s1"] > step_no_rain["wet_scav_rate_s1"]


def test_box_model_dimensional_non_negativity():
    """Dimensional Sanity: Concentrations must never drop below 0."""
    res = integrate_box_model_step(
        c_current=10.0,
        pollutant="pm25",
        wind_speed_ms=20.0,
        pbl_height_m=1000.0,
        precipitation_mm_h=50.0)
    assert res["c_next"] >= 0.0
