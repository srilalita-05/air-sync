"""
AirSync Physics Engine Parameters.

Centralized empirical baseline parameters and tunable coefficients.
NOTE: These values represent parameterized approximations for urban Delhi-NCR domains.
They are NOT fundamental physical constants and can be calibrated against observation data.
"""

from typing import Dict

# Domain & Box Model Geometry Parameters
# L = 50 km (approximate Delhi urban core scale)
DOMAIN_CHARACTERISTIC_LENGTH_M: float = 50000.0
# Default daytime mixing height (m)
DEFAULT_PBL_HEIGHT_M: float = 800.0
# Minimum nocturnal stability PBL threshold (m)
MIN_PBL_HEIGHT_M: float = 100.0

# Dry Deposition Velocities (v_d in m/s)
# Values typical of atmospheric boundary layer literature for urban
# aerosols & gases
DRY_DEPOSITION_VELOCITY_M_S: Dict[str, float] = {
    "pm25": 0.0010,  # 1.0 mm/s for fine particulates
    "pm10": 0.0050,  # 5.0 mm/s for coarse particulates
    "o3": 0.0040,    # 4.0 mm/s surface reaction on soil/vegetation
    "no2": 0.0015,   # 1.5 mm/s
    "so2": 0.0060,   # 6.0 mm/s
    "co": 0.0001,    # negligible dry deposition
}

# Rain Scavenging Parameters: Lambda(R) = a * R^b  (R in mm/h, Lambda in s^-1)
# Parameters based on empirical washout studies (e.g., Mircea et al.)
RAIN_SCAVENGING_A: Dict[str, float] = {
    "pm25": 1.0e-4,  # Coefficient a for PM2.5
    # Coefficient a for PM10 (coarser particles washed out faster)
    "pm10": 3.0e-4,
    "o3": 2.0e-5,    # Low solubility
    "no2": 3.0e-5,
    "so2": 1.5e-4,    # High solubility (acid precipitation precursor)
    "co": 1.0e-6,    # Insoluble gas
}
RAIN_SCAVENGING_B: float = 0.8  # Exponent b

# Background Upwind Concentrations - Pristine/rural background priors
# NOTE: All pollutants are in µg/m³ EXCEPT CO which is in mg/m³ (matching
# co_mgm3 convention)
BACKGROUND_CONCENTRATIONS_UGM3: Dict[str, float] = {
    "pm25": 25.0,
    "pm10": 45.0,
    "o3": 35.0,
    "no2": 15.0,
    "so2": 10.0,
    # mg/m³ (not µg/m³) — consistent with co_mgm3 tracking unit
    "co": 0.5,
}

# Urban Emission Proxy Flux Rates - Default baseline urban traffic/domestic emissions
# NOTE: All pollutants in µg/(m²·s) EXCEPT CO in mg/(m²·s) to match
# co_mgm3 convention
URBAN_EMISSION_FLUX_UGM2S: Dict[str, float] = {
    "pm25": 0.45,   # µg/(m²·s) baseline urban emission flux
    "pm10": 0.90,   # µg/(m²·s)
    "o3": 0.00,     # Primary emission is zero (O3 is secondary)
    "no2": 0.35,    # µg/(m²·s)
    "so2": 0.15,    # µg/(m²·s)
    "co": 0.0025,   # mg/(m²·s) — was 2.50 µg/(m²·s) = 0.0025 mg/(m²·s)
}

# Ventilation & Diagnostic Thresholds
# VC >= 5000 m²/s -> good dispersion
GOOD_VENTILATION_THRESHOLD_M2S: float = 5000.0
# VC <= 1500 m²/s -> poor ventilation / stagnation
POOR_VENTILATION_THRESHOLD_M2S: float = 1500.0
# VC <= 800 m²/s -> severe accumulation risk
SEVERE_STAGNATION_THRESHOLD_M2S: float = 800.0
LOW_WIND_THRESHOLD_MS: float = 1.5               # Stagnant surface wind (m/s)
# Shallow boundary layer threshold (m)
LOW_PBL_THRESHOLD_M: float = 300.0
