"""
AirSync Two-Stage Forecast Coordinator Engine.

Orchestrates:
STAGE 1: Physics-informed mass-balance baseline forecast
STAGE 2: Machine Learning residual correction (XGBoost / Gradient Boosting)

Final Forecast C(t) = max(0, C_physics(t) + e_predicted(t))
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

from app.physics.engine import estimate_pollutants
from app.physics.diagnostics import calculate_all_diagnostics
from app.aqi.calculator import calculate_indian_aqi
from app.explainability.engine import generate_explanation
from app.episode.detector import detect_pollution_episodes
from app.forecasting.ml_residual import ml_residual_engine


def run_72h_forecast(
    weather_timeline: List[Dict[str, Any]],
    initial_observations: Optional[Dict[str, float]] = None,
    use_ml_residual: bool = True
) -> Dict[str, Any]:
    """Runs full 72-hour hourly forecast sequence across two stages.

    Inputs:
        - weather_timeline: List of 73 hourly dicts (h=0 to h=72)
        - initial_observations: Dict of anchor pollutant values at t=0 (from CPCB ground obs)
        - use_ml_residual: bool (whether to apply trained ML residual correction)

    Returns:
        - horizon_hours: int (72)
        - model_status: dict (physics_engine: active, residual_model: trained/not_trained)
        - validation_metrics: dict or None
        - hourly_forecast: List of hourly forecast objects
        - episode_summary: dict (data-driven episode onset/peak/recovery)
        - synthetic_data_flag: bool
    """
    if not weather_timeline:
        return {"error": "Empty weather timeline"}

    start_iso = weather_timeline[0].get(
        "timestamp", datetime.now(
            timezone.utc).isoformat())

    # Establish initial pollutant anchors at origin (t=0)
    origin_obs = {
        "pm25_ugm3": float(
            initial_observations.get(
                "pm25_ugm3",
                weather_timeline[0].get(
                    "pm25_ugm3",
                    80.0)) if initial_observations else weather_timeline[0].get(
                "pm25_ugm3",
                80.0)),
        "pm10_ugm3": float(
            initial_observations.get(
                "pm10_ugm3",
                weather_timeline[0].get(
                    "pm10_ugm3",
                    120.0)) if initial_observations else weather_timeline[0].get(
                "pm10_ugm3",
                120.0)),
        "o3_ugm3": float(
            initial_observations.get(
                "o3_ugm3",
                weather_timeline[0].get(
                    "o3_ugm3",
                    45.0)) if initial_observations else weather_timeline[0].get(
                "o3_ugm3",
                45.0)),
        "no2_ugm3": float(
            initial_observations.get(
                "no2_ugm3",
                weather_timeline[0].get(
                    "no2_ugm3",
                    35.0)) if initial_observations else weather_timeline[0].get(
                "no2_ugm3",
                35.0)),
        "so2_ugm3": float(
            initial_observations.get(
                "so2_ugm3",
                weather_timeline[0].get(
                    "so2_ugm3",
                    15.0)) if initial_observations else weather_timeline[0].get(
                "so2_ugm3",
                15.0)),
        "co_mgm3": float(
            initial_observations.get(
                "co_mgm3",
                weather_timeline[0].get(
                    "co_mgm3",
                    1.2)) if initial_observations else weather_timeline[0].get(
                "co_mgm3",
                1.2)),
    }

    hourly_forecast: List[Dict[str, Any]] = []
    prev_pollutants = dict(origin_obs)

    ml_status = "trained" if ml_residual_engine.is_trained else "not_trained"
    metrics = ml_residual_engine.metrics if ml_residual_engine.is_trained else None

    for h, step_w in enumerate(weather_timeline):
        # Inject previous timestep output as continuity state for physics box
        # step
        step_w_inp = dict(step_w)
        if h == 0:
            step_w_inp.update(origin_obs)

        # STAGE 1: Physics Baseline Step
        phys_out = estimate_pollutants(
            step_w_inp, previous=prev_pollutants if h > 0 else None)

        phys_pm25 = phys_out["pm25_ugm3"]
        phys_pm10 = phys_out["pm10_ugm3"]
        phys_o3 = phys_out["o3_ugm3"]
        phys_no2 = phys_out["no2_ugm3"]
        phys_so2 = phys_out["so2_ugm3"]
        phys_co = phys_out["co_mgm3"]

        diagnostics = phys_out["diagnostics"]

        # STAGE 2: ML Residual Correction (Strict origin availability)
        res_pm25 = 0.0
        res_pm10 = 0.0
        res_o3 = 0.0

        if use_ml_residual and ml_residual_engine.is_trained:
            # Construct no-leakage feature vector
            feats = ml_residual_engine.extract_features(
                weather_forecast_step=step_w,
                physics_baseline_step={
                    "pm25_ugm3": phys_pm25,
                    "pm10_ugm3": phys_pm10,
                    "o3_ugm3": phys_o3},
                initial_obs_at_origin=origin_obs,
                horizon_hour=h,
                hour_of_day=h %
                24,
                day_of_week=0)
            res_pm25 = ml_residual_engine.predict_residual("pm25", feats)
            res_pm10 = ml_residual_engine.predict_residual("pm10", feats)
            res_o3 = ml_residual_engine.predict_residual("o3", feats)

        # Final Combined Forecast
        final_pm25 = max(0.0, phys_pm25 + res_pm25)
        final_pm10 = max(0.0, phys_pm10 + res_pm10)
        final_o3 = max(0.0, phys_o3 + res_o3)
        final_no2 = max(0.0, phys_no2)
        final_so2 = max(0.0, phys_so2)
        final_co = max(0.0, phys_co)

        # Update continuity state for next hour's box model step
        prev_pollutants = {
            "pm25_ugm3": final_pm25,
            "pm10_ugm3": final_pm10,
            "o3_ugm3": final_o3,
            "no2_ugm3": final_no2,
            "so2_ugm3": final_so2,
            "co_mgm3": final_co,
        }

        # Calculate CPCB AQI
        aqi_out = calculate_indian_aqi(
            pm25=final_pm25, pm10=final_pm10, o3=final_o3,
            no2=final_no2, so2=final_so2, co=final_co
        )

        # Generate Explainability attribution
        explanation = generate_explanation(
            step_w, diagnostics, {
                "pm25": final_pm25, "pm10": final_pm10, "o3": final_o3})

        hourly_forecast.append({
            "hour": h,
            "timestamp": step_w.get("timestamp", ""),
            "pollutants": {
                "pm25_ugm3": round(final_pm25, 2),
                "pm10_ugm3": round(final_pm10, 2),
                "o3_ugm3": round(final_o3, 2),
                "no2_ugm3": round(final_no2, 2),
                "so2_ugm3": round(final_so2, 2),
                "co_mgm3": round(final_co, 2),
            },
            "physics_baseline": {
                "pm25_ugm3": round(phys_pm25, 2),
                "pm10_ugm3": round(phys_pm10, 2),
                "o3_ugm3": round(phys_o3, 2),
            },
            "ml_residual_correction": {
                "res_pm25": round(res_pm25, 2),
                "res_pm10": round(res_pm10, 2),
                "res_o3": round(res_o3, 2),
            },
            "aqi": aqi_out,
            "physics_diagnostics": diagnostics,
            "explanation": explanation,
        })

    # Data-driven episode detection over the hourly forecast
    timeline_for_episode = [
        {
            "timestamp": item["timestamp"],
            "aqi": item["aqi"]["overall_aqi"],
            "explanation": item["explanation"],
            "pm25_ugm3": item["pollutants"]["pm25_ugm3"]
        } for item in hourly_forecast
    ]
    episode_summary = detect_pollution_episodes(
        timeline_for_episode, threshold_aqi=201.0)

    return {
        "forecast_type": "72-hour hourly forecast",
        "horizon_hours": len(hourly_forecast) - 1,
        "start_timestamp": start_iso,
        "model_status": {
            "physics_engine": "active_mass_balance_box_model",
            "residual_model": ml_status,
        },
        "validation_metrics": metrics,
        "episode_summary": episode_summary,
        "hourly_forecast": hourly_forecast,
        "synthetic_data_flag": True,
    }
