import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, capacity_kw: float) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    nmae_pct = (mae / capacity_kw) * 100 if capacity_kw > 0 else 0.0
    r2 = r2_score(y_true, y_pred)
    mask = y_true > 0.05 * capacity_kw
    if mask.any():
        mape_pct = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    else:
        mape_pct = None
    forecast_reliability = 100 * (1 - nmae_pct / 100)
    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "nMAE_%": float(nmae_pct),
        "R2": float(r2),
        "MAPE_%": float(mape_pct) if mape_pct is not None else None,
        "Forecast_Reliability_Score": float(forecast_reliability),
    }


def walk_forward_split(df: pd.DataFrame, n_splits: int = 5, test_size: int = 168):
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)
    for train_idx, test_idx in tscv.split(df):
        yield train_idx, test_idx
