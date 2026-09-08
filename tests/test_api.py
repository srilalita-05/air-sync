"""
Integration tests for FastAPI REST API endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["physics_engine"] == "active_mass_balance_box_model"


def test_forecast_72h_endpoint():
    payload = {"scenario_type": "stagnant_winter", "use_ml_residual": False}
    response = client.post("/forecast/72h", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "hourly_forecast" in data
    assert len(data["hourly_forecast"]) == 73
    assert data["forecast_type"] == "72-hour hourly forecast"


def test_explain_endpoint():
    payload = {
        "weather_input": {
            "timestamp": "2026-11-15T12:00:00Z",
            "latitude": 28.61,
            "longitude": 77.20,
            "temperature_c": 22.0,
            "relative_humidity": 70.0,
            "pressure_hpa": 1012.0,
            "wind_speed_ms": 1.1,
            "wind_direction_deg": 300.0,
            "precipitation_mm": 0.0,
            "solar_radiation_wm2": 300.0,
            "cloud_cover_pct": 10.0,
            "pbl_height_m": 250.0,
            "fire_influence": 0.5
        }
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "dominant_driver" in data["explanation"]


def test_plume_endpoint():
    payload = {
        "fire_latitude": 30.5,
        "fire_longitude": 75.5,
        "wind_speed_ms": 3.0,
        "wind_direction_deg": 315.0,
        "target_latitude": 28.61,
        "target_longitude": 77.20,
        "horizon_hours": 12
    }
    response = client.post("/plume", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "potential_downwind_influence_score" in data


def test_aqi_endpoint():
    payload = {"pm25": 120.0, "pm10": 200.0, "o3": 50.0}
    response = client.post("/aqi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_aqi"] == 300
    assert data["aqi_category"] == "Poor"
