import numpy as np
import pandas as pd


def get_wind_feature_cols() -> list:
    return [
        "wind_speed_10m", "wind_speed_hub", "wind_direction_deg",
        "wind_dir_sin", "wind_dir_cos",
        "air_temp", "pressure", "air_density",
        "hour_sin", "hour_cos", "month_sin", "month_cos",
        "lag_1h_generation", "lag_24h_generation",
        "rolling_mean_6h", "turbine_rated_capacity_kw",
        "power_curve_estimate", "wind_speed_std_3h",
    ]


def persistence_baseline_wind(generation: pd.Series, horizon_hours: int) -> pd.Series:
    return generation.shift(horizon_hours)
