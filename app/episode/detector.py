"""
AirSync Pollution Episode Detection Engine.

Scans predicted 72-hour forecast timeseries for data-driven pollution episode detection:
- onset: first hour crossing threshold (default AQI >= 201 Poor or >= 301 Very Poor/Severe)
- rising: positive gradient leading to episode peak
- peak: hour of maximum forecast AQI
- recovery: negative gradient declining back below threshold
- normal: AQI below episode threshold
"""

from typing import Dict, List, Any, Optional


def detect_pollution_episodes(
    forecast_timeline: List[Dict[str, Any]],
    threshold_aqi: float = 201.0,  # Default threshold: AQI >= 201 (CPCB Poor Category)
) -> Dict[str, Any]:
    """Analyzes a 72-hour forecast timeline array to detect pollution episodes dynamically.
    
    Each item in forecast_timeline is expected to contain:
        - timestamp: str
        - aqi: float / int
        - drivers: dict or list
        - pm25_ugm3: float
    
    Returns:
        - episode_detected: bool
        - threshold_used: float
        - onset_timestamp: Optional[str]
        - peak_timestamp: Optional[str]
        - recovery_timestamp: Optional[str]
        - max_forecast_aqi: Optional[float]
        - duration_hours: int
        - dominant_drivers_at_peak: List[str]
        - hourly_statuses: List[Dict[str, str]]  # timestamp -> status mapping
    """
    if not forecast_timeline:
        return {
            "episode_detected": False,
            "threshold_used": threshold_aqi,
            "message": "Empty forecast timeline provided",
        }

    # Extract valid AQI scores and timestamps
    valid_points = []
    for item in forecast_timeline:
        aqi_val = item.get("aqi")
        ts = item.get("timestamp", "")
        if aqi_val is not None:
            valid_points.append({"timestamp": ts, "aqi": float(aqi_val), "item": item})
            
    if not valid_points:
        return {
            "episode_detected": False,
            "threshold_used": threshold_aqi,
            "message": "No valid AQI values found in timeline",
        }

    # Find peak point in timeline
    peak_point = max(valid_points, key=lambda x: x["aqi"])
    max_aqi = peak_point["aqi"]
    peak_ts = peak_point["timestamp"]

    # Check if episode threshold is breached
    episode_breached = (max_aqi >= threshold_aqi)
    
    if not episode_breached:
        hourly_statuses = [{"timestamp": pt["timestamp"], "status": "normal", "aqi": pt["aqi"]} for pt in valid_points]
        return {
            "episode_detected": False,
            "threshold_used": threshold_aqi,
            "onset_timestamp": None,
            "peak_timestamp": None,
            "recovery_timestamp": None,
            "max_forecast_aqi": max_aqi,
            "duration_hours": 0,
            "dominant_drivers_at_peak": [],
            "hourly_statuses": hourly_statuses,
        }

    # Find onset timestamp: first hour crossing threshold
    onset_idx = None
    for idx, pt in enumerate(valid_points):
        if pt["aqi"] >= threshold_aqi:
            onset_idx = idx
            break
            
    onset_ts = valid_points[onset_idx]["timestamp"] if onset_idx is not None else None

    # Find recovery timestamp: first hour AFTER peak where AQI drops below threshold
    peak_idx = valid_points.index(peak_point)
    recovery_idx = None
    for idx in range(peak_idx, len(valid_points)):
        if valid_points[idx]["aqi"] < threshold_aqi:
            recovery_idx = idx
            break
            
    recovery_ts = valid_points[recovery_idx]["timestamp"] if recovery_idx is not None else None

    # Calculate duration
    end_idx = recovery_idx if recovery_idx is not None else len(valid_points)
    duration_h = max(0, end_idx - onset_idx) if onset_idx is not None else 0

    # Build per-hour state machine classification
    hourly_statuses = []
    for idx, pt in enumerate(valid_points):
        ts = pt["timestamp"]
        aqi_val = pt["aqi"]
        
        if aqi_val < threshold_aqi:
            status = "normal"
        elif idx == peak_idx:
            status = "peak"
        elif onset_idx is not None and idx < peak_idx and idx >= onset_idx:
            status = "rising"
        elif peak_idx is not None and recovery_idx is not None and idx > peak_idx and idx < recovery_idx:
            status = "recovery"
        elif peak_idx is not None and recovery_idx is None and idx > peak_idx:
            status = "recovery"
        else:
            status = "onset"
            
        hourly_statuses.append({"timestamp": ts, "status": status, "aqi": aqi_val})

    # Extract dominant drivers at peak timestep
    peak_drivers = []
    peak_item = peak_point["item"]
    if "explanation" in peak_item and "dominant_driver" in peak_item["explanation"]:
        peak_drivers.append(peak_item["explanation"]["dominant_driver"])
    elif "drivers" in peak_item and isinstance(peak_item["drivers"], dict):
        # Fallback dictionary of drivers
        for k, v in peak_item["drivers"].items():
            if v in ["HIGH", "CRITICAL"]:
                peak_drivers.append(k)

    return {
        "episode_detected": True,
        "threshold_used": threshold_aqi,
        "onset_timestamp": onset_ts,
        "peak_timestamp": peak_ts,
        "recovery_timestamp": recovery_ts,
        "max_forecast_aqi": max_aqi,
        "duration_hours": duration_h,
        "dominant_drivers_at_peak": peak_drivers,
        "hourly_statuses": hourly_statuses,
    }
