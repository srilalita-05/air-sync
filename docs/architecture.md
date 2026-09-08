# AirSync System Architecture

**Problem Statement ID:** SIH26082  
**Project Name:** AirSync — Web-based Air Pollution–Weather Coupled Forecasting Platform  
**Team:** Semantic Souls (SIH 2026)

---

## 1. High-Level Data Flow

```
+-----------------------------------------------------------------------+
|                            DATA ADAPTERS                              |
|  Operational Weather Forecast (IMD/GFS)   CPCB CAAQMS   NASA FIRMS     |
|  Historical ERA5 Reanalysis (Offline Training/Validation Only)        |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                    INGESTION, CLEANING & VALIDATION                   |
|                   (app/data/validator.py & providers.py)               |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                   PHYSICS DIAGNOSTICS MODULE                          |
|             (Ventilation VC, Wind (u,v), Scavenging,                    |
|             Inversion vs Accumulation Potential)                      |
|                 (app/physics/diagnostics.py)                          |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                STAGE 1: PHYSICS-INFORMED BASELINE FORECAST            |
|             Mass-Balance Single-Box Model Differential Solver         |
|                     (app/physics/box_model.py)                        |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                STAGE 2: MACHINE LEARNING RESIDUAL MODEL               |
|            XGBoost / HistGradientBoosting Bias Correction             |
|                 (No-Data-Leakage Origin Features)                     |
|                   (app/forecasting/ml_residual.py)                    |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                           FINAL FORECAST                              |
|           C_final(t) = max(0, C_physics(t) + e_residual(t))          |
+-------------------+-------------------------------+-------------------+
                    |                               |
                    v                               v
+-----------------------+               +-------------------------------+
|  EXPLAINABILITY ENGINE |               | DATA-DRIVEN EPISODE DETECTOR  |
|  "WHY?" Drivers Rank  |               | "WHEN?" Onset, Peak, Recovery |
| (app/explainability/) |               |     (app/episode/detector.py)   |
+-----------+-----------+               +---------------+---------------+
            |                                           |
            +-------------------+-----------------------+
                                |
                                v
+-----------------------------------------------------------------------+
|                         FASTAPI BACKEND REST API                      |
|      /health  /forecast/72h  /explain  /episode  /plume  /aqi         |
|                          (app/api/routes.py)                          |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                     INTERACTIVE WEB DASHBOARD UI                      |
|        Single-Page Glassmorphic Web App (HTML/CSS/JS/Leaflet/Chart.js) |
|                              (frontend/)                              |
+-----------------------------------------------------------------------+
```

---

## 2. Directory Layout & Module Responsibilities

```
d:\Projects\air sync\
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entrypoint & Static dashboard mounting
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py            # REST API endpoints (/health, /forecast/72h, /explain, /plume, /aqi)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── payload.py           # Pydantic request/response schemas
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── validator.py         # Ingestion validator & missing variable handler
│   │   │   ├── providers.py         # Abstract data provider adapters (ERA5 vs Operational Weather)
│   │   │   └── synthetic.py         # Synthetic Delhi-NCR scenario generator (tagged synthetic)
│   │   ├── physics/
│   │   │   ├── __init__.py
│   │   │   ├── units.py             # Physical units & dimensional documentation
│   │   │   ├── parameters.py        # Centralized empirical parameters & default thresholds
│   │   │   ├── box_model.py         # Dimensionally consistent mass-balance box model solver
│   │   │   ├── diagnostics.py       # Reusable physical indicators & inversion vs ventilation
│   │   │   └── engine.py            # Physics baseline coordinator
│   │   ├── forecasting/
│   │   │   ├── __init__.py
│   │   │   ├── ml_residual.py       # XGBoost/GradientBoosting ML residual model without data leakage
│   │   │   └── engine.py            # Two-stage forecast coordinator
│   │   ├── explainability/
│   │   │   ├── __init__.py
│   │   │   └── engine.py            # Driver attribution & explanation generator
│   │   ├── plume/
│   │   │   ├── __init__.py
│   │   │   └── trajectory.py        # Kinematic parcel advection & Gaussian dispersion envelope
│   │   ├── episode/
│   │   │   ├── __init__.py
│   │   │   └── detector.py          # Data-driven episode state machine (onset, peak, recovery)
│   │   └── aqi/
│   │       ├── __init__.py
│   │       ├── breakpoints.py       # Official CPCB 8-pollutant breakpoint configuration (2014)
│   │       └── calculator.py        # Isolated CPCB sub-index & overall AQI calculator
│   ├── tests/
│   │   ├── test_units_and_physics.py
│   │   ├── test_inversion_vs_ventilation.py
│   │   ├── test_aqi.py
│   │   ├── test_plume.py
│   │   ├── test_episode.py
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   ├── index.html                   # Glassmorphic web dashboard
│   ├── css/style.css                # Modern CSS design system
│   └── js/app.js                    # Dynamic chart, map, and API controller
├── docs/
│   ├── architecture.md
│   └── scientific_basis.md
├── .env.example
├── docker-compose.yml
└── README.md
```
