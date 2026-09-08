"""
AirSync Physics Engine Parameters.

Centralized empirical baseline parameters and tunable coefficients.
NOTE: These values represent parameterized approximations for urban Delhi-NCR domains.
They are NOT fundamental physical constants and can be calibrated against observation data.
"""

from typing import Dict

# Domain & Box Model Geometry Parameters
DOMAIN_CHARACTERISTIC_LENGTH_M: float = 50000.0  # L = 50 km (approximate Delhi urban core scale)
DEFAULT_PBL_HEIGHT_M: float = 800.0              # Default daytime mixing height (m)
MIN_PBL_HEIGHT_M: float = 100.0                  # Minimum nocturnal stability PBL threshold (m)

# Dry Deposition Velocities (v_d in m/s)
# Values typical of atmospheric boundary layer literature for urban aerosols & gases
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
    "pm10": 3.0e-4,  # Coefficient a for PM10 (coarser particles washed out faster)
    "o3": 2.0e-5,    # Low solubility
    "no2": 3.0e-5,
    "so2": 1.5e-4,    # High solubility (acid precipitation precursor)
    "co": 1.0e-6,    # Insoluble gas
}
RAIN_SCAVENGING_B: float = 0.8  # Exponent b

# Background Upwind Concentrations (C_bg in µg/m³) - Pristine/rural background priors
BACKGROUND_CONCENTRATIONS_UGM3: Dict[str, float] = {
    "pm25": 25.0,
    "pm10": 45.0,
    "o3": 35.0,
    "no2": 15.0,
    "so2": 10.0,
    "co": 0.5,
}

# Urban Emission Proxy Flux Rates (E in µg/(m²·s)) - Default baseline urban traffic/domestic emissions
URBAN_EMISSION_FLUX_UGM2S: Dict[str, float] = {
    "pm25": 0.45,   # Baseline urban emission flux
    "pm10": 0.90,
    "o3": 0.00,     # Primary emission is zero (O3 is secondary)
    "no2": 0.35,
    "so2": 0.15,
    "co": 2.50,
}

# Ventilation & Diagnostic Thresholds
GOOD_VENTILATION_THRESHOLD_M2S: float = 5000.0   # VC >= 5000 m²/s -> good dispersion
POOR_VENTILATION_THRESHOLD_M2S: float = 1500.0   # VC <= 1500 m²/s -> poor ventilation / stagnation
SEVERE_STAGNATION_THRESHOLD_M2S: float = 800.0   # VC <= 800 m²/s -> severe accumulation risk
LOW_WIND_THRESHOLD_MS: float = 1.5               # Stagnant surface wind (m/s)
LOW_PBL_THRESHOLD_M: float = 300.0               # Shallow boundary layer threshold (m)
