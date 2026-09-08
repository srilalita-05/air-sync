# AirSync Implementation Plan - SIH 2026 (Problem ID: SIH26082)

## Project Overview
**AirSync** is a web-based, physics-informed air pollution–weather coupled forecasting and decision-support platform tailored for the **Delhi-NCR** region. Built for **Smart India Hackathon 2026 (Team: Semantic Souls)**, AirSync directly answers four key operational questions:
1. **WHAT?**: Accurate 72-hour hourly forecasts for major pollutants (PM2.5, PM10, O3, NO2, SO2, CO) & Indian AQI.
2. **WHY?**: Physics-based explainability attributing pollution trends to meteorological drivers (ventilation coefficient, PBL height, wind stagnation, temperature inversion, precipitation scavenging, biomass burning).
3. **WHERE?**: Kinematic parcel advection and plume trajectory modeling tracing biomass burning transport downwind into Delhi-NCR across spatial grids.
4. **WHEN?**: Automated episode detection characterizing severe episode onset, rising phase, peak window, and recovery timing.

> [!IMPORTANT]
> **Technical Constraint**: AirSync explicitly avoids heavy numerical weather prediction / regional chemistry models like WRF/WRF-Chem. Instead, it employs a lightweight, transparent, physics-informed 2-stage engine: **Physics Baseline + Machine Learning Residual Correction (XGBoost/GradientBoosting)**.

---

## User Review Required

> [!NOTE]
> **Data & Verification Strategy**:
> - We will create realistic synthetic sample datasets representing Delhi-NCR stations (Anand Vihar, RK Puram, Punjabi Bagh, ITO, Noida, Gurugram) and NASA FIRMS fire hotspots for immediate offline execution, testing, and UI demonstration.
> - Data ingestion interfaces are designed as clean adapters (CPCB CAAQMS, NOAA/IMD GFS weather forecasts, NASA FIRMS fire CSVs) so live operational data can be swapped seamlessly via environment variables or configuration files.

---

## Proposed System Architecture & File Structure

```
d:\Projects\air sync\
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application initialization & routes
│   │   ├── config.py                  # Environment config & constants
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py              # REST API endpoint implementations
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── payload.py             # Pydantic schemas for requests/responses
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── validator.py           # Ingestion validator & missing data handler
│   │   │   ├── synthetic.py           # Delhi-NCR synthetic dataset generator
│   │   │   └── gridding.py            # Spatial grid interpolation (IDW/Bilinear)
│   │   ├── physics/
│   │   │   ├── __init__.py
│   │   │   ├── box_model.py           # Mass-balance ventilation & dispersion engine
│   │   │   ├── advection.py           # 2D horizontal transport engine
│   │   │   ├── scavenging.py          # Wet deposition / rain scavenging engine
│   │   │   ├── chemistry.py           # Solar/temp photochemical proxy for O3
│   │   │   └── boundary_layer.py      # PBL height & stability/inversion index
│   │   ├── forecasting/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py              # Two-stage forecast coordinator
│   │   │   └── ml_residual.py         # XGBoost/GradientBoosting residual model
│   │   ├── explainability/
│   │   │   ├── __init__.py
│   │   │   └── engine.py              # Driver attribution & explanation engine
│   │   ├── plume/
│   │   │   ├── __init__.py
│   │   │   └── trajectory.py          # Kinematic parcel advection & Gaussian plume
│   │   ├── episode/
│   │   │   ├── __init__.py
│   │   │   └── detector.py            # Onset, peak, recovery episode state machine
│   │   └── aqi/
│   │       ├── __init__.py
│   │       └── calculator.py          # CPCB Indian AQI sub-index calculator
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_physics.py            # Physics sanity checks & conservation tests
│   │   ├── test_aqi.py                # CPCB AQI breakpoint tests
│   │   ├── test_plume.py              # Trajectory advection tests
│   │   ├── test_episode.py            # Episode state transition tests
│   │   └── test_api.py                # FastAPI endpoint integration tests
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── index.html                     # Main Web Dashboard structure
│   ├── css/
│   │   └── style.css                  # Modern Glassmorphic Dark UI design system
│   └── js/
│       ├── app.js                     # Dashboard interaction logic & state
│       ├── chart_config.js            # Chart.js 72h forecast & driver charts
│       └── map_config.js              # Leaflet.js Delhi-NCR spatial map & plume overlay
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/                        # Sample CSV files (weather, CPCB, FIRMS)
├── models/                            # Saved trained residual model artifacts (.pkl/.json)
├── docs/
│   ├── architecture.md
│   └── scientific_basis.md            # Documented physical equations & assumptions
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Detailed Component Specifications

### 1. Physics-Informed Engine (`backend/app/physics/`)
- **Ventilation & Dispersion Box Model**:
  $$VC = U \times \text{PBLH}$$
  $$\frac{dC}{dt} = \frac{E}{PBLH} - \frac{VC}{L_{box}} (C - C_{bg}) - k_{dep} C - \Lambda(R) C + P_{chem}$$
  where $U$ is wind speed ($m/s$), $PBLH$ is boundary layer height ($m$), $E$ is surface emission rate proxy ($g/m^2/s$), $L_{box}$ is characteristic domain scale, $k_{dep}$ is dry deposition rate, $\Lambda(R)$ is wet scavenging rate.
- **Inversion & Atmospheric Stability**:
  Defines Inversion Index based on thermal gradient $\frac{dT}{dz}$ or lower PBLH ($< 250m$) combined with low wind ($< 1.5 m/s$), scaling accumulation potential exponentially.
- **Wet Scavenging Engine**:
  $$\Lambda(R) = a R^b \implies C(t) = C_0 e^{-\Lambda(R) \Delta t}$$
  where $R$ is rainfall intensity ($mm/h$), parameterized for particulate matter and soluble gases.
- **Photochemical $O_3$ Proxy**:
  $O_3$ secondary formation scaled by solar radiation $I$ ($W/m^2$) and surface temperature $T$ ($^\circ C$).

### 2. Machine Learning Residual Engine (`backend/app/forecasting/ml_residual.py`)
- Fits $e(t) = C_{observed}(t) - C_{physics}(t)$.
- Models: `XGBoostRegressor` / `HistGradientBoostingRegressor` with fallback to `GradientBoostingRegressor`.
- Features: Lagged pollutant values ($t-1, t-24$), rolling statistics, wind components ($u, v$), temperature, RH, PBLH, ventilation coefficient, month/hour/day-of-week sinusoidal encodings, upwind fire density index.
- Strict time-series split (Train/Val/Test) without lookahead leakage.

### 3. CPCB Indian AQI Engine (`backend/app/aqi/calculator.py`)
- Implements official CPCB 8-pollutant sub-index breakpoints for PM2.5, PM10, O3, NO2, SO2, CO, NH3, Pb.
- Formula:
  $$I_p = I_{low} + \frac{I_{high} - I_{low}}{C_{high} - C_{low}} (C_p - C_{low})$$
- Returns: Sub-indices for all pollutants, overall AQI ($max(I_p)$), dominant pollutant, and official color-coded categories (Good [0-50], Satisfactory [51-100], Moderate [101-200], Poor [201-300], Very Poor [301-400], Severe [401-500]).

### 4. Biomass Burning Plume Engine (`backend/app/plume/trajectory.py`)
- Kinematic advection from NASA FIRMS hotspots ($lat_{fire}, lon_{fire}, FRP$).
- Calculates wind displacement vectors:
  $$\Delta x = u \cdot \Delta t, \quad \Delta y = v \cdot \Delta t$$
- Gaussian dispersion ellipse radius: $\sigma_r(t) = \sigma_0 + \gamma \cdot \sqrt{t}$.
- Computes downwind trajectory points over 24h horizon and spatial overlap score with Delhi-NCR station coordinates.

### 5. Explainability & Episode Detection (`backend/app/explainability/`, `backend/app/episode/`)
- **Driver Explainer**: Evaluates physics terms (e.g. low ventilation index $< 500 m^2/s$, low PBL $< 300m$, strong upwind biomass fire count $> 5$, zero rain vs heavy rain $> 5mm/h$) and generates human-readable attribution rank.
- **Episode Detector**: Scans 72-hour predicted AQI timeseries for threshold crossings (e.g. AQI $> 300$ for Poor/Severe episode):
  - `onset`: first hour crossing threshold.
  - `rising`: positive gradient leading to peak.
  - `peak`: hour of maximum AQI value.
  - `recovery`: negative gradient dropping towards normal.
  - `normal`: baseline levels.

### 6. REST API Endpoints (`backend/app/api/routes.py`)
- `GET /health` -> Server status & loaded model metadata.
- `POST /forecast` -> Single timestep forecast.
- `POST /forecast/72h` -> 72-hour forecast sequence with physics indicators, drivers, AQI, and episode status.
- `POST /explain` -> Detailed driver explanation breakdown for a given weather & pollution state.
- `POST /episode` -> Episode detection timeline analysis for a timeseries.
- `POST /plume` -> Biomass burning fire plume advection trajectory.
- `POST /aqi` -> Standalone CPCB Indian AQI sub-index calculator.
- `POST /data/validate` -> Input validation & missing value imputation report.
- `POST /model/train` -> Retrain ML residual model on new observation/weather paired data.
- `GET /model/status` -> Check ML model metrics (MAE, RMSE, $R^2$).

### 7. Web Dashboard (`frontend/`)
- Built with HTML5, CSS3 (Glassmorphism, custom design system, zero default styling), Vanilla JavaScript, Leaflet.js, and Chart.js.
- Visual Features:
  - Live 72-Hour AQI & Pollutant Forecast Chart with range selectors.
  - Delhi-NCR Interactive Spatial Map with CPCB stations and dynamic heatmap layer.
  - "Why is pollution changing?" Physics Explainer Breakdown cards with impact metrics.
  - "When will it peak?" Severe Episode Detection Banner (Onset, Peak, Recovery times).
  - NASA FIRMS Biomass Burning Plume Trajectory simulator on spatial map.
  - Standalone AQI Calculator tool.

---

## Verification Plan

### Automated Test Suite (`pytest backend/tests`)
1. **`test_physics.py`**:
   - Verify higher wind speed increases ventilation coefficient and reduces PM2.5 in box model.
   - Verify lower PBL height increases pollutant concentration accumulation.
   - Verify rainfall reduces pollutant concentration via wet scavenging.
2. **`test_aqi.py`**:
   - Test official CPCB breakpoints (e.g., PM2.5 = 60 $\rightarrow$ sub-index 100, PM2.5 = 250 $\rightarrow$ sub-index 400).
   - Test dominant pollutant identification.
3. **`test_plume.py`**:
   - Verify wind direction advects plume towards expected quadrant (e.g., NW wind pushes plume SE towards Delhi).
4. **`test_episode.py`**:
   - Verify correct detection of onset, peak, recovery timestamps on sample AQI peak profile.
5. **`test_api.py`**:
   - Verify status 200 and schema validity for `/health`, `/forecast/72h`, `/explain`, `/episode`, `/plume`, `/aqi`, `/data/validate`.

### Manual & System Verification
1. Run backend server via Uvicorn (`python -m uvicorn backend.app.main:app --port 8000`).
2. Test all API endpoints with `curl` or automated python scripts.
3. Launch frontend dashboard and verify real-time data fetching, chart rendering, map visualization, and responsive controls.
