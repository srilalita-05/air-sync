"""
AirSync Synthetic Data Generator for Delhi-NCR.

Generates realistic demonstration scenario datasets clearly marked:
'SYNTHETIC / DEMONSTRATION DATA'

NOTE: Synthetic data is generated for prototype development, offline testing, and UI demonstration.
It does NOT represent live official CPCB / IMD observations.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


DELHI_NCR_STATIONS = [
    {"id": "DEL001", "name": "Anand Vihar, Delhi", "lat": 28.6469, "lon": 77.3160},
    {"id": "DEL002", "name": "R.K. Puram, Delhi", "lat": 28.5633, "lon": 77.1864},
    {"id": "DEL003", "name": "Punjabi Bagh, Delhi", "lat": 28.6740, "lon": 77.1310},
    {"id": "DEL004", "name": "ITO, Delhi", "lat": 28.6317, "lon": 77.2494},
    {"id": "NCR001", "name": "Sector 62, Noida", "lat": 28.6245, "lon": 77.3577},
    {"id": "NCR002", "name": "Vikas Sadan, Gurugram", "lat": 28.4501, "lon": 77.0263},
]


def generate_synthetic_scenario(
    scenario_type: str = "stagnant_winter",
    start_time_iso: str = "2026-11-15T00:00:00Z",
    horizon_hours: int = 72,
    station_id: str = "DEL001"
) -> Dict[str, Any]:
    """Generates a 72-hour synthetic weather and pollution scenario.

    Supported scenario_type values:
    - "stagnant_winter": Low wind, shallow nocturnal PBL, high baseline PM2.5 (Severe Episode)
    - "low_pbl_inversion": Shallow mixing layer with strong nocturnal accumulation
    - "high_wind_clearing": Strong westerly winds dispersing pollutants
    - "monsoon_scavenging": Heavy precipitation washing out particulates
    - "biomass_fire_influence": Upwind stubble burning surge pushing PM2.5 up downwind
    - "normal_baseline": Moderate seasonal baseline
    """
    station = next(
        (s for s in DELHI_NCR_STATIONS if s["id"] == station_id),
        DELHI_NCR_STATIONS[0])

    start_dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
    timeline: List[Dict[str, Any]] = []

    for h in range(horizon_hours + 1):
        dt_current = start_dt + timedelta(hours=h)
        hour_of_day = dt_current.hour

        # Diurnal diurnal temperature cycle (min at 6 AM, max at 2 PM)
        temp_base = 18.0 if "winter" in scenario_type else 28.0
        temp = temp_base + 6.0 * \
            (1.0 - math.cos(2.0 * math.pi * (hour_of_day - 6) / 24.0))

        # Diurnal solar radiation (peak at noon ~12 PM)
        solar = max(0.0, 750.0 * math.sin(math.pi * (hour_of_day -
                    6) / 12.0)) if (6 <= hour_of_day <= 18) else 0.0

        # Scenario specific meteorology & pollution profiles
        if scenario_type == "stagnant_winter":
            wind_speed = 1.0 + 0.5 * math.sin(hour_of_day / 4.0)
            wind_dir = 300.0  # North-westerly
            # Diurnal PBL: collapses to 150m at night, rises to 600m afternoon
            pbl = 150.0 + 450.0 * max(0.0, math.sin(math.pi * (hour_of_day - 6) / 12.0)) if (
                6 <= hour_of_day <= 18) else 150.0
            precip = 0.0
            rh = 75.0 + 15.0 * (1.0 - (solar / 750.0))
            fire = 0.4

            # Initial CPCB anchor observations at origin (t=0)
            init_pm25 = 220.0 + 60.0 * math.sin(h / 12.0)
            init_pm10 = 340.0 + 80.0 * math.sin(h / 12.0)
            init_o3 = 35.0 + 40.0 * (solar / 750.0)

        elif scenario_type == "high_wind_clearing":
            wind_speed = 6.5 + 1.5 * math.sin(hour_of_day / 3.0)
            wind_dir = 270.0
            pbl = 1200.0 + 600.0 * \
                max(0.0, math.sin(math.pi * (hour_of_day - 6) / 12.0))
            precip = 0.0
            rh = 40.0
            fire = 0.0

            init_pm25 = max(20.0, 90.0 - 1.0 * h)
            init_pm10 = max(40.0, 140.0 - 1.5 * h)
            init_o3 = 45.0 + 20.0 * (solar / 750.0)

        elif scenario_type == "monsoon_scavenging":
            wind_speed = 3.5
            wind_dir = 110.0
            pbl = 700.0
            precip = 6.0 if (12 <= h <= 36) else 0.5  # Heavy rain block
            rh = 90.0
            fire = 0.0

            init_pm25 = max(15.0, 70.0 - 1.8 * h)
            init_pm10 = max(30.0, 110.0 - 2.5 * h)
            init_o3 = 20.0

        elif scenario_type == "biomass_fire_influence":
            wind_speed = 2.0
            wind_dir = 315.0  # Directly from Punjab/Haryana stubble burning corridor
            pbl = 350.0 + 300.0 * \
                max(0.0, math.sin(math.pi * (hour_of_day - 6) / 12.0))
            precip = 0.0
            rh = 60.0
            fire = 0.85  # Strong fire signal

            init_pm25 = 180.0 + 3.0 * h  # Accumulating plume
            init_pm10 = 280.0 + 4.5 * h
            init_o3 = 40.0

        else:  # normal_baseline
            wind_speed = 3.0 + 1.0 * math.sin(hour_of_day / 6.0)
            wind_dir = 280.0
            pbl = 400.0 + 800.0 * \
                max(0.0, math.sin(math.pi * (hour_of_day - 6) / 12.0))
            precip = 0.0
            rh = 55.0
            fire = 0.1

            init_pm25 = 65.0 + 15.0 * math.sin(hour_of_day / 4.0)
            init_pm10 = 110.0 + 25.0 * math.sin(hour_of_day / 4.0)
            init_o3 = 35.0 + 35.0 * (solar / 750.0)

        timeline.append({
            "hour": h,
            "timestamp": dt_current.isoformat(),
            "station_id": station["id"],
            "station_name": station["name"],
            "latitude": station["lat"],
            "longitude": station["lon"],
            "temperature_c": round(temp, 1),
            "relative_humidity": round(rh, 1),
            "pressure_hpa": 1012.0,
            "wind_speed_ms": round(wind_speed, 1),
            "wind_direction_deg": round(wind_dir, 1),
            "precipitation_mm": round(precip, 1),
            "solar_radiation_wm2": round(solar, 1),
            "cloud_cover_pct": 10.0,
            "pbl_height_m": round(pbl, 1),
            "fire_influence": round(fire, 2),
            "pm25_ugm3": round(init_pm25, 1),
            "pm10_ugm3": round(init_pm10, 1),
            "o3_ugm3": round(init_o3, 1),
        })

    return {
        "dataset_type": "SYNTHETIC / DEMONSTRATION DATA",
        "scenario_type": scenario_type,
        "station": station,
        "start_time": start_time_iso,
        "horizon_hours": horizon_hours,
        "timeline": timeline,
        "note": "Synthetic demonstration data for AirSync SIH 2026 prototype execution."
    }
