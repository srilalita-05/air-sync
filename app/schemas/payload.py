"""
Pydantic Request and Response Schemas for AirSync API Endpoints.
Updated for Pydantic V2 compatibility (json_schema_extra).
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class WeatherInputSchema(BaseModel):
    timestamp: str = Field(..., json_schema_extra={
                           "example": "2026-11-15T12:00:00Z"})
    latitude: float = Field(..., json_schema_extra={"example": 28.6139})
    longitude: float = Field(..., json_schema_extra={"example": 77.2090})
    temperature_c: float = Field(...,
                                 description="2 m air temperature in °C",
                                 json_schema_extra={"example": 24.5})
    relative_humidity: float = Field(...,
                                     ge=0,
                                     le=100,
                                     description="Relative humidity %",
                                     json_schema_extra={"example": 65.0})
    pressure_hpa: float = Field(
        1013.25,
        gt=800,
        lt=1100,
        description="Surface pressure in hPa")
    wind_speed_ms: float = Field(...,
                                 ge=0,
                                 description="Wind speed in m/s",
                                 json_schema_extra={"example": 1.8})
    wind_direction_deg: float = Field(..., ge=0, lt=360,
                                      description="Meteorological wind direction degrees FROM",
                                      json_schema_extra={"example": 300.0})
    precipitation_mm: float = Field(
        0.0,
        ge=0,
        description="Precipitation rate mm/h",
        json_schema_extra={
            "example": 0.0})
    solar_radiation_wm2: float = Field(
        0.0,
        ge=0,
        description="Solar radiation W/m²",
        json_schema_extra={
            "example": 450.0})
    cloud_cover_pct: float = Field(
        0.0,
        ge=0,
        le=100,
        description="Cloud cover %",
        json_schema_extra={
            "example": 20.0})
    pbl_height_m: float = Field(...,
                                gt=20,
                                description="Planetary Boundary Layer height in meters",
                                json_schema_extra={"example": 350.0})

    # Optional vertical temperature profile fields for confirmed inversion
    # detection
    temp_surface_c: Optional[float] = Field(
        None, description="Surface temperature °C")
    temp_upper_c: Optional[float] = Field(
        None, description="Upper air temperature °C")
    delta_z_m: Optional[float] = Field(
        None, description="Vertical height difference in meters")

    # Optional Initial Pollutant Anchors
    pm25_ugm3: Optional[float] = Field(
        None, ge=0, description="Observed PM2.5 µg/m³")
    pm10_ugm3: Optional[float] = Field(
        None, ge=0, description="Observed PM10 µg/m³")
    o3_ugm3: Optional[float] = Field(
        None, ge=0, description="Observed O3 µg/m³")
    no2_ugm3: Optional[float] = Field(
        None, ge=0, description="Observed NO2 µg/m³")
    so2_ugm3: Optional[float] = Field(
        None, ge=0, description="Observed SO2 µg/m³")
    co_mgm3: Optional[float] = Field(
        None, ge=0, description="Observed CO mg/m³")

    fire_influence: float = Field(
        0.0,
        ge=0,
        le=1,
        description="Upwind fire influence score (0-1)",
        json_schema_extra={
            "example": 0.4})


class Forecast72hRequest(BaseModel):
    scenario_type: Optional[str] = Field(
        "stagnant_winter",
        description="Preset synthetic scenario or custom timeline")
    station_id: Optional[str] = Field("DEL001", description="CPCB Station ID")
    start_timestamp: Optional[str] = Field("2026-11-15T00:00:00Z")
    use_ml_residual: bool = Field(
        True, description="Enable ML residual bias correction")
    custom_weather_timeline: Optional[List[WeatherInputSchema]] = None


class PlumeRequest(BaseModel):
    fire_latitude: float = Field(..., json_schema_extra={"example": 30.3165})
    fire_longitude: float = Field(..., json_schema_extra={"example": 75.9869})
    fire_timestamp: Optional[str] = Field(None)
    frp_mw: Optional[float] = Field(150.0,
                                    description="Fire Radiative Power in MW",
                                    json_schema_extra={"example": 150.0})
    wind_speed_ms: float = Field(2.5, ge=0, json_schema_extra={"example": 2.5})
    wind_direction_deg: float = Field(
        315.0, ge=0, lt=360, json_schema_extra={
            "example": 315.0})
    target_latitude: float = Field(
        28.6139, json_schema_extra={
            "example": 28.6139})
    target_longitude: float = Field(
        77.2090, json_schema_extra={
            "example": 77.2090})
    horizon_hours: int = Field(24, ge=1, le=72)


class AqiRequest(BaseModel):
    pm25: Optional[float] = Field(None, ge=0)
    pm10: Optional[float] = Field(None, ge=0)
    o3: Optional[float] = Field(None, ge=0)
    no2: Optional[float] = Field(None, ge=0)
    so2: Optional[float] = Field(None, ge=0)
    co: Optional[float] = Field(None, ge=0)
    nh3: Optional[float] = Field(None, ge=0)
    pb: Optional[float] = Field(None, ge=0)


class EpisodeRequest(BaseModel):
    forecast_timeline: List[Dict[str, Any]]
    threshold_aqi: float = Field(
        201.0, description="AQI threshold for episode onset (default 201 Poor)")


class ExplainRequest(BaseModel):
    weather_input: WeatherInputSchema
