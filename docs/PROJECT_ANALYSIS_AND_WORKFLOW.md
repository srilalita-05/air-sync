# AirSync — Comprehensive Project Analysis, Workflow & Scientific Technical Guide

**Problem Statement ID:** SIH26082 — Air Pollution–Weather Coupled Forecasting System (Delhi-NCR Focus)  
**Team:** Semantic Souls (Smart India Hackathon 2026)  
**Architecture:** 2-Stage Physics-Informed Engine + ML Residual Correction  

---

## 1. Executive Summary & Core Objective

AirSync is an atmospheric forecasting and decision-support platform designed specifically for the complex micro-climate and severe winter air pollution challenges of the **National Capital Region (Delhi-NCR)**. 

Traditional approaches to air quality forecasting suffer from two extremes:
1. **Pure Machine Learning / Deep Learning Models (Black Boxes):** High predictive power in standard regimes, but prone to catastrophic failures during unprecedented weather extremes, physical unfaithfulness (violating mass conservation or negative concentrations), and complete lack of explainability for environmental policymakers.
2. **Full Regional 3D Chemical Transport Models (WRF-Chem / CMAQ):** Computationally exorbitant, requiring supercomputers, high-latency runs (several hours per forecast), and heavy configuration overhead unsuitable for rapid operational decision-support.

### AirSync's Solution: 2-Stage Physics-Informed Architecture
AirSync bridges this divide through a **transparent 2-stage hybrid engine**:
- **Stage 1 (Physics Baseline):** A dimensionally consistent atmospheric mass-balance single-box continuity differential solver that enforces the laws of physics (boundary layer volume dilution, advection, dry deposition, rain washout scavenging, and photochemical ozone activity).
- **Stage 2 (Machine Learning Residual Correction):** A gradient boosting model (XGBoost / HistGradientBoosting) trained strictly on historical systematic errors ($e(t) = C_{\text{obs}}(t) - C_{\text{physics}}(t)$) without lookahead data leakage.

---

## 2. End-to-End System Workflow

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   EXTERNAL DATA INGESTION                                 │
│  - Operational Forecast: Open-Meteo API / NOAA GFS / IMD (Wind, PBLH, Temp, Precip, Solar)│
│  - Ground Truth: CPCB CAAQMS Stations (OpenAQ API) - Origin Anchor C_obs(T)               │
│  - Upwind Satellite Hotspots: NASA FIRMS (VIIRS / MODIS Stubble Burning Active Fires)     │
│  - Offline Reanalysis: ECMWF ERA5 (Training / Historical Bias Evaluation)                │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                           DATA VALIDATION & ADAPTATION LAYER                              │
│  - Physical bounds checking & data sanitization (`app/data/validator.py`)                 │
│  - Missing variable fallback strategies & imputation                                      │
│  - Synthetic fallback scenario generation (`app/data/synthetic.py`)                      │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                             PHYSICS DIAGNOSTICS MODULE                                    │
│  - Meteorological wind decomposition (u, v vectors)                                       │
│  - Ventilation Coefficient (VC = U * PBLH)                                                │
│  - Accumulation potential vs. Inversion separation (Inversion requires vertical dT/dz)    │
│  - Wet scavenging removal flag and photochemical proxy scores                             │
│  (`app/physics/diagnostics.py`)                                                           │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                        STAGE 1: PHYSICS BASELINE FORECAST ENGINE                          │
│  - Dimensionally consistent mass-balance box model (`app/physics/box_model.py`)           │
│  - Calculates analytical transition: C(t + dt) = C_eq + (C(t) - C_eq) * exp(-k_loss * dt)│
│  - Outputs pure physics-driven concentrations (PM2.5, PM10, O3, NO2, SO2, CO)             │
│  (`app/physics/engine.py`)                                                                │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                     STAGE 2: ML RESIDUAL CORRECTION (NO DATA LEAKAGE)                     │
│  - Input Features: Horizon step weather forecast, physics baseline, origin observation T, │
│    forecast lead time (h), calendar harmonics (sin/cos hour)                              │
│  - XGBoost / HistGradientBoosting predicts systematic bias e(t)                           │
│  - Combined Forecast: C_final(t) = max(0, C_physics(t) + e_predicted(t))                 │
│  (`app/forecasting/ml_residual.py`)                                                       │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                               DECISION & EXPLAINABILITY LAYER                             │
│  1. CPCB Indian AQI Calculation (Sub-indices & Dominant Pollutant) (`app/aqi/`)           │
│  2. "WHY?" Driver Attribution (Stagnation, Inversion, Fires, Rain) (`app/explainability/`) │
│  3. "WHEN?" Severe Episode Detection (Onset, Peak, Recovery state machine) (`app/episode/`)│
│  4. "WHERE?" Kinematic Plume Dispersion Trajectory (`app/plume/`)                         │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DELIVERY & PRESENTATION                                   │
│  - FastAPI REST API Endpoints (`app/api/routes.py` on port 8000)                          │
│  - Interactive Glassmorphic Web Dashboard (`frontend/` Leaflet Map + Chart.js Graphs)     │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack & Importance of Each Component

| Technology / Library | Version / Scope | Role in AirSync | Technical Importance & Justification |
| :--- | :--- | :--- | :--- |
| **Python** | `>= 3.10` | Core Language | The de facto standard for atmospheric science, scientific computing, and machine learning integration. |
| **FastAPI** | `>= 0.115.0` | Backend REST Framework | Asynchronous, ultra-fast Python web framework with native Pydantic typing, automatic OpenAPI / Swagger documentation generation, and high concurrency for real-time sensor and forecast querying. |
| **Uvicorn** | `>= 0.30.0` | ASGI Production Web Server | Lightning-fast asynchronous server implementation for Python based on `uvloop` and `httptools`, running the FastAPI application and static dashboard. |
| **Pydantic** | `>= 2.0.0` | Schema & Data Validation | Strictly enforces typed data contracts across meteorological input payloads, forecast requests, and API responses; catches malformed data before execution. |
| **NumPy** | `>= 1.26.0` | Numerical Array Computing | Provides vectorization, trigonometric wind vector transformations (zonal $u$ and meridional $v$), exponential decays, and high-performance array operations. |
| **Pandas** | `>= 2.0.0` | Data Wrangling & Timeseries | Structures historical paired datasets (merging weather reanalysis with ground observations), handles chronological sorting, sliding windows, and feature engineering. |
| **XGBoost** | `>= 2.0.0` | Gradient Boosted Decision Trees | Industry-standard ensemble learning framework used in Stage 2 to learn non-linear residual bias patterns without data leakage. Offers L1/L2 regularization to prevent overfitting. |
| **Scikit-Learn** | `>= 1.5.0` | Machine Learning Utilities | Supplies fallback `HistGradientBoostingRegressor`, validation metrics (`mean_absolute_error`, `root_mean_squared_error`, `r2_score`), and data preprocessing pipelines. |
| **Joblib** | `>= 1.4.0` | Model Serialization | Efficiently persists and loads trained scikit-learn and XGBoost model artifacts (`.pkl`) to disk without re-compilation overhead. |
| **SciPy** | `>= 1.10.0` | Scientific & Statistical Algorithms | Provides advanced mathematical distributions, interpolation utilities, and physical solvers. |
| **Requests / HTTPX** | `>= 2.30.0 / >= 0.27.0` | Synchronous & Asynchronous HTTP | Handles external REST API calls to Open-Meteo, OpenAQ, and NASA FIRMS endpoints, plus powers automated backend integration tests via `TestClient`. |
| **Pytest** | `>= 8.0.0` | Automated Testing Suite | Provides regression testing across physical units, mass conservation, CPCB AQI breakpoints, episode state machines, plume trajectories, and API routes. |
| **HTML5 / CSS3 / Vanilla JS** | Modern Standards | Web Dashboard Frontend | Lightweight, dependency-free frontend avoiding bloated single-page framework overhead. Provides responsive, glassmorphic dark-theme UI with 60fps micro-animations. |
| **Leaflet.js** | `1.9.4` (CDN) | Interactive GIS Geospatial Mapping | Renders OpenStreetMap base layers, active NASA FIRMS stubble burning hotspots, and the downwind expanding Gaussian plume dispersion envelope over Delhi-NCR. |
| **Chart.js** | `4.x` (CDN) | Real-Time Time-Series Visualization | Plots multi-pollutant 72-hour forecast timelines, CPCB category bands, physics baseline vs. ML-corrected curves, and episode peak markers. |

---

## 4. Complete Mathematical & Physical Formulations

### 4.1 Atmospheric Mass-Balance Box Model (`app/physics/box_model.py`)
The atmospheric boundary layer over Delhi ($L = 50,000\,\text{m}$) is modeled as a continuously stirred single box governed by the differential continuity equation:

$$\frac{dC}{dt} = \frac{E}{H} - \frac{U}{L}(C - C_{bg}) - \frac{v_d}{H}C - \Lambda(R)C + P_{\text{chem}}$$

Where:
- $C$: Pollutant concentration $[\mu\text{g}/\text{m}^3]$
- $E$: Surface emission flux rate $[\mu\text{g}/(\text{m}^2\cdot\text{s})]$
- $H$: Planetary Boundary Layer Height (PBLH) $[\text{m}]$
- $U$: Horizontal wind speed $[\text{m}/\text{s}]$
- $L$: Characteristic domain length scale $[\text{m}] = 50,000\,\text{m}$
- $C_{bg}$: Background upwind concentration $[\mu\text{g}/\text{m}^3]$
- $v_d$: Dry deposition velocity $[\text{m}/\text{s}]$ ($0.001$ for PM2.5, $0.005$ for PM10)
- $\Lambda(R)$: Precipitation wet scavenging coefficient $[\text{s}^{-1}]$
- $P_{\text{chem}}$: Photochemical ozone formation rate proxy $[\mu\text{g}/(\text{m}^3\cdot\text{s})]$

#### Analytical Solution:
Grouping the total first-order loss rate $k_{\text{loss}}$ $[\text{s}^{-1}]$ and total volumetric source rate $P_{\text{total}}$ $[\mu\text{g}/(\text{m}^3\cdot\text{s})]$:

$$k_{\text{loss}} = \frac{U}{L} + \frac{v_d}{H} + \Lambda(R)$$

$$P_{\text{total}} = \frac{E}{H} + \frac{U}{L}C_{bg} + P_{\text{chem}}$$

The steady-state asymptotic equilibrium concentration is:
$$C_{\text{eq}} = \frac{P_{\text{total}}}{k_{\text{loss}}}$$

Over a discrete timestep $\Delta t = 3600\,\text{s}$ (1 hour), the analytical integration yields:
$$C(t + \Delta t) = C_{\text{eq}} + \big(C(t) - C_{\text{eq}}\big) \cdot e^{-k_{\text{loss}}\Delta t}$$

---

### 4.2 Precipitation Wet Scavenging Rate
Precipitation actively washes out particulate matter via aerosol-hydrometeor impaction:
$$\Lambda(R) = a \cdot R^b \quad [\text{s}^{-1}]$$

- $R$: Rainfall intensity $[\text{mm}/\text{h}]$
- $a = 1.0 \times 10^{-4}$ for PM2.5, $1.5 \times 10^{-4}$ for PM10
- $b = 0.8$ (power-law scavenging exponent)

---

### 4.3 Ventilation Coefficient & Accumulation Potential (`app/physics/diagnostics.py`)
Ventilation Coefficient ($VC$) measures the flushing capacity of the boundary layer per unit horizontal width:
$$VC = U \times \text{PBLH} \quad [\text{m}^2/\text{s}]$$

- **$VC > 5000\,\text{m}^2/\text{s}$**: Strong ventilation / rapid pollutant dispersion.
- **$1500 < VC \le 5000\,\text{m}^2/\text{s}$**: Moderate dispersion.
- **$800 < VC \le 1500\,\text{m}^2/\text{s}$**: Poor ventilation / accumulation potential.
- **$VC \le 800\,\text{m}^2/\text{s}$**: Severe stagnation / critical air entrapment.

---

### 4.4 Scientific Inversion vs. Poor Ventilation Separation
To prevent scientific hallucination:
- Poor ventilation is determined strictly from $VC$.
- **Thermal Inversion** ($\frac{dT}{dz} > 0$) is diagnosed **only** when vertical temperature sounding data is provided:
$$\Gamma = \frac{T_{\text{upper}} - T_{\text{surface}}}{\Delta z / 100} \quad [^\circ\text{C}/100\,\text{m}]$$
If vertical temperature data is absent, `inversion_detected = None` with status `"vertical_data_unavailable"`. Low PBL + calm wind alone is **never** falsely labeled as an inversion.

---

### 4.5 Meteorological Wind Decomposition
Meteorological wind direction $\theta$ is the direction *from* which the wind blows:
$$u_{\text{east}} = -U \cdot \sin(\theta)$$
$$v_{\text{north}} = -U \cdot \cos(\theta)$$

---

### 4.6 Kinematic Plume Trajectory & Gaussian Dispersion (`app/plume/trajectory.py`)
For stubble burning hotspots detected by NASA FIRMS at $(\phi_{\text{fire}}, \lambda_{\text{fire}})$:
Flow direction angle: $\theta_{\text{flow}} = (\theta_{\text{wind}} + 180^\circ) \pmod{360^\circ}$.

Displacement over time $t = h \times 3600\,\text{s}$:
$$\Delta x(t) = U \cdot \sin(\theta_{\text{flow}}) \cdot t$$
$$\Delta y(t) = U \cdot \cos(\theta_{\text{flow}}) \cdot t$$

The horizontal expanding Gaussian plume buffer radius is:
$$\sigma_r(t) = \sqrt{\sigma_0^2 + 2 K_y t} \quad [\text{m}]$$
Where $\sigma_0 = 500 + \min(500, \text{FRP} \times 5)\,\text{m}$, and $K_y \approx 50\,\text{m}^2/\text{s}$ is the horizontal eddy diffusivity proxy.

Downwind influence score on Delhi-NCR:
$$S_{\text{influence}} = \exp\left(-\frac{1}{2}\left(\frac{d_{\text{min}}}{\max(2000, \sigma_r)}\right)^2\right) \times \left(0.4 + 0.6 \cdot \min(1.0, \frac{\text{FRP}}{200})\right)$$

---

### 4.7 Official Indian CPCB Air Quality Index Formulation (`app/aqi/calculator.py`)
CPCB (Central Pollution Control Board, 2014) piecewise linear sub-index formula:

$$I_p = I_{\text{low}} + \frac{I_{\text{high}} - I_{\text{low}}}{C_{\text{high}} - C_{\text{low}}} \cdot (C_p - C_{\text{low}})$$

Overall AQI is determined by the maximum sub-index across monitored pollutants:
$$\text{AQI}_{\text{overall}} = \max(I_{\text{PM2.5}}, I_{\text{PM10}}, I_{\text{O3}}, I_{\text{NO2}}, I_{\text{SO2}}, I_{\text{CO}}, \dots)$$

The pollutant yielding $\text{AQI}_{\text{overall}}$ is designated as the **Dominant Pollutant**.

---

## 5. Machine Learning Residual Architecture & Training Process

### 5.1 No-Data-Leakage Design
For any forecast starting at initialization origin $T$:
- **Available Inputs:** Future meteorological forecasts $(T+1 \dots T+72)$, Stage 1 physics forecasts $(T+1 \dots T+72)$, and ground pollutant observation $C_{\text{obs}}(T)$ available at origin $T$.
- **Forbidden Inputs:** Future ground observations $C_{\text{obs}}(T+h)$ where $h > 0$.
- **Target Variable:** Systematic physical residual:
$$e(t) = C_{\text{observed}}(t) - C_{\text{physics}}(t)$$
- **Combined Inference:**
$$C_{\text{final}}(t) = \max\big(0, C_{\text{physics}}(t) + \hat{e}(t)\big)$$

### 5.2 Feature Vector Construction (20 Dimensions)
1. `wind_speed_ms`: Wind speed at $T+h$
2. `u_wind`: Zonal wind component at $T+h$
3. `v_wind`: Meridional wind component at $T+h$
4. `pbl_height_m`: Planetary boundary layer height at $T+h$
5. `vc`: Ventilation coefficient $(U \times \text{PBLH})$ at $T+h$
6. `temperature_c`: Surface 2m temperature at $T+h$
7. `relative_humidity`: Relative humidity percentage at $T+h$
8. `precipitation_mm`: Hourly rainfall at $T+h$
9. `solar_radiation_wm2`: Downwelling shortwave solar flux at $T+h$
10. `fire_influence`: NASA FIRMS stubble burning proximity index at $T+h$
11. `phys_pm25`: Physics baseline forecast for PM2.5 at $T+h$
12. `phys_pm10`: Physics baseline forecast for PM10 at $T+h$
13. `phys_o3`: Physics baseline forecast for O3 at $T+h$
14. `pm25_origin`: Ground observed PM2.5 at origin $T$
15. `pm10_origin`: Ground observed PM10 at origin $T$
16. `o3_origin`: Ground observed O3 at origin $T$
17. `horizon_hour`: Lead time $h \in [0, 72]$
18. `hour_sin`: $\sin(2\pi \cdot (\text{hour}\%24) / 24)$
19. `hour_cos`: $\cos(2\pi \cdot (\text{hour}\%24) / 24)$
20. `day_of_week`: Day of week index $[0 \dots 6]$

---

## 6. Step-by-Step Model Training & Testing Procedures

### Step 1: Environment Setup
Ensure the Python virtual environment is activated and dependencies installed:
```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Running Automated Unit & Integration Tests
Execute the complete test suite using `pytest`:
```bash
.venv\Scripts\python.exe -m pytest -v
```
**Verification Scope:**
- 18 automated tests passing across API endpoints, physical mass conservation, AQI breakpoints, episode detection, and plume advection.

### Step 3: Offline Model Training
To train the Stage 2 ML residual correction model on paired data:
```bash
# Option A: Train using synthetic Delhi-NCR scenario (built-in default)
.venv\Scripts\python.exe scripts/train_on_real_data.py

# Option B: Train using real paired dataset (ERA5 + CPCB + FIRMS)
.venv\Scripts\python.exe scripts/train_on_real_data.py --input-csv path/to/paired_training_data.csv
```

**Artifacts Generated in `models/`:**
- `models/model_pm25.pkl`
- `models/model_pm10.pkl`
- `models/model_o3.pkl`
- `models/residual_metadata.pkl` (Validation metrics: MAE, RMSE, $R^2$)

### Step 4: Online Model Retraining via REST API
AirSync supports triggering model retraining dynamically over HTTP:
```bash
# POST request to retrain
curl -X POST http://localhost:8000/model/train

# Check training status and validation metrics
curl -X GET http://localhost:8000/model/status
```

### Step 5: Launching & Validating the Interactive Platform
Start the backend web server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```
- **Web Dashboard:** [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/)
- **Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health & Model Status:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 7. Summary of REST Endpoints

| Endpoint | Method | Payload / Params | Return Data |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | None | Engine status, active physics model, and ML training state |
| `/forecast/72h` | `POST` | `Forecast72hRequest` (scenario, start_time, station_id) | 72-hour hourly forecasts, AQI, drivers, and episode status |
| `/explain` | `POST` | `ExplainRequest` (weather_input) | Structured physics driver ranking and narrative summary |
| `/episode` | `POST` | `EpisodeRequest` (timeline, threshold_aqi) | Onset, peak, recovery timestamps and episode duration |
| `/plume` | `POST` | `PlumeRequest` (fire_lat, fire_lon, wind, frp) | 2D kinematic advection points and downwind influence score |
| `/aqi` | `POST` | `AqiRequest` (pollutant concentrations) | CPCB sub-indices, overall AQI, and dominant pollutant |
| `/data/validate`| `POST` | Raw JSON dictionary | Cleaned data, flags, and missing variable fallbacks |
| `/model/train` | `POST` | None | Retrains ML residual models and returns MAE, RMSE, R² |
| `/model/status`| `GET` | None | Current validation metrics and model state |
