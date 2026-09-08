"""
AirSync Physics Engine Coordinator.

Integrates mass-balance box model equations, advection diagnostics, rain scavenging,
and photochemical proxy estimations into a unified physics baseline prediction interface.
"""

from typing import Dict, Any, Optional
from app.physics.box_model import integrate_box_model_step
from app.physics.diagnostics import calculate_all_diagnostics, calculate_wind_components


def estimate_pollutants(inp, previous: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Physics-informed baseline forecast step over a 1-hour interval (dt = 3600 s).
    
    Uses dimensionally consistent mass-balance box modeling:
    - Advective flushing by surface wind
    - Planetary Boundary Layer volume dilution
    - Dry deposition on urban surfaces
    - Precipitation wet scavenging
    - Photochemical secondary formation (for O3 proxy)
    
    Accepts Pydantic model or dict containing weather & initial pollution fields.
    """
    # Extract weather parameters with fallback defaults
    wind_speed = float(getattr(inp, "wind_speed_ms", 2.0))
    wind_dir = float(getattr(inp, "wind_direction_deg", 270.0))
    pbl_h = float(getattr(inp, "pbl_height_m", 800.0))
    precip = float(getattr(inp, "precipitation_mm", 0.0))
    solar = float(getattr(inp, "solar_radiation_wm2", 0.0))
    temp = float(getattr(inp, "temperature_c", 25.0))
    cloud = float(getattr(inp, "cloud_cover_pct", 0.0))
    fire = float(getattr(inp, "fire_influence", 0.0))
    
    temp_surf = getattr(inp, "temp_surface_c", None)
    temp_upper = getattr(inp, "temp_upper_c", None)
    delta_z = getattr(inp, "delta_z_m", None)
    
    # Anchors for initial state
    pm25_init = float(getattr(inp, "pm25_ugm3", 80.0) if getattr(inp, "pm25_ugm3", None) is not None else 80.0)
    pm10_init = float(getattr(inp, "pm10_ugm3", 120.0) if getattr(inp, "pm10_ugm3", None) is not None else 120.0)
    o3_init = float(getattr(inp, "o3_ugm3", 45.0) if getattr(inp, "o3_ugm3", None) is not None else 45.0)
    no2_init = float(getattr(inp, "no2_ugm3", 35.0) if getattr(inp, "no2_ugm3", None) is not None else 35.0)
    so2_init = float(getattr(inp, "so2_ugm3", 15.0) if getattr(inp, "so2_ugm3", None) is not None else 15.0)
    co_init = float(getattr(inp, "co_mgm3", 1.2) if getattr(inp, "co_mgm3", None) is not None else 1.2)

    if previous:
        pm25_init = previous.get("pm25_ugm3", pm25_init)
        pm10_init = previous.get("pm10_ugm3", pm10_init)
        o3_init = previous.get("o3_ugm3", o3_init)
        no2_init = previous.get("no2_ugm3", no2_init)
        so2_init = previous.get("so2_ugm3", so2_init)
        co_init = previous.get("co_mgm3", co_init)

    # Compute step updates via box model
    step_pm25 = integrate_box_model_step(pm25_init, "pm25", wind_speed, pbl_h, precip, solar, temp, cloud, fire, no2_init)
    step_pm10 = integrate_box_model_step(pm10_init, "pm10", wind_speed, pbl_h, precip, solar, temp, cloud, fire, no2_init)
    step_o3 = integrate_box_model_step(o3_init, "o3", wind_speed, pbl_h, precip, solar, temp, cloud, fire, no2_init)
    step_no2 = integrate_box_model_step(no2_init, "no2", wind_speed, pbl_h, precip, solar, temp, cloud, fire, no2_init)
    step_so2 = integrate_box_model_step(so2_init, "so2", wind_speed, pbl_h, precip, solar, temp, cloud, fire, no2_init)
    step_co = integrate_box_model_step(co_init, "co", wind_speed, pbl_h, precip, solar, temp, cloud, fire, no2_init)

    diagnostics = calculate_all_diagnostics(
        wind_speed, wind_dir, pbl_h, precip, solar, temp, cloud, fire, temp_surf, temp_upper, delta_z
    )

    return {
        "pm25_ugm3": step_pm25["c_next"],
        "pm10_ugm3": step_pm10["c_next"],
        "o3_ugm3": step_o3["c_next"],
        "no2_ugm3": step_no2["c_next"],
        "so2_ugm3": step_so2["c_next"],
        "co_mgm3": step_co["c_next"],
        "diagnostics": diagnostics,
        "box_model_details": {
            "pm25_loss_rate_s1": step_pm25["loss_rate_s1"],
            "pm25_equilibrium_ugm3": step_pm25["equilibrium_conc"],
            "wet_scavenging_rate_s1": step_pm25["wet_scav_rate_s1"],
        }
    }
