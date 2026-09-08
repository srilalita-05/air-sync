"""
CPCB Official Indian Air Quality Index (AQI) Breakpoint Configuration.

Reference:
    Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change,
    Government of India (2014). "National Air Quality Index - Final Report".
    Table 1: Breakpoint concentrations for different pollutants.
"""

from typing import Dict, List, Tuple

# Each entry is a list of tuples: (Conc_Low, Conc_High, AQI_Low, AQI_High, Averaging_Period)
CPCB_BREAKPOINTS: Dict[str, Dict[str, Any]] = {
    "pm25": {
        "pollutant_name": "PM2.5",
        "unit": "µg/m³",
        "averaging_period": "24-hour",
        "ranges": [
            (0.0, 30.0, 0, 50),
            (31.0, 60.0, 51, 100),
            (61.0, 90.0, 101, 200),
            (91.0, 120.0, 201, 300),
            (121.0, 250.0, 301, 400),
            (251.0, 500.0, 401, 500),
        ],
    },
    "pm10": {
        "pollutant_name": "PM10",
        "unit": "µg/m³",
        "averaging_period": "24-hour",
        "ranges": [
            (0.0, 50.0, 0, 50),
            (51.0, 100.0, 51, 100),
            (101.0, 250.0, 101, 200),
            (251.0, 350.0, 201, 300),
            (351.0, 430.0, 301, 400),
            (431.0, 600.0, 401, 500),
        ],
    },
    "o3": {
        "pollutant_name": "Ozone (O3)",
        "unit": "µg/m³",
        "averaging_period": "8-hour",
        "ranges": [
            (0.0, 50.0, 0, 50),
            (51.0, 100.0, 51, 100),
            (101.0, 168.0, 101, 200),
            (169.0, 208.0, 201, 300),
            (209.0, 748.0, 301, 400),
            (749.0, 1000.0, 401, 500),
        ],
    },
    "no2": {
        "pollutant_name": "Nitrogen Dioxide (NO2)",
        "unit": "µg/m³",
        "averaging_period": "24-hour",
        "ranges": [
            (0.0, 40.0, 0, 50),
            (41.0, 80.0, 51, 100),
            (81.0, 180.0, 101, 200),
            (181.0, 280.0, 201, 300),
            (281.0, 400.0, 301, 400),
            (401.0, 500.0, 401, 500),
        ],
    },
    "so2": {
        "pollutant_name": "Sulphur Dioxide (SO2)",
        "unit": "µg/m³",
        "averaging_period": "24-hour",
        "ranges": [
            (0.0, 40.0, 0, 50),
            (41.0, 80.0, 51, 100),
            (81.0, 380.0, 101, 200),
            (381.0, 800.0, 201, 300),
            (801.0, 1600.0, 301, 400),
            (1601.0, 2000.0, 401, 500),
        ],
    },
    "co": {
        "pollutant_name": "Carbon Monoxide (CO)",
        "unit": "mg/m³",
        "averaging_period": "8-hour",
        "ranges": [
            (0.0, 1.0, 0, 50),
            (1.1, 2.0, 51, 100),
            (2.1, 10.0, 101, 200),
            (10.1, 17.0, 201, 300),
            (17.1, 34.0, 301, 400),
            (34.1, 50.0, 401, 500),
        ],
    },
    "nh3": {
        "pollutant_name": "Ammonia (NH3)",
        "unit": "µg/m³",
        "averaging_period": "24-hour",
        "ranges": [
            (0.0, 200.0, 0, 50),
            (201.0, 400.0, 51, 100),
            (401.0, 800.0, 101, 200),
            (801.0, 1200.0, 201, 300),
            (1201.0, 1800.0, 301, 400),
            (1801.0, 2400.0, 401, 500),
        ],
    },
    "pb": {
        "pollutant_name": "Lead (Pb)",
        "unit": "µg/m³",
        "averaging_period": "24-hour",
        "ranges": [
            (0.0, 0.5, 0, 50),
            (0.6, 1.0, 51, 100),
            (1.1, 2.0, 101, 200),
            (2.1, 3.0, 201, 300),
            (3.1, 3.5, 301, 400),
            (3.6, 5.0, 401, 500),
        ],
    },
}

CPCB_CATEGORIES: List[Tuple[int, int, str, str]] = [
    (0, 50, "Good", "#009966"),
    (51, 100, "Satisfactory", "#55a846"),
    (101, 200, "Moderate", "#ffde33"),
    (201, 300, "Poor", "#ff9933"),
    (301, 400, "Very Poor", "#cc0033"),
    (401, 5000, "Severe", "#660099"),
]
