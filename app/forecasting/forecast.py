from datetime import datetime, timedelta
from app.physics.engine import estimate_pollutants
from app.aqi.calculator import calculate_aqi

DRIVER_LABELS = {
    "low_wind": "HIGH",
    "low_pbl": "HIGH",
    "humidity": "MODERATE",
    "rain": "LOW",
    "fire": "LOW",
}

def drivers(inp, physics):
    low_wind = max(0, min(1, (4-inp.wind_speed_ms)/4))
    low_pbl = max(0, min(1, (800-inp.pbl_height_m)/800))
    humidity = inp.relative_humidity/100
    rain = min(1, inp.precipitation_mm/5)
    fire = inp.fire_influence
    def level(x):
        return "HIGH" if x >= .67 else "MODERATE" if x >= .34 else "LOW"
    return {
        "low_wind": level(low_wind), "low_pbl": level(low_pbl),
        "humidity": level(humidity), "rain": level(rain), "fire": level(fire)
    }

def forecast(inp, hours=72):
    start = datetime.fromisoformat(inp.timestamp.replace("Z", "+00:00"))
    rows=[]
    for h in range(hours+1):
        # Prototype persistence assumption. In production these are replaced by hourly weather forecasts.
        p = estimate_pollutants(inp)
        decay = 1.0 - 0.002*h
        pm25, pm10, o3 = p["pm25_ugm3"]*decay, p["pm10_ugm3"]*decay, p["o3_ugm3"]
        aqi, sub = calculate_aqi(pm25, pm10, o3)
        rows.append({
            "timestamp": (start+timedelta(hours=h)).isoformat(),
            "pm25_ugm3": round(pm25,2), "pm10_ugm3": round(pm10,2), "o3_ugm3": round(o3,2),
            "aqi": aqi, "subindices": sub,
            "dispersion_index": round(p["dispersion_index"],3),
            "inversion_risk": round(p["inversion_risk"],3),
            "rain_removal_factor": round(p["rain_removal_factor"],3),
            "photochemical_activity": round(p["photochemical_activity"],3),
            "drivers": drivers(inp,p),
        })
    return rows
