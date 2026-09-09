"""
AirSync Physics Units and Dimensional Documentation.

Centralized registry defining the exact physical units and dimensions for all inputs,
physics diagnostics, and output variables in the AirSync forecasting engine.
"""

UNITS = {
    # Pollutant Concentrations
    "pm25": "µg/m³",
    "pm10": "µg/m³",
    "o3": "µg/m³",
    "no2": "µg/m³",
    "so2": "µg/m³",
    "co": "mg/m³",

    # Meteorological Variables
    "temperature": "°C",
    "relative_humidity": "%",
    "pressure": "hPa",
    "wind_speed": "m/s",
    "wind_direction": "degrees (0-360, meteorological FROM direction)",
    "u_wind": "m/s (east-west component; positive eastwards)",
    "v_wind": "m/s (north-south component; positive northwards)",
    "precipitation_rate": "mm/h",
    "solar_radiation": "W/m²",
    "cloud_cover": "%",
    "pbl_height": "m (Planetary Boundary Layer height)",
    "vertical_temperature_gradient": "°C/100m or °C difference",

    # Physical Diagnostic Terms
    "ventilation_coefficient": "m²/s (wind_speed * pbl_height)",
    "characteristic_domain_length": "m (domain diameter / scale length)",
    "emission_flux_rate": "µg/(m²·s) (surface emission proxy)",
    "dry_deposition_velocity": "m/s",
    "wet_scavenging_rate": "s⁻¹ (Lambda = a * R^b)",
    "dispersion_timescale": "s (L / U)",
    "timestep": "s (standard forecast step = 3600 s)",

    # Fire & Plume Properties
    "fire_radiative_power": "MW (FIRMS FRP)",
    "downwind_distance": "m",
    "plume_dispersion_sigma": "m (Gaussian spread radius)",
    "potential_downwind_influence_score": "dimensionless index (0.0 to 1.0)",
}

DIMENSIONAL_CHECKLIST = {
    "mass_balance": "dC/dt [µg/(m³·s)] = E/H [µg/(m³·s)] - (U/L)*C [µg/(m³·s)] - (v_d/H)*C [µg/(m³·s)] - Lambda*C [µg/(m³·s)]",
    "ventilation_rate": "(U * H) / (L * H) = U / L [s⁻¹]",
    "wet_removal": "dC = C_0 * (1 - exp(-Lambda * dt)) [µg/m³]",
}
