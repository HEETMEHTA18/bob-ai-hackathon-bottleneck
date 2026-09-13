#!/usr/bin/env python3
"""
statistical_suite.py — deep statistical & numerical validation of deployed models.

Runs on the SAME 2024 real-weather OOS window as benchmark.py and examines the
deployed models (solar / wind / hybrid) from every angle:

  Point metrics    : MAE, RMSE, nMAE%, R2, MAPE, sMAPE, bias (ME), Pearson &
                     Spearman corr, Theil's U (vs no-change), P95/max error.
  Quantile model   : empirical coverage (P10-P90), quantile calibration
                     (% below P10/P50/P90), average pinball loss, Winkler
                     interval score, mean interval width.
  Numerical guard  : P10<=P50<=P90 monotonicity, bounds in [0,capacity],
                     no NaN/inf, deterministic (two runs identical).
  Residuals        : mean/std, lag-1 autocorrelation, D'Agostino normality,
                     heteroskedasticity (|err| vs driver), worst-error hours.
  Structure        : per-season MAE/R2, day/night split (solar).
  Baseline row     : same-window physics, persistence_1h/24h, climatology for
                     context (values deliberately NOT DM-tested here).

Honest framing: every metric is computed on the chronological OOS slice only;
no metrics are reported on training data.
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy import stats as sps

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.forecasting.inference import (
    predict_solar, predict_wind, predict_hybrid,
)
from backend.forecasting.solar import run_physics_model
from backend.forecasting.features import power_curve_estimate
from backend.forecasting.inference import _load_solar_calibration

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
MODELS_DIR = ROOT / "models"
CAPACITY = 100.0
LAT, LON = 27.5667, 72.0667
SITE = {"latitude": LAT, "longitude": LON, "altitude": 210,
        "capacity_kw": CAPACITY, "surface_tilt": 26, "surface_azimuth": 180}
TEST_FRAC = 0.3


# ---------------------------------------------------------------- helpers
def load(path):
    df = pd.read_csv(DATA_DIR / path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


def oos_split(df, frac=TEST_FRAC):
    split = int(len(df) * (1 - frac))
    return df.iloc[:split], df.iloc[split:]


def season_of(ts):
    m = ts.dt.month
    return m.map({3: "summer", 4: "summer", 5: "summer",
                  6: "monsoon", 7: "monsoon", 8: "monsoon", 9: "monsoon",
                  10: "post-monsoon", 11: "post-monsoon",
                  12: "winter", 1: "winter", 2: "winter"}).to_numpy()


def metrics(y, p, capacity=CAPACITY):
    p = np.clip(np.asarray(p, dtype=float), 0, capacity)
    y = np.asarray(y, dtype=float)
    e = y - p
    eps = 1e-9
    nz = np.abs(y) >= 1.0                      # MAPE only where actual >= 1% capacity
    mape = float(np.mean(np.abs(e[nz]) / np.maximum(np.abs(y[nz]), eps)) * 100) if nz.any() else 0.0
    smape = float(np.mean(np.abs(e) / (np.maximum(np.abs(y), 1e-9) + np.abs(p) + 1e-9)) * 200)
    r2 = float(1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2)) if np.var(y) > 0 else 0.0
    return {
        "MAE": float(np.mean(np.abs(e))),
        "RMSE": float(np.sqrt(np.mean(e ** 2))),
        "nMAE_%": float(np.mean(np.abs(e)) / capacity * 100),
        "R2": float(r2),
        "MAPE_%": float(mape),
        "sMAPE_%": float(smape),
        "bias_ME": float(np.mean(e)),
        "corr_pearson": float(np.corrcoef(y, p)[0, 1]) if len(y) > 2 else 0.0,
        "corr_spearman": float(sps.spearmanr(y, p).statistic) if len(y) > 2 else 0.0,
        "P95_abs_err": float(np.percentile(np.abs(e), 95)),
        "max_abs_err": float(np.max(np.abs(e))),
    }


def theil_u(y, p, y_prev):
    """U = RMSE(model)/RMSE(no-change persistence).  <1 => beats naive."""
    p, y, yp = np.asarray(p), np.asarray(y), np.asarray(y_prev)
    return float(np.sqrt(np.mean((y - p) ** 2)) /
                 (np.sqrt(np.mean((y - yp) ** 2)) + 1e-12))


def skill_score(y, p, clim):
    """1 - MSE(model)/MSE(climatology).  >0 => beats hour-of-day climatology."""
    mse_p = np.mean((np.asarray(y) - np.asarray(p)) ** 2)
    mse_c = np.mean((np.asarray(y) - np.asarray(clim)) ** 2)
    return float(1 - mse_p / (mse_c + 1e-12))


def quantile_verification(y, p10, p50, p90, capacity=CAPACITY):
    y = np.asarray(y, dtype=float)
    p10 = np.clip(np.asarray(p10, dtype=float), 0, capacity)
    p50 = np.clip(np.asarray(p50, dtype=float), 0, capacity)
    p90 = np.clip(np.asarray(p90, dtype=float), 0, capacity)
    inside80 = (y >= p10) & (y <= p90)
    pinball = {}
    for tau, q in ((0.1, p10), (0.5, p50), (0.9, p90)):
        d = y - q
        loss = np.where(d >= 0, tau * d, (tau - 1) * d)
        pinball[f"pinball_{tau}"] = float(np.mean(loss))
    # Winkler / interval score for the 80% (alpha=0.2) central interval
    alpha = 0.2
    L, U = p10, p90
    width = U - L
    pen = (2 / alpha) * np.where(y < L, L - y, np.where(y > U, y - U, 0.0))
    winkler = float(np.mean(width + pen))
    return {
        "coverage_80_empirical": float(np.mean(inside80)),
        "frac_below_p10": float(np.mean(y < p10)),
        "frac_below_p50": float(np.mean(y < p50)),
        "frac_below_p90": float(np.mean(y < p90)),
        "pinball_avg": float(np.mean(list(pinball.values()))),
        **pinball,
        "winkler_80": winkler,
        "mean_interval_width": float(np.mean(width)),
    }


def numerical_guard(p10, p50, p90, capacity=CAPACITY):
    p10 = np.asarray(p10, dtype=float)
    p50 = np.asarray(p50, dtype=float)
    p90 = np.asarray(p90, dtype=float)
    finite = bool(np.isfinite(p10).all() and np.isfinite(p50).all() and np.isfinite(p90).all())
    monotone = bool(np.all((p10 <= p50 + 1e-9) & (p50 <= p90 + 1e-9)))
    inbounds = bool(np.all((p10 >= -1e-9) & (p90 <= capacity + 1e-9)))
    return {
        "finite": finite,
        "monotone_p10<=p50<=p90": monotone,
        "in_bounds_0..cap": inbounds,
        "any_negative": bool(np.any(p10 < 0)),
        "any_over_cap": bool(np.any(p90 > capacity + 1e-9)),
        "n": int(len(p50)),
    }


def residual_diagnostics(y, p, driver, driver_name):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    e = y - p
    lag1 = float(np.corrcoef(e[:-1], e[1:])[0, 1]) if len(e) > 3 else 0.0
    norm_p = float(sps.normaltest(e).pvalue) if len(e) > 8 else 0.0
    skew = float(sps.skew(e))
    kurt = float(sps.kurtosis(e))
    het = float(np.corrcoef(np.abs(e), driver)[0, 1]) if len(e) > 3 else 0.0
    worst = np.argsort(np.abs(e))[-10:][::-1]
    return {
        "residual_mean": float(np.mean(e)),
        "residual_std": float(np.std(e)),
        "lag1_autocorr": lag1,
        "normality_p": norm_p,
        "skew": skew,
        "kurtosis": kurt,
        f"heterosk(|err| vs {driver_name})": het,
        "worst_hour_indices": [int(i) for i in worst],
        "worst_10_mae": float(np.mean(np.abs(e)[worst])),
    }


def season_breakdown(y, p, ts, capacity=CAPACITY):
    seas = season_of(ts)
    out = {}
    for s in np.unique(seas):
        m = seas == s
        out[str(s)] = metrics(y[m], p[m], capacity)
    return out


# ---------------------------------------------------------------- asset eval
def eval_asset(name, y, p10, p50, p90, y_prev, clim, ts):
    m = metrics(y, p50)
    q = quantile_verification(y, p10, p50, p90)
    ng = numerical_guard(p10, p50, p90)
    return {
        "window": f"{len(y)}h (last {int(TEST_FRAC*100)}% of 2024)",
        "point_metrics": m,
        "theil_U_vs_nochange": theil_u(y, p50, y_prev),
        "skill_score_vs_climatology": skill_score(y, p50, clim),
        "quantile_verification": q,
        "numerical_guard": ng,
    }


# ------------------------------------------------------------------ solar
def run_solar():
    df = load("solar_generation.csv")
    tr, te = oos_split(df)
    out = predict_solar(te.copy(), LAT, LON, CAPACITY)
    p10, p50, p90 = map(np.asarray, (out["p10"], out["p50"], out["p90"]))
    y = te["generation_kw"].values
    day = te["ghi"].values > 10.0

    phys_df = te.copy()
    phys_df["temp_air"] = phys_df["temp_air"]
    phys_df["wind_speed"] = phys_df["wind_speed"]
    bias = _load_solar_calibration().get("physics_bias_scale", 1.0)
    phys = np.clip(np.asarray(run_physics_model(phys_df, SITE)) * bias, 0, CAPACITY)

    h_tr = tr["timestamp"].dt.hour.values
    h_te = te["timestamp"].dt.hour.values
    clim = np.array([tr["generation_kw"].to_numpy()[h_tr == hh].mean() if (h_tr == hh).any() else 0.0
                     for hh in h_te])

    res = eval_asset("solar", y, p10, p50, p90,
                     y_prev=np.concatenate([[tr["generation_kw"].iloc[-1]], y[:-1]]), clim=clim,
                     ts=te["timestamp"])
    res["physics_only"] = metrics(y, phys)
    res["climatology"] = metrics(y, clim)
    day_m = metrics(y[day], p50[day])
    res["point_metrics_daytime_R2"] = round(day_m["R2"], 4)
    res["point_metrics_daytime_MAE"] = round(day_m["MAE"], 3)
    res["point_metrics_night_MAE"] = round(metrics(y[~day], p50[~day])["MAE"], 3)
    res["quantile_verification"] = quantile_verification(y[day], p10[day], p50[day], p90[day])
    res["season_breakdown"] = season_breakdown(y, p50, te["timestamp"])
    res["residual_diagnostics"] = residual_diagnostics(y, p50, te["ghi"].values, "ghi")
    res["deterministic"] = bool(
        np.allclose(np.asarray(predict_solar(te.copy(), LAT, LON, CAPACITY)["p50"]), p50))
    return res


# ------------------------------------------------------------------ wind
def run_wind():
    df = load("wind_generation.csv")
    tr, te = oos_split(df)
    out = predict_wind(te.copy(), hub_height=80, rated_capacity_kw=CAPACITY)
    p10, p50, p90 = map(np.asarray, (out["p10"], out["p50"], out["p90"]))
    y = te["generation_kw"].values

    ws = te["wind_speed"].values
    phys = np.clip(np.array([power_curve_estimate(v) for v in ws]), 0, CAPACITY)

    h_tr = tr["timestamp"].dt.hour.values
    h_te = te["timestamp"].dt.hour.values
    clim = np.array([tr["generation_kw"].to_numpy()[h_tr == hh].mean() if (h_tr == hh).any() else 0.0
                     for hh in h_te])

    res = eval_asset("wind", y, p10, p50, p90,
                     y_prev=np.concatenate([[tr["generation_kw"].iloc[-1]], y[:-1]]), clim=clim,
                     ts=te["timestamp"])
    res["physics_only"] = metrics(y, phys)
    res["climatology"] = metrics(y, clim)
    res["season_breakdown"] = season_breakdown(y, p50, te["timestamp"])
    res["residual_diagnostics"] = residual_diagnostics(y, p50, te["wind_speed"].values, "wind_speed")
    res["deterministic"] = bool(
        np.allclose(np.asarray(predict_wind(te.copy(), hub_height=80, rated_capacity_kw=CAPACITY)["p50"]), p50))
    return res


# ------------------------------------------------------------------ hybrid
def run_hybrid():
    """Co-located hybrid plant at Bhadla: 60 kW PV + 40 kW wind (share 0.6)."""
    df = load("solar_generation.csv")            # real weather incl. wind_speed
    tr, te = oos_split(df)

    # ground truth: 60 kW solar (scale of 100-kW physics truth) + 40 kW wind
    from backend.training.build_wind_dataset import generate_wind_ground_truth
    wind_truth = generate_wind_ground_truth(te.copy(), {"capacity_kw": 40.0})
    y_hybrid = te["generation_kw"].values * 0.6 + wind_truth["generation_kw"].values

    out = predict_hybrid(te.copy(), LAT, LON, capacity_kw=100, solar_share=0.6)
    p10, p50, p90 = map(np.asarray, (out["p10"], out["p50"], out["p90"]))

    # baselines: naive hybrid physics = 0.6*solar + 0.4*IEC-power
    phys_df = te.copy()
    phys_df["wind_speed"] = phys_df["wind_speed"]
    bias = _load_solar_calibration().get("physics_bias_scale", 1.0)
    w_phys = np.clip(np.array([power_curve_estimate(v, p_rated_kw=40.0) for v in te["wind_speed"].values]), 0, 40)
    s_phys = np.clip(np.asarray(run_physics_model(phys_df, SITE)) * bias * 0.6, 0, 60)
    phys_hybrid = np.clip(s_phys + w_phys, 0, CAPACITY)

    h_tr = tr["timestamp"].dt.hour.values
    h_te = te["timestamp"].dt.hour.values
    clim = np.array([(tr["generation_kw"].to_numpy() * 0.6)[h_tr == hh].mean() if (h_tr == hh).any() else 0.0
                     for hh in h_te])
    clim += np.full(len(te), wind_truth["generation_kw"].values.mean())

    res = eval_asset("hybrid", y_hybrid, p10, p50, p90,
                     y_prev=np.concatenate([[y_hybrid[0]], y_hybrid[:-1]]), clim=clim,
                     ts=te["timestamp"])
    res["physics_only"] = metrics(y_hybrid, phys_hybrid)
    res["climatology"] = metrics(y_hybrid, clim)
    res["season_breakdown"] = season_breakdown(y_hybrid, p50, te["timestamp"])
    res["residual_diagnostics"] = residual_diagnostics(y_hybrid, p50, te["ghi"].values, "ghi")
    res["deterministic"] = bool(np.allclose(
        np.asarray(predict_hybrid(te.copy(), LAT, LON, capacity_kw=100, solar_share=0.6)["p50"]), p50))
    res["construction_note"] = ("truth = 0.6*100kW-pvlib-solar + 40kW-IEC-wind at the "
                                "same Bhadla site; solar truth scaled linearly (deployed "
                                "physics is linear in capacity).")
    return res


# ------------------------------------------------------------------ main
def main():
    results = {"timestamp": datetime.now().isoformat(),
               "framework": "2024 real-weather OOS (last 30%), deployed models"}
    results["solar"] = run_solar()
    results["wind"] = run_wind()
    results["hybrid"] = run_hybrid()

    out = MODELS_DIR / "metrics" / "statistical_suite.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()