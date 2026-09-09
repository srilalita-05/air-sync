# AirSync — Air Pollution & Weather Coupled Forecasting System

**Smart India Hackathon 2026 (SIH 2026)**  
**Problem Statement ID:** SIH26082 — Air Pollution–Weather Coupled Forecasting System (Delhi-NCR Focus)  
**Team:** Semantic Souls  

---

## 🌟 What is AirSync?

AirSync is a web-based, physics-informed forecasting and decision-support platform designed for the **Delhi-NCR** region. 

Unlike traditional black-box machine learning models or heavy supercomputer weather models (like WRF-Chem), AirSync combines **transparent atmospheric physics** with **lightweight machine learning residual correction** to deliver accurate 72-hour pollution forecasts while explaining *why* pollution changes and *where* it is moving.

> 📢 **Key Positioning:**  
> *"AirSync doesn't just forecast pollution. It explains why pollution will change, predicts where it will move, and identifies when a severe episode is likely to peak."*

---

## 🚀 The 4 Core Questions AirSync Answers

1. 📊 **WHAT?**  
   Provides detailed 72-hour hourly forecasts for major pollutants (**PM2.5, PM10, O3, NO2, SO2, CO**) and calculates the official Indian Air Quality Index (AQI).

2. 🔍 **WHY?**  
   Explains meteorological drivers behind pollution changes (e.g. low wind stagnation, shallow boundary layer height, temperature inversion, rain scavenging, upwind biomass fires).

3. 📍 **WHERE?**  
   Tracks stubble burning smoke plumes from NASA FIRMS satellite data and predicts downwind transport into Delhi-NCR using wind vectors.

4. ⏰ **WHEN?**  
   Detects severe pollution episodes in advance, providing exact onset, peak window, and recovery timing.

---

## 🔬 How AirSync Works (2-Stage Engine)

```
        Raw Weather & Satellite Data
                    │
                    ▼
     Stage 1: Physics Baseline Forecast
   (Mass-Balance Box Model & Wind Vectors)
                    │
                    ▼
  Stage 2: Machine Learning Residual Correction
 (XGBoost / Gradient Boosting Error Alignment)
                    │
                    ▼
       Final 72-Hour Air Quality Forecast
   + Driver Attribution + Episode Timeline
```

### Stage 1: Physics-Informed Baseline
- **Dispersion & Ventilation:** Calculates the Ventilation Coefficient ($VC = \text{Wind Speed} \times \text{Boundary Layer Height}$) to measure atmospheric flushing capacity.
- **Rain Washout:** Simulates wet deposition scavenging where rainfall actively washes out particulate matter.
- **Thermal Inversion:** Distinguishes poor ventilation from true thermal inversion layers (only confirmed when vertical temperature profile data is present).

### Stage 2: Machine Learning Residual Correction
- Fits the systematic difference between physical baseline estimates and real ground observations without lookahead data leakage.

---

## ⚡ Quickstart Guide

### 1. Create & Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
python -m pytest
```

### 4. Launch AirSync Web Platform
```bash
python -m uvicorn app.main:app --reload --port 8000
```

- 🌐 **Web Dashboard:** [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/)
- 📖 **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 REST API Summary

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health check and active physics model status |
| `POST` | `/forecast/72h` | 72-hour hourly forecast with AQI, drivers, & episode status |
| `POST` | `/explain` | Detailed physical driver breakdown explaining pollution trends |
| `POST` | `/episode` | Data-driven episode onset, peak, and recovery detection |
| `POST` | `/plume` | Kinematic biomass fire plume trajectory simulator |
| `POST` | `/aqi` | Official CPCB Indian AQI sub-index calculator |
| `POST` | `/data/validate` | Data validation and missing value fallbacks report |
| `POST` | `/model/train` | Retrain ML residual correction model |
| `GET` | `/model/status` | Model training status and performance metrics (MAE, RMSE, R²) |

---

## 📂 Project Structure

```
air-sync/
├── app/                        # FastAPI Backend Application
│   ├── api/routes.py           # REST API Endpoints
│   ├── aqi/                    # Official CPCB AQI Breakpoint Calculator
│   ├── data/                   # Data Validators & Provider Adapters
│   ├── episode/                # Data-driven Severe Episode Detector
│   ├── explainability/         # Physics Driver Attribution Engine
│   ├── forecasting/            # 2-Stage Physics + ML Forecast Coordinator
│   ├── physics/                # Box Model, Diagnostics, & Unit Registry
│   └── plume/                  # Biomass Burning Plume Simulator
├── frontend/                   # Web Dashboard (HTML5, CSS3, JS, Leaflet, Chart.js)
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── tests/                      # Automated Pytest Test Suite
├── docs/                       # Technical & Architectural Documentation
├── .env.example                # API Key Configuration Template
├── .gitignore                  # Git Ignore Rules
└── requirements.txt            # Python Dependencies
```

---

## 👥 Team & License
Built for **Smart India Hackathon 2026** by **Team Semantic Souls**.  
Licensed under the MIT License.

---

## 🔄 Complete End-to-End System Workflow

AirSync operates via an end-to-end, multi-stage pipeline coupling atmospheric physics, machine learning, and decision-support explainability:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               1. DATA INGESTION LAYER                                  │
│  • Surface Meteorology: Open-Meteo API / ERA5 Reanalysis (Wind, PBLH, Temp, RH, Rain)  │
│  • Ground Air Quality: CPCB CAAQMS Station Real-time Ground Monitors                   │
│  • Satellite Fire Observations: NASA FIRMS (VIIRS/MODIS Thermal Hotspots & FRP)        │
│  • Vertical Atmosphere: Radiosonde / Reanalysis Profiles (Multi-level Temperatures)    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        2. VALIDATION & SANITY FALLBACK ENGINE                          │
│  • Schema verification (Pydantic v2)                                                   │
│  • Range checks against physical limits (e.g. non-negative wind speed, PBLH > 50 m)    │
│  • Graceful degradation & sensor fault imputation via spatial/temporal interpolation   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      3. STAGE 1: PHYSICS BASELINE FORECAST ENGINE                      │
│  • Solves Mass-Balance Atmospheric Box Model continuity differential equation          │
│  • Computes advective transport flushing (Wind Speed / Domain Length)                  │
│  • Calculates surface emissions, background inflow, and dry deposition velocity        │
│  • Calculates precipitation wet scavenging washout: Lambda(R) = a * R^b               │
│  • Incorporates photochemical Ozone production proxy (Solar radiation + Temp + Cloud)   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     4. REUSABLE ATMOSPHERIC DIAGNOSTICS ENGINE                         │
│  • Ventilation Coefficient (VC = U * PBLH in m²/s)                                     │
│  • Wind velocity decomposition (Zonal u-east & Meridional v-north components)          │
│  • Accumulation Potential Score (0.0 to 1.0 stagnation scale)                          │
│  • Thermal Inversion Assessment (Lapse Rate dT/dz strictly evaluated if profiles exist)│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               5. STAGE 2: MACHINE LEARNING RESIDUAL CORRECTION ENGINE                  │
│  • Target: Systematic bias e(t) = C_observed(t) - C_physics(t)                         │
│  • Model: XGBoost Regressor / HistGradientBoosting Regressor                          │
│  • Feature Set: Weather at T+h, Physics baseline at T+h, Origin observation C(T),      │
│    Horizon step h, Diurnal calendar sin/cos features                                  │
│  • STRICT ZERO-LEAKAGE: No future pollutant observations consumed past origin T        │
│  • Final Pollutant Concentration: C_final(t) = max(0, C_physics(t) + e_predicted(t))   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          6. CPCB AIR QUALITY INDEX CALCULATOR                          │
│  • Official Indian CPCB piecewise linear sub-index formula                             │
│  • Evaluates 8 pollutants (PM2.5, PM10, O3, NO2, SO2, CO, NH3, Pb)                     │
│  • Determines Overall AQI = max(sub-indices) and identifies dominant pollutant         │
│  • Assigns official CPCB color hex codes and health advisory categories                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
┌──────────────────────────────────────────┐  ┌──────────────────────────────────────────┐
│        7. EXPLAINABILITY ENGINE          │  │       8. SEVERE EPISODE DETECTOR         │
│ • Ranks physical drivers by severity:    │  │ • Analyzes 72-hour forecast trajectory   │
│   - Severe Stagnation (VC < 800 m²/s)    │  │ • State Machine classification:          │
│   - Low Wind Speed (< 1.5 m/s)           │  │   "normal" -> "onset" -> "rising" ->     │
│   - Shallow Boundary Layer (< 300 m)     │  │   "peak" -> "recovery"                   │
│   - Confirmed Inversion (dT/dz > 0)      │  │ • Identifies onset time, peak AQI window,│
│   - Rain Washout Scavenging (> 2 mm/h)   │  │   recovery hour, and total duration      │
│   - Upwind Biomass Fire Influence        │  └────────────────────┬─────────────────────┘
│ • Generates human-readable narrative     │                       │
└────────────────────┬─────────────────────┘                       │
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   9. BIOMASS SMOKE PLUME KINEMATIC SIMULATOR                           │
│  • 2D Kinematic Advection using surface wind vectors                                   │
│  • Expanding Gaussian dispersion envelope: sigma_r(t) = sqrt(sigma_0^2 + 2*Ky*t)       │
│  • Proximity-weighted downwind influence score [0.0 - 1.0] for Delhi-NCR receptors     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       10. PRESENTATION & INTEGRATION LAYER                             │
│  • FastAPI REST Backend (`/forecast/72h`, `/explain`, `/episode`, `/plume`, `/aqi`)    │
│  • Web Dashboard: Interactive Leaflet.js Map + Chart.js 72h Curves + Diagnostics Grid   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack & Library Importance

| Category | Technology / Library | Version / Spec | Critical Importance & Architectural Role in AirSync |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | `FastAPI` | `>=0.115.0` | Provides high-performance, asynchronous REST API endpoints with native Pydantic validation, automatic OpenAPI/Swagger documentation (`/docs`), and fast response times for real-time forecasting. |
| **ASGI Server** | `Uvicorn` | `>=0.30.0` | Production-grade ASGI web server that powers FastAPI with event-loop concurrency, enabling parallel handling of multiple forecast queries and simulation workloads. |
| **Data Validation** | `Pydantic` | `>=2.0.0` | Enforces strict type schemas and physical boundaries on meteorological inputs, CPCB measurements, and API payloads; rejects corrupted or nonsensical atmospheric data. |
| **Numerical Computing** | `NumPy` | `>=1.26.0` | High-speed vectorized computations for wind vector decomposition ($u, v$), trigonometric diurnal cyclic features ($\sin/\cos$), exponential plume diffusion, and array manipulations. |
| **Data Manipulation** | `Pandas` | `>=2.0.0` | Manages time-series data structures, chronological data splits (training/validation/testing), feature matrix assembly, and dataset ingestion for model training. |
| **Machine Learning** | `XGBoost` | `>=2.0.0` | Primary Stage 2 gradient-boosted decision tree algorithm. Learns non-linear atmospheric residuals $e(t) = C_{obs}(t) - C_{phys}(t)$ without overfitting, capturing complex local microclimate deviations. |
| **Machine Learning** | `Scikit-Learn` | `>=1.5.0` | Provides fallback gradient boosting (`HistGradientBoostingRegressor`), evaluation metrics (`MAE`, `RMSE`, $R^2$), and train/test splitting utilities. |
| **Model Persistence** | `Joblib` | `>=1.4.0` | Serializes trained machine learning models (`model_pm25.pkl`, `model_pm10.pkl`, `model_o3.pkl`) and evaluation metadata to disk, allowing instant model loading during server startup. |
| **Scientific Routines** | `SciPy` | `>=1.10.0` | Supplies mathematical optimization, scientific functions, and spatial calculation utilities for atmospheric dispersion and regression modeling. |
| **HTTP Clients** | `Requests` & `HTTPX` | `>=2.30.0` / `>=0.27.0` | Facilitates reliable synchronous and asynchronous HTTP requests to external APIs (Open-Meteo, NASA FIRMS fire API, Copernicus ERA5 reanalysis). |
| **Testing Framework** | `Pytest` | `>=8.0.0` | Comprehensive automated test suite ensuring physical constraints, zero-leakage ML pipeline, AQI breakpoints, episode state machine, and REST routes are bug-free. |
| **Frontend Core** | `HTML5` & `Vanilla CSS3` | Modern Standards | Ultra-fast, lightweight user interface without heavy build steps. Features dark mode, glassmorphism, responsive grid layouts, and clean typography via Google Fonts (Inter & Outfit). |
| **Frontend Logic** | `Vanilla JavaScript` | ES6+ | Lightweight asynchronous client that queries FastAPI endpoints, manipulates DOM elements in real-time, and handles interactive user inputs without framework bloat. |
| **GIS Mapping** | `Leaflet.js` | `1.9.4` | Interactive mobile-friendly map rendering Delhi-NCR monitoring stations, NASA FIRMS fire hotspots, wind directional vectors, and animated biomass plume dispersion envelopes. |
| **Data Visualization** | `Chart.js` | Latest CDN | Interactive, hardware-accelerated canvas charts displaying 72-hour hourly forecasts, comparing Stage 1 Physics baselines against Stage 2 ML-corrected outputs, and visualizing AQI category thresholds. |

---

## 📐 Mathematical & Physical Formulas Used

AirSync is built upon rigorous atmospheric physics combined with official regulatory formulas and machine learning error formulations:

### 1. Atmospheric Mass-Balance Box Model (Continuity Equation)
The concentration of pollutant $C$ over time inside a well-mixed urban boundary layer of height $H$ is governed by:

$$\frac{dC}{dt} = \frac{E}{H} - \frac{U}{L}(C - C_{bg}) - \frac{v_d}{H}C - \Lambda(R)C + P_{chem}$$

Where:
- $C$ = Pollutant concentration $[\mu\text{g}/\text{m}^3]$
- $E$ = Surface urban emission flux rate $[\mu\text{g}/(\text{m}^2\cdot\text{s})]$
- $H$ = Planetary Boundary Layer mixing Height (PBLH) $[\text{m}]$
- $U$ = Surface wind speed $[\text{m}/\text{s}]$
- $L$ = Characteristic domain length scale $[\text{m}]$ (Delhi-NCR $\approx 50,000\text{ m}$)
- $C_{bg}$ = Background upwind concentration $[\mu\text{g}/\text{m}^3]$
- $v_d$ = Dry deposition velocity $[\text{m}/\text{s}]$ ($\approx 0.001\text{ m/s}$ for PM2.5, $0.005\text{ m/s}$ for PM10)
- $\Lambda(R)$ = Wet precipitation scavenging rate $[\text{s}^{-1}]$
- $P_{chem}$ = Photochemical production proxy rate $[\mu\text{g}/(\text{m}^3\cdot\text{s})]$

#### Discrete Analytical Solution over Timestep $\Delta t$:
Combining total volumetric production $P_{total}$ and first-order loss rate $k_{loss}$:
$$k_{loss} = \frac{U}{L} + \frac{v_d}{H} + \Lambda(R)$$
$$P_{total} = \frac{E}{H} + \frac{U}{L}C_{bg} + P_{chem}$$
$$\text{Equilibrium Concentration: } C_{eq} = \frac{P_{total}}{k_{loss}}$$
$$C(t + \Delta t) = C_{eq} + \left(C(t) - C_{eq}\right) \cdot e^{-k_{loss} \cdot \Delta t}$$

---

### 2. Atmospheric Ventilation & Dispersion Diagnostics

- **Ventilation Coefficient ($VC$):**
  $$VC = U \times H \quad \left[\text{m}^2/\text{s}\right]$$
  - $VC < 800\text{ m}^2/\text{s}$: **Severe Stagnation** (high accumulation hazard)
  - $VC < 1500\text{ m}^2/\text{s}$: **Poor Ventilation** (inadequate dispersal)
  - $VC > 5000\text{ m}^2/\text{s}$: **Strong Dispersion** (rapid clean atmospheric flushing)

- **Wet Deposition Rain Scavenging Rate:**
  $$\Lambda(R) = a \cdot R^b \quad \left[\text{s}^{-1}\right]$$
  where $R$ is the rainfall intensity in $\text{mm/h}$, $a = 1.0 \times 10^{-4}$, and $b = 0.8$.

- **Meteorological Wind Vector Decomposition:**
  Wind direction $\theta$ is defined as the direction **from which** the wind blows:
  $$u_{east} = -U \cdot \sin\left(\frac{\pi}{180} \theta\right)$$
  $$v_{north} = -U \cdot \cos\left(\frac{\pi}{180} \theta\right)$$

- **Atmospheric Thermal Inversion Condition:**
  Confirmed **only** when vertical temperature profile data is available:
  $$\Gamma = \frac{T_{upper} - T_{surface}}{\Delta z / 100} \quad \left[^\circ\text{C}/100\text{m}\right]$$
  $$\text{Inversion Confirmed} \iff \Gamma > 0 \quad \left(\frac{\partial T}{\partial z} > 0\right)$$

- **Photochemical Ozone Production Proxy ($P_{chem}$):**
  $$P_{chem} = P_{max} \cdot \left(\frac{R_{solar}}{1000}\right) \cdot \left(\frac{T - 15}{25}\right) \cdot \left(1 - 0.8 \cdot \frac{\text{Cloud}\%}{100}\right) \cdot \min\left(2.0, \max\left(0.2, \frac{[\text{NO}_2]}{40}\right)\right)$$
  (Active only when $R_{solar} > 5\text{ W/m}^2$ and $T > 5^\circ\text{C}$).

---

### 3. Kinematic Biomass Smoke Plume & Gaussian Dispersion Envelope

- **Downwind Displacement over time $t$:**
  Flow heading $\phi = (\theta + 180^\circ) \pmod{360^\circ}$
  $$\Delta x = U \cdot \sin(\phi) \cdot t, \quad \Delta y = U \cdot \cos(\phi) \cdot t$$
  $$\text{Latitude}(t) = \text{Lat}_{fire} + \frac{\Delta y}{111,000}, \quad \text{Longitude}(t) = \text{Lon}_{fire} + \frac{\Delta x}{111,000 \cdot \cos(\text{Lat}_{fire})}$$

- **Expanding Gaussian Horizontal Diffusion Radius:**
  $$\sigma_r(t) = \sqrt{\sigma_0^2 + 2 \cdot K_y \cdot t}$$
  where initial thermal plume radius $\sigma_0 = 500\text{ m} + \min(500, \text{FRP} \times 5)$ and horizontal eddy diffusivity $K_y \approx 50\text{ m}^2/\text{s}$.

- **Downwind Receptor Proximity Influence Score:**
  $$S_{influence} = \exp\left(-\frac{1}{2}\left(\frac{d_{min}}{\max(2000, \sigma_r)}\right)^2\right) \cdot \left(0.4 + 0.6 \cdot \min\left(1.0, \frac{\text{FRP}}{200}\right)\right)$$

---

### 4. Official Indian CPCB Air Quality Index (AQI)

The sub-index $I_p$ for a pollutant concentration $C_p$ is calculated using the official CPCB piecewise linear interpolation:

$$I_p = I_{low} + \frac{I_{high} - I_{low}}{C_{high} - C_{low}} \times (C_p - C_{low})$$

Where $[C_{low}, C_{high}]$ is the concentration breakpoint bracket containing $C_p$, and $[I_{low}, I_{high}]$ is the corresponding AQI sub-index bracket.

$$\text{Overall AQI} = \max\left(I_{\text{PM2.5}}, I_{\text{PM10}}, I_{\text{O3}}, I_{\text{NO2}}, I_{\text{SO2}}, I_{\text{CO}}, I_{\text{NH3}}, I_{\text{Pb}}\right)$$

The dominant pollutant is the species yielding the maximum sub-index.

| Category | AQI Range | Color Hex | Health Impact Description |
| :--- | :---: | :---: | :--- |
| **Good** | 0 – 50 | `#009966` | Minimal impact |
| **Satisfactory** | 51 – 100 | `#55a84f` | Minor breathing discomfort to sensitive people |
| **Moderate** | 101 – 200 | `#a3c639` | Breathing discomfort to people with lungs, asthma, and heart diseases |
| **Poor** | 201 – 300 | `#fff833` | Breathing discomfort to most people on prolonged exposure |
| **Very Poor** | 301 – 400 | `#f29c33` | Respiratory illness on prolonged exposure |
| **Severe** | 401 – 500 | `#e93f33` | Affects healthy people and seriously impacts those with existing diseases |

---

### 5. Stage 2 Machine Learning Residual Correction Formulation

- **Residual Target Variable:**
  $$e_{pollutant}(t) = C_{observed}(t) - C_{physics}(t)$$

- **Combined Final Forecast:**
  $$C_{final}(t) = \max\left(0, \; C_{physics}(t) + \hat{e}(t)\right)$$

- **Model Evaluation Performance Metrics:**
  $$\text{Mean Absolute Error (MAE)} = \frac{1}{N} \sum_{i=1}^N \left| y_i - \hat{y}_i \right|$$
  $$\text{Root Mean Squared Error (RMSE)} = \sqrt{\frac{1}{N} \sum_{i=1}^N \left( y_i - \hat{y}_i \right)^2}$$
  $$\text{Coefficient of Determination } (R^2) = 1 - \frac{\sum_{i=1}^N \left(y_i - \hat{y}_i\right)^2}{\sum_{i=1}^N \left(y_i - \bar{y}\right)^2}$$

---

## 🧪 Steps to Train and Test the Model

### Step 1: Environment Setup & Activation
Ensure you are running within the project environment with all dependencies installed:

```bash
# Clone or navigate to the repository
cd "d:/Projects/air sync"

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Verify dependencies
pip install -r requirements.txt
```

---

### Step 2: Automated Testing Suite Execution
AirSync includes a test suite covering physics equations, CPCB breakpoints, episode state machine, API endpoints, and zero-leakage validation:

```bash
# Run the complete test suite with Pytest
python -m pytest

# Run with detailed verbose output
python -m pytest -v

# Run a specific unit test file (e.g. Physics & Units test)
python -m pytest tests/test_units_and_physics.py -v
```

---

### Step 3: Train the Stage 2 ML Residual Correction Model

You can train the ML residual correction model either via the command-line script or via the live REST API.

#### Option A: Offline CLI Training Script (Recommended)
AirSync provides a standalone training script `scripts/train_on_real_data.py`. It accepts historical paired datasets (ERA5 weather + CPCB ground observations) or automatically synthesizes Delhi-NCR winter stagnation scenarios:

```bash
# Train on synthetic Delhi-NCR scenario (default):
python scripts/train_on_real_data.py

# Train on custom historical paired CSV dataset:
python scripts/train_on_real_data.py --input-csv data/sample/training_paired_dataset.csv
```

**Training Process Details:**
1. Loads the historical paired dataset.
2. Chronologically splits data (70% Train, 15% Validation, 15% Test) without random shuffling to prevent time-series lookahead leakage.
3. Computes the residual target: $e(t) = C_{obs}(t) - C_{phys}(t)$ for PM2.5, PM10, and O3.
4. Trains gradient-boosted decision trees (`XGBoost` or `HistGradientBoosting`).
5. Evaluates model performance using MAE, RMSE, and $R^2$.
6. Saves model artifacts directly into the `models/` directory:
   - `models/model_pm25.pkl`
   - `models/model_pm10.pkl`
   - `models/model_o3.pkl`
   - `models/residual_metadata.pkl`

#### Option B: Train via REST API Endpoint
Launch the backend server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Trigger model training dynamically using `curl` or PowerShell:
```bash
# Trigger training via POST request
curl -X POST http://localhost:8000/model/train
```

---

### Step 4: Verify Model Status & Performance Metrics
Inspect the current model training status and validation scores:

```bash
# Query the model status endpoint
curl http://localhost:8000/model/status
```

Expected JSON response:
```json
{
  "residual_model": "trained",
  "validation_metrics": {
    "pm25": {"mae": 14.53, "rmse": 17.00, "r2": 0.74},
    "pm10": {"mae": 21.34, "rmse": 24.74, "r2": 0.71},
    "o3":   {"mae": 8.55,  "rmse": 10.25, "r2": 0.68}
  },
  "supported_pollutants": ["pm25", "pm10", "o3"],
  "no_data_leakage_enforced": true
}
```

---

### Step 5: Test 72-Hour Forecast & Episode Detection

Verify that the full 2-stage engine generates predictions:

```bash
# Run a 72-hour forecast scenario (Stagnant Winter)
curl -X POST http://localhost:8000/forecast/72h \
     -H "Content-Type: application/json" \
     -d '{"scenario_type": "stagnant_winter", "use_ml_residual": true}'
```

Alternatively, open your browser and navigate to:
- 🌐 **Interactive Dashboard:** [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/)
- 📖 **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)