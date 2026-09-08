"""
AirSync Mass-Balance Box Model Module.

Implements a dimensionally consistent single-box atmospheric mass balance equation:

    dC/dt = (E / H) - (U / L)*(C - C_bg) - (v_d / H)*C - Lambda(R)*C + P_chem

where:
    C    : Pollutant concentration [µg/m³]
    E    : Surface emission flux rate [µg/(m²·s)]
    H    : Planetary boundary layer mixing height (PBLH) [m]
    U    : Wind speed [m/s]
    L    : Characteristic domain length scale [m]
    C_bg : Background upwind concentration [µg/m³]
    v_d  : Dry deposition velocity [m/s]
    Lambda(R) : Wet scavenging rate coefficient [s⁻¹] (Lambda = a * R^b)
    P_chem : Photochemical production proxy rate [µg/(m³·s)]
"""

import math
from typing import Dict, Any, Optional
from app.physics.parameters import (
    DOMAIN_CHARACTERISTIC_LENGTH_M,
    DRY_DEPOSITION_VELOCITY_M_S,
    RAIN_SCAVENGING_A,
    RAIN_SCAVENGING_B,
    BACKGROUND_CONCENTRATIONS_UGM3,
    URBAN_EMISSION_FLUX_UGM2S,
    MIN_PBL_HEIGHT_M,
)


def calculate_wet_scavenging_rate(pollutant: str, precipitation_mm_h: float) -> float:
    """Calculates wet scavenging rate Lambda(R) in s^-1.
    
    Formula: Lambda(R) = a * R^b
    where R is precipitation rate in mm/h.
    Returns 0.0 if precipitation_mm_h <= 0.
    """
    if precipitation_mm_h <= 0.0:
        return 0.0
    
    a = RAIN_SCAVENGING_A.get(pollutant.lower(), 1.0e-4)
    b = RAIN_SCAVENGING_B
    return a * math.pow(precipitation_mm_h, b)


def calculate_photochemical_o3_rate(
    temperature_c: float,
    solar_radiation_wm2: float,
    cloud_cover_pct: float,
    no2_ugm3: Optional[float] = None
) -> float:
    """Calculates a simplified photochemical O3 production rate proxy P_chem in µg/(m³·s).
    
    NOTE: Ozone formation is a complex nonlinear photochemistry function of NOx, VOCs, UV flux,
    and temperature. This function serves as a simplified photochemical activity proxy, NOT
    a full chemical transport model mechanism (e.g., CB05/SAPRC).
    """
    if solar_radiation_wm2 <= 5.0 or temperature_c <= 5.0:
        return 0.0  # No solar photolysis at night or freezing temperatures
    
    # Radiative index normalized to peak noon solar (~1000 W/m²)
    radiation_factor = max(0.0, solar_radiation_wm2 / 1000.0)
    # Temperature enhancement factor (O3 formation accelerates above 25°C)
    temp_factor = max(0.0, (temperature_c - 15.0) / 25.0)
    # Cloud attenuation
    cloud_factor = max(0.1, 1.0 - (cloud_cover_pct / 100.0) * 0.8)
    
    # Precursor factor (NO2 proxy if available, otherwise nominal urban precursor factor)
    precursor_factor = (no2_ugm3 / 40.0) if (no2_ugm3 is not None and no2_ugm3 > 0) else 1.0
    precursor_factor = min(2.0, max(0.2, precursor_factor))
    
    # Production rate proxy: Peak production ~ 0.005 µg/(m³·s) under intense midday sun & heat
    p_chem = 0.005 * radiation_factor * temp_factor * cloud_factor * precursor_factor
    return max(0.0, p_chem)


def integrate_box_model_step(
    c_current: float,
    pollutant: str,
    wind_speed_ms: float,
    pbl_height_m: float,
    precipitation_mm_h: float = 0.0,
    solar_radiation_wm2: float = 0.0,
    temperature_c: float = 25.0,
    cloud_cover_pct: float = 0.0,
    fire_influence: float = 0.0,
    no2_ugm3: Optional[float] = None,
    dt_seconds: float = 3600.0,
    domain_length_m: float = DOMAIN_CHARACTERISTIC_LENGTH_M,
) -> Dict[str, float]:
    """Integrates the single-box mass balance differential equation over timestep dt.
    
    Returns a dictionary containing:
        - c_next: New concentration [µg/m³]
        - loss_rate_s1: Total first-order loss rate [s⁻¹]
        - equilibrium_conc: Steady-state asymptotic concentration [µg/m³]
        - ventilation_rate_s1: Advective ventilation loss rate [s⁻¹]
        - dry_dep_rate_s1: Dry deposition loss rate [s⁻¹]
        - wet_scav_rate_s1: Wet scavenging loss rate [s⁻¹]
        - emission_rate_volumetric: Volumetric source rate [µg/(m³·s)]
    """
    key = pollutant.lower()
    
    # Physical boundaries
    h = max(MIN_PBL_HEIGHT_M, pbl_height_m)
    u = max(0.1, wind_speed_ms)  # Non-zero minimum advection speed
    
    # Loss rate terms [s⁻¹]
    v_advection = u / domain_length_m  # Advective flushing rate [s⁻¹]
    v_d = DRY_DEPOSITION_VELOCITY_M_S.get(key, 0.001)
    v_dry_dep = v_d / h                # Dry deposition loss rate [s⁻¹]
    v_wet_scav = calculate_wet_scavenging_rate(key, precipitation_mm_h) # Wet removal [s⁻¹]
    
    k_loss = v_advection + v_dry_dep + v_wet_scav  # Total loss coefficient [s⁻¹]
    
    # Volumetric Source terms [µg/(m³·s)]
    c_bg = BACKGROUND_CONCENTRATIONS_UGM3.get(key, 20.0)
    e_surface = URBAN_EMISSION_FLUX_UGM2S.get(key, 0.4)
    
    # Add biomass burning fire emission boost if applicable
    if key in ["pm25", "pm10", "co"]:
        e_surface += fire_influence * 1.5  # Fire emission proxy flux addition
        
    p_emission = e_surface / h  # Volumetric surface emission source [µg/(m³·s)]
    p_advection = v_advection * c_bg  # Inflow background source [µg/(m³·s)]
    
    p_chem = 0.0
    if key == "o3":
        p_chem = calculate_photochemical_o3_rate(temperature_c, solar_radiation_wm2, cloud_cover_pct, no2_ugm3)
        
    p_total = p_emission + p_advection + p_chem  # Total volumetric production [µg/(m³·s)]
    
    # Asymptotic steady-state concentration C_eq = P_total / k_loss [µg/m³]
    c_eq = p_total / k_loss
    
    # Analytical solution: C(t + dt) = C_eq + (C(t) - C_eq) * exp(-k_loss * dt)
    c_next = c_eq + (c_current - c_eq) * math.exp(-k_loss * dt_seconds)
    c_next = max(0.0, c_next)  # Non-negative mass constraint
    
    return {
        "c_next": c_next,
        "loss_rate_s1": k_loss,
        "equilibrium_conc": c_eq,
        "ventilation_rate_s1": v_advection,
        "dry_dep_rate_s1": v_dry_dep,
        "wet_scav_rate_s1": v_wet_scav,
        "emission_rate_volumetric": p_emission,
    }
