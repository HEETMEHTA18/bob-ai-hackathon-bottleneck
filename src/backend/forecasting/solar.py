import numpy as np
import pandas as pd
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain


def run_physics_model(df: pd.DataFrame, site_params: dict) -> np.ndarray:
    location = Location(
        latitude=site_params["latitude"],
        longitude=site_params["longitude"],
        altitude=site_params.get("altitude", 0),
        tz="Asia/Kolkata",
    )
    system = PVSystem(
        surface_tilt=site_params.get("surface_tilt", site_params["latitude"]),
        surface_azimuth=site_params.get("surface_azimuth", 180),
        module_parameters={
            "pdc0": site_params["capacity_kw"] * 1000,
            "gamma_pdc": site_params.get("temp_coeff_pmax", -0.004),
        },
        inverter_parameters={"pdc0": site_params["capacity_kw"] * 1000},
        temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
            "sapm"]["open_rack_glass_glass"],
    )
    mc = ModelChain(
        system, location,
        dc_model="pvwatts", ac_model="pvwatts",
        aoi_model="physical", spectral_model="no_loss",
    )
    weather_df = df.set_index("timestamp")[["ghi", "dni", "dhi", "temp_air", "wind_speed"]].copy()
    weather_df.columns = ["ghi", "dni", "dhi", "temp_air", "wind_speed"]
    mc.run_model(weather_df)
    physics_watts = mc.results.ac.values
    return physics_watts / 1000.0


def persistence_baseline(generation: pd.Series, horizon_hours: int) -> pd.Series:
    return generation.shift(horizon_hours)


def get_solar_feature_cols() -> list:
    return [
        "ghi", "dni", "dhi", "temp_air", "wind_speed", "humidity", "cloud_cover_pct",
        "hour_sin", "hour_cos", "doy_sin", "doy_cos",
        "solar_elevation", "solar_azimuth", "clearsky_index",
        "lag_1h_generation", "lag_24h_generation",
        "rolling_mean_24h", "rolling_std_24h", "physics_estimate_kw",
    ]
