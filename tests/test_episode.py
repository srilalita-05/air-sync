"""
Unit tests for data-driven pollution episode detection.
"""

from app.episode.detector import detect_pollution_episodes


def test_episode_onset_peak_recovery_timestamps():
    """Verifies data-driven detection of onset, peak, and recovery timestamps on sample AQI peak curve."""
    # Synthetic AQI curve: normal -> rising -> peak at h=3 -> recovery ->
    # normal
    timeline = [
        {"timestamp": "2026-11-15T00:00:00Z", "aqi": 120},
        {"timestamp": "2026-11-15T01:00:00Z", "aqi": 180},
        {"timestamp": "2026-11-15T02:00:00Z",
            "aqi": 250},  # Onset (crosses 201)
        {"timestamp": "2026-11-15T03:00:00Z", "aqi": 380},  # Peak
        {"timestamp": "2026-11-15T04:00:00Z", "aqi": 280},  # Recovery
        {"timestamp": "2026-11-15T05:00:00Z", "aqi": 160},  # Normal again
    ]

    ep = detect_pollution_episodes(timeline, threshold_aqi=201.0)

    assert ep["episode_detected"] is True
    assert ep["onset_timestamp"] == "2026-11-15T02:00:00Z"
    assert ep["peak_timestamp"] == "2026-11-15T03:00:00Z"
    assert ep["recovery_timestamp"] == "2026-11-15T05:00:00Z"
    assert ep["max_forecast_aqi"] == 380
    assert ep["duration_hours"] == 3
