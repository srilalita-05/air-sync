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
│   ├── PROJECT_ANALYSIS_AND_WORKFLOW.md  # Comprehensive Workflow, Formulas & Tech Stack
│   ├── architecture.md                   # System Architecture & Component Interactions
│   └── scientific_basis.md               # Physics Principles & Dimensional Details
├── .env.example                # API Key Configuration Template
├── .gitignore                  # Git Ignore Rules
└── requirements.txt            # Python Dependencies
```

---

## 👥 Team & License
Built for **Smart India Hackathon 2026** by **Team Semantic Souls**.  
Licensed under the MIT License.