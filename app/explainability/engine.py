"""
AirSync Explainability Engine ("WHY?").

Translates raw meteorology and calculated physics diagnostics into structured, human-readable
driver attribution reports explaining WHY pollution is increasing, decreasing, or peaking.

Architecture:
    RAW INPUTS -> PHYSICS DIAGNOSTICS -> DRIVER ATTRIBUTION -> HUMAN-READABLE EXPLANATION
"""

from typing import Dict, List, Any, Optional


def generate_explanation(
    weather_input: Dict[str, Any],
    physics_diagnostics: Dict[str, Any],
    pollutant_baseline: Dict[str, float]
) -> Dict[str, Any]:
    """Generates structured driver attribution breakdown from actual model inputs and physics diagnostics.
    
    Returns:
        - dominant_driver: str
        - drivers: List of driver dicts (name, severity, value, unit, description)
        - narrative_summary: Human readable text
    """
    drivers: List[Dict[str, Any]] = []
    
    speed = float(weather_input.get("wind_speed_ms", 2.0))
    pbl = float(weather_input.get("pbl_height_m", 800.0))
    precip = float(weather_input.get("precipitation_mm", 0.0))
    temp = float(weather_input.get("temperature_c", 25.0))
    solar = float(weather_input.get("solar_radiation_wm2", 0.0))
    fire = float(weather_input.get("fire_influence", 0.0))
    rh = float(weather_input.get("relative_humidity", 50.0))
    
    vc = physics_diagnostics.get("ventilation_coefficient_m2s", speed * pbl)
    accum = physics_diagnostics.get("accumulation", {})
    inversion = physics_diagnostics.get("inversion", {})
    photo = physics_diagnostics.get("photochemical_activity_proxy", 0.0)
    
    # 1. Ventilation Driver
    if vc <= 800.0:
        drivers.append({
            "name": "severe_stagnation",
            "severity": "critical",
            "value": round(vc, 1),
            "unit": "m²/s",
            "description": "Severe atmospheric stagnation (ventilation coefficient < 800 m²/s) trapping local emissions.",
        })
    elif vc <= 1500.0:
        drivers.append({
            "name": "poor_ventilation",
            "severity": "high",
            "value": round(vc, 1),
            "unit": "m²/s",
            "description": "Poor atmospheric ventilation (ventilation coefficient < 1500 m²/s) limiting pollutant dispersion.",
        })
    elif vc >= 5000.0:
        drivers.append({
            "name": "strong_dispersion",
            "severity": "beneficial",
            "value": round(vc, 1),
            "unit": "m²/s",
            "description": "Strong atmospheric dispersion (ventilation coefficient > 5000 m²/s) rapidly flushing pollutants.",
        })

    # 2. Surface Wind Speed
    if speed <= 1.5:
        drivers.append({
            "name": "low_wind",
            "severity": "high",
            "value": round(speed, 1),
            "unit": "m/s",
            "description": "Calm surface wind (< 1.5 m/s) prevents horizontal pollutant transport.",
        })
    elif speed >= 6.0:
        drivers.append({
            "name": "high_wind_flushing",
            "severity": "beneficial",
            "value": round(speed, 1),
            "unit": "m/s",
            "description": "Strong surface wind (> 6.0 m/s) enhances horizontal advective transport.",
        })

    # 3. Mixing Height (PBLH)
    if pbl <= 300.0:
        drivers.append({
            "name": "low_pbl",
            "severity": "high",
            "value": round(pbl, 1),
            "unit": "m",
            "description": "Shallow boundary layer (< 300 m) compresses pollutants into a small atmospheric volume.",
        })

    # 4. Thermal Inversion (ONLY if vertical temperature data is available and detected)
    if inversion.get("inversion_detected") is True:
        lapse = inversion.get("lapse_rate_c_100m", 0.0)
        drivers.append({
            "name": "thermal_inversion",
            "severity": "critical",
            "value": lapse,
            "unit": "°C/100m",
            "description": "Confirmed thermal inversion (temperature increases with height) creating a stable lid over Delhi.",
        })

    # 5. Precipitation Scavenging
    if precip >= 2.0:
        drivers.append({
            "name": "rainfall_scavenging",
            "severity": "beneficial",
            "value": round(precip, 1),
            "unit": "mm/h",
            "description": "Rainfall (> 2.0 mm/h) actively washes out particulate matter via wet deposition.",
        })
    elif precip == 0.0:
        drivers.append({
            "name": "no_rainfall",
            "severity": "moderate",
            "value": 0.0,
            "unit": "mm/h",
            "description": "Absence of precipitation allows aerosol buildup without wet scavenging removal.",
        })

    # 6. Biomass Burning Fire Plume Influence
    if fire >= 0.3:
        drivers.append({
            "name": "upwind_fire_influence",
            "severity": "high",
            "value": round(fire, 2),
            "unit": "index (0-1)",
            "description": "Significant upwind agricultural biomass burning detected by NASA FIRMS contributing downwind smoke.",
        })

    # 7. Photochemical O3 Production
    if solar >= 500.0 and temp >= 30.0:
        drivers.append({
            "name": "photochemical_o3_peak",
            "severity": "high",
            "value": round(solar, 1),
            "unit": "W/m²",
            "description": "High solar radiation and temperature accelerate secondary photochemical Ozone formation.",
        })

    # Determine Dominant Driver
    if not drivers:
        dominant = "normal_baseline"
    else:
        # Sort by severity rank: critical > high > moderate > beneficial
        rank_order = {"critical": 4, "high": 3, "moderate": 2, "beneficial": 1}
        sorted_drivers = sorted(drivers, key=lambda d: rank_order.get(d["severity"], 0), reverse=True)
        dominant = sorted_drivers[0]["name"]

    # Generate Human Readable Narrative
    narrative_parts = []
    if dominant in ["severe_stagnation", "poor_ventilation", "low_pbl", "thermal_inversion"]:
        narrative_parts.append(f"Pollution accumulation is driven by atmospheric trapping (Ventilation VC = {vc:.0f} m²/s, PBLH = {pbl:.0f} m).")
    elif dominant == "upwind_fire_influence":
        narrative_parts.append(f"Pollution rise is heavily impacted by upwind biomass burning stubble fires.")
    elif dominant == "photochemical_o3_peak":
        narrative_parts.append(f"Ozone surge is driven by strong midday solar radiation ({solar:.0f} W/m²) and warmth ({temp:.1f} °C).")
    elif dominant == "rainfall_scavenging":
        narrative_parts.append(f"Pollution reduction is driven by wet scavenging rainfall removal ({precip:.1f} mm/h).")
    else:
        narrative_parts.append("Atmospheric dispersion and emission conditions are at baseline levels.")

    return {
        "dominant_driver": dominant,
        "drivers": drivers,
        "narrative_explanation": " ".join(narrative_parts),
    }
