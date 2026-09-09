"""
AirSync Offline ML Residual Model Training Script.

Trains the Stage 2 ML residual correction model (XGBoost / Gradient Boosting)
using paired historical observations (ERA5 Reanalysis + CPCB CAAQMS + NASA FIRMS).

Usage:
    python scripts/train_on_real_data.py --input-csv data/sample/training_paired_dataset.csv
"""

from app.data.synthetic import generate_synthetic_scenario
from app.physics.engine import estimate_pollutants
from app.forecasting.ml_residual import ml_residual_engine
import os
import sys
import argparse
import numpy as np
import pandas as pd

# Add backend app to path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..")))


def main():
    parser = argparse.ArgumentParser(
        description="AirSync ML Residual Model Training Script")
    parser.add_argument(
        "--input-csv",
        type=str,
        default=None,
        help="Path to input paired CSV dataset")
    args = parser.parse_args()

    print("==========================================================")
    print("AirSync Stage 2 ML Residual Model Training")
    print("==========================================================")

    if args.input_csv and os.path.exists(args.input_csv):
        print(
            f"Loading real historical training dataset from: {
                args.input_csv}")
        df_train = pd.read_csv(args.input_csv)
    else:
        print("No external CSV specified. Generating synthetic training dataset representing Delhi-NCR...")
        synth = generate_synthetic_scenario(
            "stagnant_winter", horizon_hours=300)
        records = []
        for pt in synth["timeline"]:
            phys = estimate_pollutants(pt)
            obs_pm25 = max(
                0.0,
                phys["pm25_ugm3"] +
                18.0 *
                np.sin(
                    pt["hour"] /
                    5.0) +
                4.0 *
                np.random.randn())
            obs_pm10 = max(
                0.0,
                phys["pm10_ugm3"] +
                28.0 *
                np.sin(
                    pt["hour"] /
                    5.0) +
                6.0 *
                np.random.randn())
            obs_o3 = max(
                0.0,
                phys["o3_ugm3"] +
                9.0 *
                np.cos(
                    pt["hour"] /
                    6.0) +
                2.0 *
                np.random.randn())

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
                "obs_pm25": obs_pm25,
                "obs_pm10": obs_pm10,
                "obs_o3": obs_o3,
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

    print(
        f"Dataset shape: {
            df_train.shape[0]} rows, {
            df_train.shape[1]} columns.")
    print("Fitting XGBoost / GradientBoosting ML residual model without data leakage...")

    result = ml_residual_engine.train(df_train)

    print("\nTraining Results:")
    print("----------------------------------------------------------")
    for pol, metrics in result.get("metrics", {}).items():
        print(
            f"Pollutant: {
                pol.upper():<6} | MAE: {
                metrics['mae']:<6.2f} | RMSE: {
                metrics['rmse']:<6.2f} | R²: {
                    metrics['r2']:<6.2f}")
    print("----------------------------------------------------------")
    print(
        f"Model artifacts successfully saved to: {
            ml_residual_engine.model_dir}")


if __name__ == "__main__":
    main()
