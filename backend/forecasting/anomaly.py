"""
Anomaly Detection Module for GridMind AI
Methods: Z-score, IQR, Isolation Forest
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple


class AnomalyDetector:
    def __init__(self, window_size: int = 24):
        self.window_size = window_size

    def detect_zscore(self, series: pd.Series, threshold: float = 3.0) -> pd.Series:
        rolling_mean = series.rolling(window=self.window_size, center=True).mean()
        rolling_std = series.rolling(window=self.window_size, center=True).std()
        z_scores = np.abs((series - rolling_mean) / rolling_std.clip(lower=1e-6))
        return z_scores > threshold

    def detect_iqr(self, series: pd.Series, multiplier: float = 1.5) -> pd.Series:
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR
        return (series < lower) | (series > upper)

    def detect_gaps(self, timestamps: pd.Series, max_gap_hours: int = 2) -> pd.Series:
        if not pd.api.types.is_datetime64_any_dtype(timestamps):
            timestamps = pd.to_datetime(timestamps)
        time_diff = timestamps.diff().dt.total_seconds() / 3600
        return time_diff > max_gap_hours

    def detect_zero_output(self, generation: pd.Series, irradiance: pd.Series, threshold: float = 100) -> pd.Series:
        return (generation < 1) & (irradiance > threshold)

    def detect_negative(self, series: pd.Series) -> pd.Series:
        return series < 0

    def detect_sensor_drift(self, series: pd.Series, window: int = 48, threshold: float = 0.3) -> pd.Series:
        rolling_mean = series.rolling(window=window).mean()
        long_mean = series.expanding().mean()
        drift = np.abs((rolling_mean - long_mean) / long_mean.clip(lower=1e-6))
        return drift > threshold

    def detect_all(self, df: pd.DataFrame, generation_col: str = "generation_kw",
                   irradiance_col: str = "ghi") -> List[Dict]:
        anomalies = []

        if generation_col in df.columns:
            zscore_mask = self.detect_zscore(df[generation_col])
            for idx in df.index[zscore_mask]:
                anomalies.append({
                    "index": int(idx),
                    "type": "spike",
                    "severity": "high",
                    "metric": generation_col,
                    "value": float(df.loc[idx, generation_col]),
                    "description": f"Z-score anomaly detected",
                })

            iqr_mask = self.detect_iqr(df[generation_col])
            for idx in df.index[iqr_mask]:
                if idx not in [a["index"] for a in anomalies]:
                    anomalies.append({
                        "index": int(idx),
                        "type": "outlier",
                        "severity": "medium",
                        "metric": generation_col,
                        "value": float(df.loc[idx, generation_col]),
                        "description": "IQR-based outlier detected",
                    })

            neg_mask = self.detect_negative(df[generation_col])
            for idx in df.index[neg_mask]:
                anomalies.append({
                    "index": int(idx),
                    "type": "negative",
                    "severity": "high",
                    "metric": generation_col,
                    "value": float(df.loc[idx, generation_col]),
                    "description": "Negative generation value",
                })

        if "timestamp" in df.columns:
            gap_mask = self.detect_gaps(df["timestamp"])
            for idx in df.index[gap_mask]:
                anomalies.append({
                    "index": int(idx),
                    "type": "gap",
                    "severity": "low",
                    "metric": "timestamp",
                    "value": 0,
                    "description": "Data gap detected",
                })

        if generation_col in df.columns and irradiance_col in df.columns:
            zero_mask = self.detect_zero_output(df[generation_col], df[irradiance_col])
            for idx in df.index[zero_mask]:
                anomalies.append({
                    "index": int(idx),
                    "type": "zero_output",
                    "severity": "high",
                    "metric": generation_col,
                    "value": 0,
                    "description": "Zero output despite irradiance",
                })

        return sorted(anomalies, key=lambda x: x["severity"] == "high", reverse=True)

    def auto_fix(self, df: pd.DataFrame, anomalies: List[Dict], col: str) -> pd.DataFrame:
        df = df.copy()
        for a in anomalies:
            if a["type"] == "gap":
                idx = a["index"]
                if idx < len(df):
                    df.loc[idx, col] = df[col].interpolate().iloc[idx]
            elif a["type"] == "negative":
                idx = a["index"]
                if idx < len(df):
                    df.loc[idx, col] = max(0, df.loc[idx, col])
        return df


def get_anomaly_summary(anomalies: List[Dict]) -> Dict:
    return {
        "total": len(anomalies),
        "high": sum(1 for a in anomalies if a["severity"] == "high"),
        "medium": sum(1 for a in anomalies if a["severity"] == "medium"),
        "low": sum(1 for a in anomalies if a["severity"] == "low"),
        "types": list(set(a["type"] for a in anomalies)),
    }
