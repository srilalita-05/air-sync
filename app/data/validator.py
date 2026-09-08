"""
AirSync Data Ingestion Validator and Imputation Module.

Validates incoming meteorological and pollutant payload data, handling missing variables
gracefully without failing or inventing fake measurements.
"""

from typing import Dict, Any, List, Tuple


REQUIRED_METEOROLOGICAL_FIELDS = [
    "timestamp", "latitude", "longitude", "temperature_c", "relative_humidity",
    "pressure_hpa", "wind_speed_ms", "wind_direction_deg", "pbl_height_m"
]

FALLBACK_DEFAULTS = {
    "precipitation_mm": 0.0,
    "solar_radiation_wm2": 0.0,
    "cloud_cover_pct": 0.0,
    "fire_influence": 0.0,
}


def validate_and_clean_input(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates raw input dictionary, checking required fields and applying physical bounds checks.
    
    Returns:
        - is_valid: bool
        - cleaned_data: dict
        - missing_variables: list
        - warnings: list
    """
    missing_required = []
    warnings = []
    cleaned = dict(raw_data)
    
    for field in REQUIRED_METEOROLOGICAL_FIELDS:
        if field not in cleaned or cleaned[field] is None:
            missing_required.append(field)
            
    # Impute non-critical optional defaults if missing
    for field, default_val in FALLBACK_DEFAULTS.items():
        if field not in cleaned or cleaned[field] is None:
            cleaned[field] = default_val
            warnings.append(f"Optional variable '{field}' was missing; defaulted to {default_val}.")
            
    # Range validations
    if "temperature_c" in cleaned and cleaned["temperature_c"] is not None:
        val = cleaned["temperature_c"]
        if val < -30.0 or val > 60.0:
            warnings.append(f"Unusual temperature value: {val} °C.")
            
    if "relative_humidity" in cleaned and cleaned["relative_humidity"] is not None:
        cleaned["relative_humidity"] = max(0.0, min(100.0, float(cleaned["relative_humidity"])))
        
    if "wind_speed_ms" in cleaned and cleaned["wind_speed_ms"] is not None:
        cleaned["wind_speed_ms"] = max(0.0, float(cleaned["wind_speed_ms"]))
        
    if "pbl_height_m" in cleaned and cleaned["pbl_height_m"] is not None:
        cleaned["pbl_height_m"] = max(20.0, float(cleaned["pbl_height_m"]))

    is_valid = (len(missing_required) == 0)
    
    return {
        "is_valid": is_valid,
        "cleaned_data": cleaned,
        "missing_required_variables": missing_required,
        "warnings": warnings,
    }
