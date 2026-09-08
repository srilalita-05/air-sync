# AirSync Scientific Basis & Technical Documentation

**Problem Statement ID:** SIH26082  
**Project Name:** AirSync — Air Pollution–Weather Coupled Forecasting System (Delhi-NCR Focus)  
**Team:** Semantic Souls (Smart India Hackathon 2026)

> [!IMPORTANT]
> **Technical Defense & Anti-Hallucination Disclaimer**: AirSync explicitly avoids regional numerical weather prediction / 3D chemical transport models (such as WRF or WRF-Chem). It implements a transparent, lightweight, physics-informed 2-stage engine (**Physics Baseline + Machine Learning Residual Correction**). All equations, parameterizations, and data assumptions are explicitly documented below.

---

## 1. Established Physical Principles
AirSync incorporates foundational physical mechanisms governing boundary layer air quality:

1. **Mass Conservation (Single-Box Continuity Equation)**:
   $$\frac{dC}{dt} = \frac{E}{H} - \frac{U}{L}(C - C_{bg}) - \frac{v_d}{H}C - \Lambda(R)C + P_{chem}$$
   - Concentration units: $\mu g / m^3$
   - Volumetric source terms ($E/H$, $P_{chem}$): $\mu g / (m^3 \cdot s)$
   - First-order removal rates ($U/L$, $v_d/H$, $\Lambda(R)$): $s^{-1}$

2. **Ventilation Rate ($VC$)**:
   $$VC = U \times \text{PBLH} \quad [m^2/s]$$
   Directly measures the volumetric flushing rate of the planetary boundary layer per unit width.

3. **Precipitation Wet Scavenging**:
   $$\Lambda(R) = a R^b \quad [s^{-1}]$$
   Rainfall rate $R$ ($mm/h$) exponentially scavenges aerosols via aerosol-hydrometeor collisions ($C(t) = C_0 e^{-\Lambda(R) \Delta t}$).

4. **Kinematic Parcel Transport (Plume Motion)**:
   $$\Delta x = u \cdot \Delta t, \quad \Delta y = v \cdot \Delta t$$
   Zonal ($u$) and meridional ($v$) wind velocity advect fire hotspots downwind into receptive urban grids.

---

## 2. Simplified Physical Approximations
To maintain lightweight real-time execution without supercomputers, AirSync employs defensible approximations:

- **Single-Box Domain**: The entire Delhi urban core is parameterized as a characteristic box ($L = 50,000 m$). Spatial variation is handled via station point interpolation rather than 3D grid resolution.
- **Photochemical $O_3$ Proxy**: Ozone formation is modeled via a solar-radiation ($I$) and temperature ($T$) activity proxy, rather than a full 100+ reaction chemical mechanism (e.g., CB05).
- **2D Kinematic Plume Radius**: Biomass fire plume spread uses a 2D Gaussian horizontal spread radius $\sigma_r(t) = \sqrt{\sigma_0^2 + 2 K_y t}$ rather than a 3D Eulerian turbulent diffusion solver.

---

## 3. Empirical & Tunable Parameters (`app/physics/parameters.py`)
These values represent parameterized baseline defaults for the Delhi-NCR domain. They are **empirical parameters**, NOT invariant physical constants:

| Parameter | Symbol | Value | Unit | Description |
| :--- | :--- | :--- | :--- | :--- |
| Domain Length | $L$ | 50,000 | $m$ | Urban domain characteristic scale |
| Dry Deposition (PM2.5) | $v_d$ | 0.001 | $m/s$ | Fine aerosol surface deposition velocity |
| Dry Deposition (PM10) | $v_d$ | 0.005 | $m/s$ | Coarse aerosol surface deposition velocity |
| Rain Scavenging (PM2.5) | $a, b$ | $1.0\times 10^{-4}, 0.8$ | $s^{-1}$ | Rain rate washout coefficient |
| Good Ventilation Threshold | $VC_{good}$ | 5,000 | $m^2/s$ | Threshold for rapid atmospheric flushing |
| Poor Ventilation Threshold | $VC_{poor}$ | 1,500 | $m^2/s$ | Threshold for air stagnation & buildup |

---

## 4. Inversion vs Accumulation Potential (Requirement 2)
AirSync strictly enforces scientific boundary separation:

- **Poor Ventilation / Accumulation Potential**: Calculated continuously from surface wind speed, boundary layer height ($PBLH$), and $VC$.
- **Thermal Inversion Indicator (`inversion_detected`)**: Calculated **ONLY** when vertical atmospheric temperature profile data ($\frac{dT}{dz} > 0$ or $T_{upper} > T_{surface}$) is available. When vertical temperature data is absent, `inversion_detected = None` with status `"vertical_data_unavailable"`. Low PBL + low wind alone is **NEVER** falsely called a confirmed inversion.

---

## 5. Machine Learning Residual Correction & No-Data-Leakage Design
- **Target**: Systematic model error $e(t) = C_{observed}(t) - C_{physics}(t)$
- **Algorithm**: XGBoostRegressor / HistGradientBoostingRegressor
- **No-Data-Leakage Rule**: For any forecast initialized at origin time $T$, input features **ONLY** consume information available AT OR BEFORE time $T$. Future CPCB observations (past $T$) are strictly excluded.
- **Un-trained State**: If the ML model is not fitted, AirSync explicitly outputs `"residual_model": "not_trained"` and presents the unadjusted Physics Baseline rather than fabricating metrics.

---

## 6. Official Indian CPCB AQI Calculation (Requirement 7)
Isolated CPCB 8-pollutant sub-index calculator implementing official 2014 CPCB guidelines:
- **Sub-index Formula**:
  $$I_p = I_{low} + \frac{I_{high} - I_{low}}{C_{high} - C_{low}} (C_p - C_{low})$$
- **Breakpoints**: PM2.5 (24h), PM10 (24h), O3 (8h), NO2 (24h), SO2 (24h), CO (8h), NH3 (24h), Pb (24h).
- **Categories**: Good (0–50), Satisfactory (51–100), Moderate (101–200), Poor (201–300), Very Poor (301–400), Severe (401–500).

---

## 7. Known Limitations
1. **Vertical Atmospheric Data**: Operational radiosonde or vertical meteorology soundings are required to confirm thermal inversion layers.
2. **VOC/Precursor Emissions**: Secondary organic aerosol and ozone formation accuracy improves when high-resolution VOC emission inventories are connected.
3. **Complex Terrain Micro-climates**: Regional topography effects are parameterized into domain ventilation terms.
