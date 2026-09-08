from pydantic import BaseModel, Field
from typing import Optional

class WeatherInput(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    temperature_c: float = Field(..., description="2 m air temperature in °C")
    relative_humidity: float = Field(..., ge=0, le=100)
    pressure_hpa: float = Field(..., gt=800, lt=1100)
    wind_speed_ms: float = Field(..., ge=0)
    wind_direction_deg: float = Field(..., ge=0, lt=360)
    precipitation_mm: float = Field(0, ge=0)
    solar_radiation_wm2: float = Field(0, ge=0)
    cloud_cover_pct: float = Field(0, ge=0, le=100)
    pbl_height_m: float = Field(..., gt=20)
    pm25_ugm3: Optional[float] = Field(None, ge=0)
    pm10_ugm3: Optional[float] = Field(None, ge=0)
    o3_ugm3: Optional[float] = Field(None, ge=0)
    fire_influence: float = Field(0, ge=0, le=1)
