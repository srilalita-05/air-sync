"""
Machine Learning Residual Correction Engine.

Fits and predicts systematic bias e(t) = C_observed(t) - C_physics(t).

STRICT NO-DATA-LEAKAGE DESIGN:
- For forecast initialized at time T: Features only consume information available AT OR BEFORE time T.
- Multi-step Strategy: Exogenous Horizon Direct Forecasting. Future weather forecasts for T+h,
  physics baseline predictions for T+h, and origin state C_observed(T) are used.
  FUTURE CPCB pollutant observations (past initialization origin T) are NEVER used as input features.
- Chronological time-series train/val/test splitting.
"""

import os
import math
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from sklearn.ensemble import HistGradientBoostingRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")


class ResidualCorrectionModel:
    """Manages training, saving, loading, and predicting ML residual corrections.
    
    Target: residual e_pollutant = C_observed - C_physics
    Final Forecast: C_final = max(0, C_physics + e_predicted)
    """
    
    def __init__(self, model_dir: str = MODEL_DIR):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.models: Dict[str, Any] = {}
        self.metrics: Dict[str, Dict[str, float]] = {}
        self.is_trained: bool = False
        self._load_models_if_exist()
        
    def _load_models_if_exist(self):
        """Attempts to load saved residual model artifacts from models directory."""
        meta_path = os.path.join(self.model_dir, "residual_metadata.pkl")
        if os.path.exists(meta_path):
            try:
                meta = joblib.load(meta_path)
                self.metrics = meta.get("metrics", {})
                for pol in ["pm25", "pm10", "o3"]:
                    m_path = os.path.join(self.model_dir, f"model_{pol}.pkl")
                    if os.path.exists(m_path):
                        self.models[pol] = joblib.load(m_path)
                if len(self.models) == 3:
                    self.is_trained = True
            except Exception:
                self.is_trained = False
                
    def extract_features(
        self,
        weather_forecast_step: Dict[str, Any],
        physics_baseline_step: Dict[str, Any],
        initial_obs_at_origin: Dict[str, float],
        horizon_hour: int,
        hour_of_day: int = 12,
        day_of_week: int = 2,
    ) -> List[float]:
        """Constructs input feature vector for horizon step T + horizon_hour.
        
        CRITICAL NO-LEAKAGE FEATURE SET:
        - Weather forecast fields at T+h (wind_speed, pbl_height, temp, rh, precip, solar)
        - Derived physics diagnostics at T+h (ventilation_coefficient, accumulation_score)
        - Baseline physics forecast at T+h (pm25_phys, pm10_phys, o3_phys)
        - Forecast horizon h (hours past origin T)
        - Calendar features (hour sin/cos, day of week)
        - Initial pollutant observation available AT ORIGIN T (lag 0 observation)
        
        NO future pollutant observations are consumed!
        """
        u_wind = weather_forecast_step.get("wind", {}).get("u_east", 0.0)
        v_wind = weather_forecast_step.get("wind", {}).get("v_north", 0.0)
        wind_speed = weather_forecast_step.get("wind_speed_ms", 2.0)
        pbl_h = weather_forecast_step.get("pbl_height_m", 800.0)
        vc = wind_speed * pbl_h
        
        temp = weather_forecast_step.get("temperature_c", 25.0)
        rh = weather_forecast_step.get("relative_humidity", 50.0)
        precip = weather_forecast_step.get("precipitation_mm", 0.0)
        solar = weather_forecast_step.get("solar_radiation_wm2", 0.0)
        fire = weather_forecast_step.get("fire_influence", 0.0)
        
        pm25_phys = physics_baseline_step.get("pm25_ugm3", 50.0)
        pm10_phys = physics_baseline_step.get("pm10_ugm3", 90.0)
        o3_phys = physics_baseline_step.get("o3_ugm3", 40.0)
        
        # Origin T initial observation
        pm25_origin = initial_obs_at_origin.get("pm25_ugm3", pm25_phys)
        pm10_origin = initial_obs_at_origin.get("pm10_ugm3", pm10_phys)
        o3_origin = initial_obs_at_origin.get("o3_ugm3", o3_phys)
        
        hour_sin = math.sin(2.0 * math.pi * hour_of_day / 24.0)
        hour_cos = math.cos(2.0 * math.pi * hour_of_day / 24.0)
        
        return [
            wind_speed, u_wind, v_wind, pbl_h, vc, temp, rh, precip, solar, fire,
            pm25_phys, pm10_phys, o3_phys,
            pm25_origin, pm10_origin, o3_origin,
            float(horizon_hour), hour_sin, hour_cos, float(day_of_week)
        ]

    def train(self, df_training_data: pd.DataFrame) -> Dict[str, Any]:
        """Trains residual models on historical dataset using strict chronological split.
        
        Expected columns in df_training_data:
        - weather & physics features
        - obs_pm25, obs_pm10, obs_o3
        - phys_pm25, phys_pm10, phys_o3
        """
        if df_training_data is None or len(df_training_data) < 50:
            return {"status": "error", "message": "Insufficient training records"}
            
        # Sort chronologically
        if "timestamp" in df_training_data.columns:
            df_training_data = df_training_data.sort_values("timestamp").reset_index(drop=True)
            
        n = len(df_training_data)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)
        
        feature_cols = [c for c in df_training_data.columns if c not in ["timestamp", "obs_pm25", "obs_pm10", "obs_o3", "res_pm25", "res_pm10", "res_o3"]]
        
        metrics_out = {}
        
        for pol in ["pm25", "pm10", "o3"]:
            y_target = df_training_data[f"obs_{pol}"] - df_training_data[f"phys_{pol}"]
            X = df_training_data[feature_cols]
            
            X_train, y_train = X.iloc[:train_end], y_target.iloc[:train_end]
            X_test, y_test = X.iloc[val_end:], y_target.iloc[val_end:]
            
            if HAS_XGBOOST:
                model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
            else:
                model = HistGradientBoostingRegressor(max_iter=100, max_depth=5, random_state=42)
                
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            mae = mean_absolute_error(y_test, y_pred)
            rmse = root_mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            self.models[pol] = model
            metrics_out[pol] = {"mae": round(float(mae), 3), "rmse": round(float(rmse), 3), "r2": round(float(r2), 3)}
            
            # Save artifact
            joblib.dump(model, os.path.join(self.model_dir, f"model_{pol}.pkl"))
            
        self.metrics = metrics_out
        self.is_trained = True
        joblib.dump({"metrics": metrics_out}, os.path.join(self.model_dir, "residual_metadata.pkl"))
        
        return {"status": "trained", "metrics": metrics_out}

    def predict_residual(
        self,
        pollutant: str,
        features: List[float]
    ) -> float:
        """Predicts residual error e(t) = C_observed - C_physics for a single timestep."""
        pol = pollutant.lower()
        if not self.is_trained or pol not in self.models:
            return 0.0  # Return 0 residual when model is not trained (unadjusted physics)
            
        try:
            X_in = np.array([features])
            res = float(self.models[pol].predict(X_in)[0])
            return res
        except Exception:
            return 0.0


# Global singleton instance
ml_residual_engine = ResidualCorrectionModel()
