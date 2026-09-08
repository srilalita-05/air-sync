"""
Unit tests for kinematic fire plume trajectory module.
"""

from app.plume.trajectory import calculate_plume_trajectory


def test_nw_wind_advects_plume_southeast_towards_delhi():
    """Verifies that NW wind (315 deg) pushes fire plume SE towards Delhi coordinates."""
    # Fire in Punjab (30.5 N, 75.5 E), NW wind -> pushes SE towards Delhi (28.6 N, 77.2 E)
    res = calculate_plume_trajectory(
        fire_lat=30.5,
        fire_lon=75.5,
        wind_speed_ms=5.0,
        wind_direction_deg=315.0,
        target_lat=28.61,
        target_lon=77.20,
        horizon_hours=24
    )
    
    pts = res["trajectory_points"]
    # Check that parcel moves south (latitude decreases) and east (longitude increases)
    assert pts[-1]["latitude"] < pts[0]["latitude"]
    assert pts[-1]["longitude"] > pts[0]["longitude"]
    assert res["is_simplified_kinematic_proxy"] is True
