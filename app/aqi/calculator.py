"""
Indian AQI Calculator Engine.

Calculates sub-indices and overall Air Quality Index according to the official CPCB methodology.
Isolated from forecasting engine.
"""

from typing import Dict, Any, Optional
from app.aqi.breakpoints import CPCB_BREAKPOINTS, CPCB_CATEGORIES


def calculate_sub_index(concentration: Optional[float], pollutant_key: str) -> Optional[float]:
    """Calculates CPCB AQI sub-index for a given pollutant concentration.
    
    Formula:
        Ip = I_low + ((I_high - I_low) / (C_high - C_low)) * (Cp - C_low)
    """
    if concentration is None or concentration < 0:
        return None
        
    key = pollutant_key.lower()
    if key not in CPCB_BREAKPOINTS:
        return None
        
    ranges = CPCB_BREAKPOINTS[key]["ranges"]
    
    # Check lower boundary
    if concentration <= ranges[0][0]:
        return float(ranges[0][2])
        
    for c_low, c_high, i_low, i_high in ranges:
        if c_low <= concentration <= c_high:
            sub = i_low + ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low)
            return round(sub, 1)
            
    # Beyond highest breakpoint (severe extension)
    max_c_high = ranges[-1][1]
    max_i_high = ranges[-1][3]
    if concentration > max_c_high:
        return 500.0
        
    return None


def get_aqi_category(aqi_value: float) -> Dict[str, str]:
    """Maps AQI numerical score to official CPCB AQI category and hex color."""
    val = round(aqi_value)
    for lo, hi, category, color in CPCB_CATEGORIES:
        if lo <= val <= hi:
            return {"category": category, "color_hex": color}
    return {"category": "Severe", "color_hex": "#660099"}


def calculate_indian_aqi(
    pm25: Optional[float] = None,
    pm10: Optional[float] = None,
    o3: Optional[float] = None,
    no2: Optional[float] = None,
    so2: Optional[float] = None,
    co: Optional[float] = None,
    nh3: Optional[float] = None,
    pb: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculates overall CPCB Indian AQI and sub-indices for all available pollutants.
    
    Returns:
        - overall_aqi: int (maximum of sub-indices)
        - dominant_pollutant: str (pollutant giving the highest sub-index)
        - aqi_category: str
        - color_hex: str
        - sub_indices: dict of pollutant sub-indices
        - concentrations: dict of input concentrations
        - reference: CPCB 2014 Guidelines
    """
    inputs = {
        "pm25": pm25,
        "pm10": pm10,
        "o3": o3,
        "no2": no2,
        "so2": so2,
        "co": co,
        "nh3": nh3,
        "pb": pb,
    }
    
    sub_indices: Dict[str, Optional[float]] = {}
    valid_subs: Dict[str, float] = {}
    
    for key, conc in inputs.items():
        if conc is not None:
            sub = calculate_sub_index(conc, key)
            sub_indices[key] = sub
            if sub is not None:
                display_name = CPCB_BREAKPOINTS[key]["pollutant_name"]
                valid_subs[display_name] = sub
        else:
            sub_indices[key] = None
            
    if not valid_subs:
        return {
            "overall_aqi": None,
            "dominant_pollutant": None,
            "aqi_category": "Insufficient Data",
            "color_hex": "#cccccc",
            "sub_indices": sub_indices,
            "concentrations": inputs,
            "reference": "CPCB National Air Quality Index Guidelines (2014)",
        }
        
    # Dominant pollutant is the one with the maximum sub-index
    dominant_name = max(valid_subs, key=lambda k: valid_subs[k])
    overall_aqi = round(valid_subs[dominant_name])
    category_info = get_aqi_category(overall_aqi)
    
    return {
        "overall_aqi": overall_aqi,
        "dominant_pollutant": dominant_name,
        "aqi_category": category_info["category"],
        "color_hex": category_info["color_hex"],
        "sub_indices": sub_indices,
        "concentrations": inputs,
        "reference": "CPCB National Air Quality Index Guidelines (2014)",
    }
