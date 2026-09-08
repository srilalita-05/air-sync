"""
AirSync REST API Routes Definition.

Provides endpoints for:
- GET  /health
- POST /forecast
- POST /forecast/72h
- POST /explain
- POST /episode
- POST /plume
- POST /aqi
- POST /data/validate
- POST /model/train
- GET  /model/status
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.payload import (
    WeatherInputSchema,
    Forecast72hRequest,
    PlumeRequest,
    AqiRequest,
    EpisodeRequest,
    ExplainRequest,
)

from app.physics.engine import estimate_pollutants
from app.physics.diagnostics import calculate_all_diagnostics
from app.forecasting.engine import run_72h_forecast
from app.forecasting.ml_residual import ml_residual_engine
from app.explainability.engine import generate_explanation
from app.episode.detector import detect_pollution_episodes
from app.plume.trajectory import calculate_plume_trajectory
from app.aqi.calculator import calculate_indian_aqi
from app.data.validator import validate_and_clean_input
from app.data.synthetic import generate_synthetic_scenario

router = APIRouter()


@router.get("/health")
def health_check():
    """Returns server status, loaded physics modules, and ML residual model state."""
    return {
        "status": "healthy",
        "service": "AirSync Air Pollution–Weather Coupled Forecasting Engine",
        "version": "1.0.0",
        "region_focus": "Delhi-NCR",
        "physics_engine": "active_mass_balance_box_model",
        "residual_model_status": "trained" if ml_residual_engine.is_trained else "not_trained",
        "residual_model_metrics": ml_residual_engine.metrics if ml_residual_engine.is_trained else None,
        "synthetic_demo_mode": True,
    }


@router.post("/forecast")
def single_step_forecast(inp: WeatherInputSchema):
    """Calculates a single 1-hour step forecast given meteorological & initial pollutant inputs."""
    val_res = validate_and_clean_input(inp.model_dump())
    if not val_res["is_valid"]:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {val_res['missing_required_variables']}")
        
    cleaned = val_res["cleaned_data"]
    phys_out = estimate_pollutants(inp)
    diagnostics = phys_out["diagnostics"]
    
    res_pm25 = 0.0
    res_pm10 = 0.0
    res_o3 = 0.0
    
    if ml_residual_engine.is_trained:
        feats = ml_residual_engine.extract_features(
            weather_forecast_step=cleaned,
            physics_baseline_step=phys_out,
            initial_obs_at_origin={
                "pm25_ugm3": inp.pm25_ugm3 or phys_out["pm25_ugm3"],
                "pm10_ugm3": inp.pm10_ugm3 or phys_out["pm10_ugm3"],
                "o3_ugm3": inp.o3_ugm3 or phys_out["o3_ugm3"],
            },
            horizon_hour=1
        )
        res_pm25 = ml_residual_engine.predict_residual("pm25", feats)
        res_pm10 = ml_residual_engine.predict_residual("pm10", feats)
        res_o3 = ml_residual_engine.predict_residual("o3", feats)
        
    final_pm25 = max(0.0, phys_out["pm25_ugm3"] + res_pm25)
    final_pm10 = max(0.0, phys_out["pm10_ugm3"] + res_pm10)
    final_o3 = max(0.0, phys_out["o3_ugm3"] + res_o3)
    
    aqi_out = calculate_indian_aqi(pm25=final_pm25, pm10=final_pm10, o3=final_o3)
    explanation = generate_explanation(cleaned, diagnostics, {"pm25": final_pm25, "pm10": final_pm10, "o3": final_o3})
    
    return {
        "timestamp": inp.timestamp,
        "pollutants": {
            "pm25_ugm3": round(final_pm25, 2),
            "pm10_ugm3": round(final_pm10, 2),
            "o3_ugm3": round(final_o3, 2),
        },
        "physics_baseline": {
            "pm25_ugm3": round(phys_out["pm25_ugm3"], 2),
            "pm10_ugm3": round(phys_out["pm10_ugm3"], 2),
            "o3_ugm3": round(phys_out["o3_ugm3"], 2),
        },
        "ml_residual_correction": {
            "res_pm25": round(res_pm25, 2),
            "res_pm10": round(res_pm10, 2),
            "res_o3": round(res_o3, 2),
        },
        "aqi": aqi_out,
        "physics_diagnostics": diagnostics,
        "explanation": explanation,
        "dataset_type": "SYNTHETIC / DEMONSTRATION DATA",
    }


@router.post("/forecast/72h")
def forecast_72h(req: Forecast72hRequest):
    """Generates a complete 72-hour hourly forecast sequence with physics indicators, AQI,
    explainability drivers, and data-driven episode detection.
    """
    if req.custom_weather_timeline and len(req.custom_weather_timeline) > 0:
        timeline = [w.model_dump() for w in req.custom_weather_timeline]
    else:
        synth = generate_synthetic_scenario(
            scenario_type=req.scenario_type or "stagnant_winter",
            start_time_iso=req.start_timestamp or "2026-11-15T00:00:00Z",
            horizon_hours=72,
            station_id=req.station_id or "DEL001"
        )
        timeline = synth["timeline"]
        
    res = run_72h_forecast(timeline, use_ml_residual=req.use_ml_residual)
    return res


@router.post("/explain")
def explain_drivers(req: ExplainRequest):
    """Calculates physical diagnostics and generates structured human-readable driver attribution."""
    val = validate_and_clean_input(req.weather_input.model_dump())
    cleaned = val["cleaned_data"]
    phys = estimate_pollutants(req.weather_input)
    diagnostics = phys["diagnostics"]
    exp = generate_explanation(cleaned, diagnostics, {"pm25": phys["pm25_ugm3"], "pm10": phys["pm10_ugm3"], "o3": phys["o3_ugm3"]})
    return {
        "timestamp": req.weather_input.timestamp,
        "explanation": exp,
        "physics_diagnostics": diagnostics,
    }


@router.post("/episode")
def detect_episode(req: EpisodeRequest):
    """Analyzes a 72-hour forecast timeline to detect episode onset, peak, recovery timestamps."""
    return detect_pollution_episodes(req.forecast_timeline, threshold_aqi=req.threshold_aqi)


@router.post("/plume")
def simulate_plume(req: PlumeRequest):
    """Simulates 2D kinematic advection trajectory and dispersion envelope for biomass fire hotspots."""
    res = calculate_plume_trajectory(
        fire_lat=req.fire_latitude,
        fire_lon=req.fire_longitude,
        wind_speed_ms=req.wind_speed_ms,
        wind_direction_deg=req.wind_direction_deg,
        frp_mw=req.frp_mw,
        target_lat=req.target_latitude,
        target_lon=req.target_longitude,
        horizon_hours=req.horizon_hours,
    )
    return res


@router.post("/aqi")
def compute_aqi(req: AqiRequest):
    """Standalone CPCB Indian AQI calculator for given pollutant concentrations."""
    return calculate_indian_aqi(
        pm25=req.pm25, pm10=req.pm10, o3=req.o3, no2=req.no2, so2=req.so2, co=req.co, nh3=req.nh3, pb=req.pb
    )


@router.post("/data/validate")
def validate_data(raw_payload: Dict[str, Any]):
    """Validates input payload fields, physical bounds, and missing variable fallbacks."""
    return validate_and_clean_input(raw_payload)


@router.post("/model/train")
def train_model():
    """Retrains the ML residual correction model using synthetic paired historical dataset."""
    # Generate synthetic training dataset with paired observations and physics forecasts
    synth = generate_synthetic_scenario("stagnant_winter", horizon_hours=200)
    records = []
    
    for pt in synth["timeline"]:
        phys = estimate_pollutants(pt)
        # Create synthetic noise/bias
        obs_pm25 = phys["pm25_ugm3"] + 15.0 * np.sin(pt["hour"] / 4.0) + 5.0 * np.random.randn()
        obs_pm10 = phys["pm10_ugm3"] + 25.0 * np.sin(pt["hour"] / 4.0) + 8.0 * np.random.randn()
        obs_o3 = phys["o3_ugm3"] + 8.0 * np.cos(pt["hour"] / 6.0) + 3.0 * np.random.randn()
        
        row = {
            "timestamp": pt["timestamp"],
            "wind_speed_ms": pt["wind_speed_ms"],
            "u_wind": -pt["wind_speed_ms"] * np.sin(np.radians(pt["wind_direction_deg"])),
            "v_wind": -pt["wind_speed_ms"] * np.cos(np.radians(pt["wind_direction_deg"])),
            "pbl_height_m": pt["pbl_height_m"],
            "vc": pt["wind_speed_ms"] * pt["pbl_height_m"],
            "temperature_c": pt["temperature_c"],
            "relative_humidity": pt["relative_humidity"],
            "precipitation_mm": pt["precipitation_mm"],
            "solar_radiation_wm2": pt["solar_radiation_wm2"],
            "fire_influence": pt["fire_influence"],
            "phys_pm25": phys["pm25_ugm3"],
            "phys_pm10": phys["pm10_ugm3"],
            "phys_o3": phys["o3_ugm3"],
            "obs_pm25": max(0.0, obs_pm25),
            "obs_pm10": max(0.0, obs_pm10),
            "obs_o3": max(0.0, obs_o3),
            "pm25_origin": 80.0,
            "pm10_origin": 120.0,
            "o3_origin": 40.0,
            "horizon_hour": float(pt["hour"]),
            "hour_sin": np.sin(2.0 * np.pi * (pt["hour"] % 24) / 24.0),
            "hour_cos": np.cos(2.0 * np.pi * (pt["hour"] % 24) / 24.0),
            "day_of_week": 1.0,
        }
        records.append(row)
        
    df_train = pd.DataFrame(records)
    res = ml_residual_engine.train(df_train)
    return res


@router.get("/model/status")
def model_status():
    """Reports status and validation performance metrics of the ML residual correction model."""
    return {
        "residual_model": "trained" if ml_residual_engine.is_trained else "not_trained",
        "validation_metrics": ml_residual_engine.metrics if ml_residual_engine.is_trained else None,
        "supported_pollutants": ["pm25", "pm10", "o3"],
        "no_data_leakage_enforced": True,
    }
