"""
Unit tests for official CPCB Indian Air Quality Index (AQI) calculations.
"""

from app.aqi.calculator import calculate_indian_aqi, calculate_sub_index


def test_official_cpcb_pm25_breakpoints():
    """Verifies official CPCB PM2.5 breakpoint sub-indices according to 2014 guidelines."""
    assert calculate_sub_index(30.0, "pm25") == 50.0   # Good upper bound
    # Satisfactory upper bound
    assert calculate_sub_index(60.0, "pm25") == 100.0
    assert calculate_sub_index(90.0, "pm25") == 200.0  # Moderate upper bound
    assert calculate_sub_index(120.0, "pm25") == 300.0  # Poor upper bound
    assert calculate_sub_index(250.0, "pm25") == 400.0  # Very Poor upper bound
    assert calculate_sub_index(500.0, "pm25") == 500.0  # Severe upper bound


def test_overall_aqi_dominant_pollutant():
    """Verifies that overall AQI matches the highest sub-index dominant pollutant."""
    # PM2.5 = 120 (sub-index 300 Poor), PM10 = 100 (sub-index 100 Satisfactory)
    aqi_res = calculate_indian_aqi(pm25=120.0, pm10=100.0, o3=40.0)

    assert aqi_res["overall_aqi"] == 300
    assert "PM2.5" in aqi_res["dominant_pollutant"]
    assert aqi_res["aqi_category"] == "Poor"
