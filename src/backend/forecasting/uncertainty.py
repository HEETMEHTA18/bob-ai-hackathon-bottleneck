import numpy as np


def compute_quantile_bands(
    point_forecast: np.ndarray,
    residuals: np.ndarray,
) -> dict:
    p10_offset = np.percentile(residuals, 10)
    p90_offset = np.percentile(residuals, 90)
    p10 = point_forecast + p10_offset
    p50 = point_forecast
    p90 = point_forecast + p90_offset
    p10 = np.maximum(p10, 0)
    p50 = np.maximum(p50, 0)
    p90 = np.maximum(p90, 0)
    stacked = np.stack([p10, p50, p90], axis=1)
    stacked = np.sort(stacked, axis=1)
    return {
        "p10": stacked[:, 0],
        "p50": stacked[:, 1],
        "p90": stacked[:, 2],
    }


def validate_coverage(y_true: np.ndarray, p10: np.ndarray, p90: np.ndarray) -> float:
    coverage = np.mean((y_true >= p10) & (y_true <= p90))
    return float(coverage)
