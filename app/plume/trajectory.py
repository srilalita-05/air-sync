"""
Kinematic Fire-Plume Trajectory and Simplified Dispersion Envelope Module.

Estimates downwind transport trajectory and expanding dispersion envelope for biomass burning
fire emissions (e.g. stubble burning hotspots detected by NASA FIRMS).

DISCLAIMER & LIMITATIONS:
- This is a 2D kinematic advection and Gaussian buffer envelope model.
- It predicts POTENTIAL DOWNWIND INFLUENCE score [0.0 - 1.0], NOT actual pollutant concentration [µg/m³].
- It is NOT equivalent to a 3D Eulerian/Lagrangian chemical transport model (such as WRF-Chem/HYSPLIT).
"""

import math
from typing import Dict, List, Any, Optional, Tuple


def calculate_plume_trajectory(
    fire_lat: float,
    fire_lon: float,
    wind_speed_ms: float,
    wind_direction_deg: float,
    frp_mw: Optional[float] = None,
    target_lat: float = 28.6139,    # Central Delhi (Connaught Place / ITO)
    target_lon: float = 77.2090,
    horizon_hours: int = 24,
) -> Dict[str, Any]:
    """Computes hourly predicted parcel locations and plume dispersion radius over downwind horizon.

    Inputs:
        - fire_lat, fire_lon: FIRMS hotspot geographic coordinates
        - wind_speed_ms: Surface wind speed [m/s]
        - wind_direction_deg: Meteorological wind direction [deg] (direction FROM which wind blows)
        - frp_mw: Fire Radiative Power [MW] (intensity proxy)
        - target_lat, target_lon: Receptive domain coordinates
        - horizon_hours: Forecast trajectory hours (default 24h)

    Returns:
        - trajectory_points: List of dicts with lat, lon, hour, sigma_radius_m
        - downwind_influence_score: float (0.0 to 1.0)
        - is_simplified_kinematic_proxy: True
        - disclaimer: Text explanation
    """
    # Wind component calculation (direction wind is blowing TOWARDS)
    # Wind direction theta is direction FROM which wind blows.
    # Flow direction = (theta + 180) % 360
    flow_rad = math.radians((wind_direction_deg + 180.0) % 360.0)

    u_flow = wind_speed_ms * math.sin(flow_rad)  # Eastwards velocity [m/s]
    v_flow = wind_speed_ms * math.cos(flow_rad)  # Northwards velocity [m/s]

    points: List[Dict[str, Any]] = []

    curr_lat = fire_lat
    curr_lon = fire_lon

    # Base initial radius from FRP intensity (higher FRP -> larger initial
    # thermal plume)
    initial_radius_m = 500.0 + \
        (min(500.0, frp_mw * 5.0) if frp_mw is not None else 100.0)

    # Distance to target initial check
    min_distance_to_target_m = 1.0e9
    closest_hour = 0

    for h in range(horizon_hours + 1):
        dt_seconds = h * 3600.0

        # Cumulative displacement in meters
        dx_m = u_flow * dt_seconds
        dy_m = v_flow * dt_seconds

        # Convert meter displacement to latitude and longitude delta
        # 1 deg latitude ~ 111,000 m
        # 1 deg longitude ~ 111,000 * cos(lat) m
        lat_pt = fire_lat + (dy_m / 111000.0)
        lon_pt = fire_lon + \
            (dx_m / (111000.0 * math.cos(math.radians(fire_lat))))

        # Dispersion horizontal spread radius sigma_r(t) = sqrt(sigma_0^2 + 2 * K_y * t)
        # K_y ~ 50 m²/s horizontal eddy diffusivity proxy
        sigma_radius_m = math.sqrt(
            initial_radius_m**2 + 2.0 * 50.0 * dt_seconds)

        # Distance from target point to this trajectory parcel
        d_lat_m = (lat_pt - target_lat) * 111000.0
        d_lon_m = (lon_pt - target_lon) * 111000.0 * \
            math.cos(math.radians(target_lat))
        dist_m = math.sqrt(d_lat_m**2 + d_lon_m**2)

        if dist_m < min_distance_to_target_m:
            min_distance_to_target_m = dist_m
            closest_hour = h

        points.append({
            "hour": h,
            "latitude": round(lat_pt, 5),
            "longitude": round(lon_pt, 5),
            "dispersion_radius_m": round(sigma_radius_m, 1),
            "distance_to_target_km": round(dist_m / 1000.0, 2),
        })

    # Calculate potential downwind influence score based on minimum approach distance and plume spread
    # Gaussian proximity weight: exp(-0.5 * (dist / sigma)^2)
    effective_sigma = points[closest_hour]["dispersion_radius_m"] if points else 5000.0
    proximity_weight = math.exp(-0.5 * (min_distance_to_target_m /
                                max(2000.0, effective_sigma))**2)

    # FRP intensity factor
    intensity_weight = min(
        1.0, (frp_mw / 200.0)) if frp_mw is not None else 0.5

    influence_score = round(
        max(0.0, min(1.0, proximity_weight * (0.4 + 0.6 * intensity_weight))), 3)

    return {
        "fire_origin": {"latitude": fire_lat, "longitude": fire_lon, "frp_mw": frp_mw},
        "target_location": {"latitude": target_lat, "longitude": target_lon},
        "wind_state": {"speed_ms": wind_speed_ms, "direction_deg": wind_direction_deg},
        "potential_downwind_influence_score": influence_score,
        "closest_approach_km": round(min_distance_to_target_m / 1000.0, 2),
        "closest_approach_hour": closest_hour,
        "trajectory_points": points,
        "is_simplified_kinematic_proxy": True,
        "disclaimer": "Kinematic 2D transport proxy showing potential downwind influence, NOT actual concentration.",
    }
