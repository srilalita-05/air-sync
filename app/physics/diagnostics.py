"""
AirSync Physics Diagnostics Module.

Calculates reusable physical indicators and atmospheric state diagnostics derived directly
from input meteorology and physical fields.

Explicitly separates:
- Poor ventilation / accumulation potential (calculated from PBLH, wind speed, VC)
- Atmospheric stability / inversion indicator (ONLY calculated when vertical temperature data is present)
"""

import math
from typing import Dict, Any, Optional
from app.physics.parameters import (
    GOOD_VENTILATION_THRESHOLD_M2S,
    POOR_VENTILATION_THRESHOLD_M2S,
    LOW_WIND_THRESHOLD_MS,
    LOW_PBL_THRESHOLD_M,
)


def calculate_wind_components(speed_ms: float, direction_deg: float) -> Dict[str, float]:
    """Calculates zonal (u) and meridional (v) wind velocity components.
    
    Convention: Meteorological direction is the direction FROM which the wind blows.
    - u_east: positive towards East (m/s)
    - v_north: positive towards North (m/s)
    """
    rad = math.radians(direction_deg)
    u_east = -speed_ms * math.sin(rad)
    v_north = -speed_ms * math.cos(rad)
    return {"u_east": u_east, "v_north": v_north}


def calculate_ventilation_coefficient(speed_ms: float, pbl_height_m: float) -> float:
    """Calculates the ventilation coefficient VC = U * PBLH in m²/s.
    
    Higher VC indicates strong atmospheric dispersion capacity.
    Lower VC indicates stagnant trapping conditions.
    """
    return max(0.0, speed_ms * pbl_height_m)


def calculate_inversion_indicator(
    temp_surface_c: Optional[float] = None,
    temp_upper_c: Optional[float] = None,
    delta_z_m: Optional[float] = None,
    lapse_rate_c_per_100m: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculates atmospheric stability / thermal inversion indicator.
    
    CRITICAL REQUIREMENT: An atmospheric temperature inversion (dT/dz > 0) can ONLY be confirmed
    when vertical atmospheric temperature profile data is available. Low PBL + low wind alone is NOT
    classified as an inversion.
    
    Returns:
        - inversion_detected: Optional[bool] (True, False, or None if vertical data missing)
        - lapse_rate_c_100m: Thermal lapse rate [°C/100m]
        - status: Description of vertical data availability
    """
    if lapse_rate_c_per_100m is not None:
        is_inversion = (lapse_rate_c_per_100m > 0.0)  # Inversion occurs when temp increases with height
        return {
            "inversion_detected": is_inversion,
            "lapse_rate_c_100m": round(lapse_rate_c_per_100m, 2),
            "status": "calculated_from_lapse_rate",
        }
        
    if temp_surface_c is not None and temp_upper_c is not None and delta_z_m is not None and delta_z_m > 0:
        # dT/dz in °C per 100m
        gamma = (temp_upper_c - temp_surface_c) / (delta_z_m / 100.0)
        is_inversion = (temp_upper_c > temp_surface_c)  # Warm air aloft trapping cold surface air
        return {
            "inversion_detected": is_inversion,
            "lapse_rate_c_100m": round(gamma, 2),
            "status": "calculated_from_vertical_temp_profile",
        }
        
    return {
        "inversion_detected": None,
        "lapse_rate_c_100m": None,
        "status": "vertical_data_unavailable",
    }


def calculate_accumulation_potential(
    speed_ms: float,
    pbl_height_m: float,
) -> Dict[str, Any]:
    """Calculates poor ventilation / accumulation potential.
    
    Uses surface wind speed, boundary layer mixing height, and ventilation coefficient
    to gauge atmosphere's tendency to trap surface emissions.
    
    Does NOT claim an inversion is present unless vertical temperature data was confirmed.
    """
    vc = calculate_ventilation_coefficient(speed_ms, pbl_height_m)
    
    # Normalized score between 0.0 (excellent ventilation) and 1.0 (severe accumulation)
    # Stagnation builds up below 1500 m²/s VC
    if vc >= GOOD_VENTILATION_THRESHOLD_M2S:
        score = max(0.0, 0.2 * (1.0 - (vc - GOOD_VENTILATION_THRESHOLD_M2S) / 10000.0))
    elif vc <= POOR_VENTILATION_THRESHOLD_M2S:
        score = 0.6 + 0.4 * (1.0 - vc / POOR_VENTILATION_THRESHOLD_M2S)
    else:
        score = 0.2 + 0.4 * (1.0 - (vc - POOR_VENTILATION_THRESHOLD_M2S) / (GOOD_VENTILATION_THRESHOLD_M2S - POOR_VENTILATION_THRESHOLD_M2S))
        
    score = max(0.0, min(1.0, score))
    
    is_poor_ventilation = (vc <= POOR_VENTILATION_THRESHOLD_M2S)
    is_severe_stagnation = (vc <= 800.0)
    
    return {
        "accumulation_potential_score": round(score, 3),
        "ventilation_coefficient_m2s": round(vc, 1),
        "poor_ventilation": is_poor_ventilation,
        "severe_stagnation": is_severe_stagnation,
        "is_low_wind": (speed_ms <= LOW_WIND_THRESHOLD_MS),
        "is_low_pbl": (pbl_height_m <= LOW_PBL_THRESHOLD_M),
    }


def calculate_all_diagnostics(
    speed_ms: float,
    direction_deg: float,
    pbl_height_m: float,
    precipitation_mm_h: float = 0.0,
    solar_radiation_wm2: float = 0.0,
    temperature_c: float = 25.0,
    cloud_cover_pct: float = 0.0,
    fire_influence: float = 0.0,
    temp_surface_c: Optional[float] = None,
    temp_upper_c: Optional[float] = None,
    delta_z_m: Optional[float] = None,
) -> Dict[str, Any]:
    """Generates complete suite of reusable physical indicators for downstream
    explainability, forecasting, and API payloads.
    """
    wind = calculate_wind_components(speed_ms, direction_deg)
    vc = calculate_ventilation_coefficient(speed_ms, pbl_height_m)
    accum = calculate_accumulation_potential(speed_ms, pbl_height_m)
    inversion = calculate_inversion_indicator(temp_surface_c, temp_upper_c, delta_z_m)
    
    # Scavenging diagnostic
    rain_active = (precipitation_mm_h > 0.1)
    
    # Photochemical activity proxy
    photo_score = 0.0
    if solar_radiation_wm2 > 10.0 and temperature_c > 10.0:
        solar_norm = min(1.0, solar_radiation_wm2 / 800.0)
        temp_norm = min(1.0, max(0.0, (temperature_c - 10.0) / 30.0))
        clear_sky = 1.0 - (cloud_cover_pct / 100.0)
        photo_score = min(1.0, 0.5 * solar_norm + 0.3 * temp_norm + 0.2 * clear_sky)
        
    return {
        "wind": wind,
        "ventilation_coefficient_m2s": round(vc, 1),
        "accumulation": accum,
        "inversion": inversion,
        "rain_scavenging_active": rain_active,
        "precipitation_rate_mm_h": precipitation_mm_h,
        "photochemical_activity_proxy": round(photo_score, 3),
        "biomass_fire_influence_score": round(fire_influence, 3),
    }
