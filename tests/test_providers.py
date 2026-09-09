"""
Unit tests for AirSync Data Provider Adapters.
"""

from app.data.providers import (
    OpenMeteoWeatherProvider,
    ERA5ReanalysisProvider,
    OpenAQCPCBGroundProvider,
    NASAFIRMSFireProvider,
)


def test_open_meteo_weather_provider():
    provider = OpenMeteoWeatherProvider()
    timeline = provider.fetch_forecast(
        latitude=28.6139,
        longitude=77.2090,
        start_time_iso="2026-11-15T00:00:00Z",
        horizon_hours=24)
    assert len(timeline) >= 24
    assert "temperature_c" in timeline[0]
    assert "pbl_height_m" in timeline[0]


def test_ground_observation_provider():
    provider = OpenAQCPCBGroundProvider()
    obs = provider.fetch_latest_observations("DEL001")
    assert "pm25_ugm3" in obs
    assert obs["pm25_ugm3"] > 0.0


def test_nasa_firms_fire_provider():
    provider = NASAFIRMSFireProvider()
    fires = provider.fetch_active_fires()
    assert isinstance(fires, list)
    assert len(fires) > 0
    assert "frp_mw" in fires[0]
