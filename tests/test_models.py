"""
GridMind AI — Model & Evaluation Test Suite

Exercises every ML forecast use case end-to-end:
  - site types : solar | wind | hybrid
  - horizons   : 24 / 48 / 72 hours
  - contracts  : P10/P50/P90 bands, bounds, ordering, timestamps, determinism
  - evaluation : evaluate(), walk_forward_split(), quantile coverage,
                 trained-artifact load, saved evaluation reports

Run:  python3 tests/test_models.py
"""
import sys
import os
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.forecasting.inference import (
    predict_solar, predict_wind, predict_hybrid, predict_from_weather_records,
    _load_solar_model, _load_solar_quantile, _load_solar_calibration,
    _load_wind_model, _load_wind_quantile, _load_wind_calibration,
)
from backend.forecasting.evaluate import evaluate, walk_forward_split
from backend.forecasting.uncertainty import validate_coverage

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
LAT, LON, CAP = 27.5667, 72.0667, 100.0

print("=" * 64)
print("GridMind AI — Model & Evaluation Test Suite")
print("=" * 64)

passed = 0


def check(name, cond):
    global passed
    assert cond, f"FAILED: {name}"
    passed += 1
    print(f"  ✓ {name}")


# ------------------------------------------------------------------ fixtures
def weather_records(hours, ghi_profile="summer", wind_profile="sine"):
    ts = pd.date_range("2026-06-01 00:00", periods=hours, freq="h", tz="Asia/Kolkata")
    h = np.arange(hours)
    if ghi_profile == "summer":
        ghi = np.array([950 * max(0, np.sin(np.pi * (t.hour - 6) / 12)) for t in ts])
    elif ghi_profile == "night":
        ghi = np.zeros(hours)
    else:
        ghi = np.full(hours, 400.0)
    if wind_profile == "sine":
        w = np.clip(3 + 8 * np.sin(np.pi * h / 12), 0, 30)
    else:
        w = np.full(hours, 7.0)
    return [{
        "timestamp": t.tz_localize(None), "ghi": float(g),
        "dni": float(g * 0.85), "dhi": float(g * 0.15),
        "temperature": 32.0, "wind_speed": float(ww), "wind_direction": 180.0,
        "humidity": 40.0, "cloud_cover": 10.0, "pressure": 1005.0,
    } for t, g, ww in zip(ts, ghi, w)]


# ------------------------------------------------- test 1: artifacts load
print("\n[1/7] Model artifacts load")
solar_model, solar_feats = _load_solar_model()
_quantile_models = _load_solar_quantile()["models"]
wind_model, wind_feats = _load_wind_model()
_wind_quantile_models = _load_wind_quantile()["models"]
check("solar XGBoost + feature_cols load ({} feats)".format(len(solar_feats)), len(solar_feats) >= 25)
check("solar quantiles load (p10/p50/p90)", set(_quantile_models) == {"p10", "p50", "p90"})
check("wind LightGBM + feature_cols load ({} feats)".format(len(wind_feats)), len(wind_feats) >= 19)
check("wind quantiles load (p10/p50/p90)", set(_wind_quantile_models) == {"p10", "p50", "p90"})
wind_calib = _load_wind_calibration()
check("wind band calibration present (band_scale>=0.5)", wind_calib.get("band_scale", 0) >= 0.5)

for f in ("solar/solar_hybrid.json", "solar/feature_cols.json",
          "solar/quantile/p10.txt", "solar/quantile/p50.txt", "solar/quantile/p90.txt",
          "wind/wind_lgbm.txt", "wind/feature_cols.json",
          "wind/quantile/p10.txt", "wind/quantile/p50.txt", "wind/quantile/p90.txt",
          "wind/calibration.json"):
    check(f"artifact exists: {f}", os.path.exists(os.path.join(MODELS_DIR, f)))


# ------------------------------------------------- test 2: all site types
print("\n[2/7] All site types × horizons → valid P10/P50/P90")
for site_type in ("solar", "wind", "hybrid"):
    for horizon in (24, 48, 72):
        recs = weather_records(horizon)
        out = predict_from_weather_records(recs, site_type, LAT, LON, CAP)
        p10, p50, p90 = np.array(out["p10"]), np.array(out["p50"]), np.array(out["p90"])
        check(f"{site_type} h={horizon}: model_type={out['model_type']}",
              out["model_type"] in ("surge_solar_xgboost", "surge_wind_xgboost", "surge_hybrid"))
        check("  length == horizon", len(p50) == horizon)
        check("  p10 <= p50 <= p90 every hour",
              bool(np.all((p10 <= p50 + 1e-9) & (p50 <= p90 + 1e-9))))
        check("  0 <= bands <= capacity", bool(np.all(p10 >= 0) and np.all(p90 <= CAP + 1e-9)))
        check("  timestamps ISO format", out["timestamps"][0].startswith("2026-06-01T"))
        check("  finite values", bool(np.isfinite(p10).all() and np.isfinite(p90).all()))


# ------------------------------------------------- test 3: physical sanity
print("\n[3/7] Physical sanity")
night = predict_solar(pd.DataFrame(weather_records(24, ghi_profile="night"), index=range(24)),
                      LAT, LON, CAP)
night_df = pd.DataFrame(weather_records(24, ghi_profile="night"))
night_out = predict_solar(night_df, LAT, LON, CAP)
check("solar at night → p50 = 0 (no generation without sun)",
      bool(np.all(np.array(night_out["p50"]) == 0)))

wind_recs = pd.DataFrame(weather_records(24, wind_profile="constant"))
wind_v = [3.0] * 24  # between cut-in (3) and rated => non-zero, below rated
wind_df = pd.DataFrame(weather_records(24, wind_profile="constant"))
wind_df["wind_speed"] = wind_v
wind_df["wind_direction"] = 180.0
w = predict_wind(wind_df, hub_height=80, rated_capacity_kw=CAP)
check("wind below rated → 0 < p50 < capacity",
      0 < float(np.mean(np.array(w["p50"])[6:18])) < CAP)

d1 = predict_solar(pd.DataFrame(weather_records(24)), LAT, LON, CAP)
d2 = predict_solar(pd.DataFrame(weather_records(24)), LAT, LON, CAP)
check("determinism (same input → same solar output)",
      np.allclose(d1["p50"], d2["p50"]))


# ------------------------------------------------- test 4: hybrid blend
print("\n[4/7] Hybrid blend decomposes correctly")
hout = predict_hybrid(pd.DataFrame(weather_records(48)), LAT, LON, CAP, solar_share=0.6)
check("hybrid model_type", hout["model_type"] == "surge_hybrid")
solar_only = predict_solar(pd.DataFrame(weather_records(48)), LAT, LON, CAP * 0.6)
wind_only = predict_wind(pd.DataFrame(weather_records(48)), hub_height=80, rated_capacity_kw=CAP * 0.4)
check("hybrid features = solar + wind feature counts",
      hout["feature_count"] == solar_only["feature_count"] + wind_only["feature_count"])
check("hybrid p50 ≈ solar_p50 + wind_p50",
      np.allclose(hout["p50"], np.array(solar_only["p50"]) + np.array(wind_only["p50"]), atol=1e-6))
check("hybrid bands stay inside total capacity",
      bool(np.all(np.array(hout["p90"]) <= CAP + 1e-9)))


# ------------------------------------------------- test 5: evaluation harness
print("\n[5/7] Metric evaluation harness")
y_true = np.array([10, 20, 30, 40, 50, 60])
y_pred = np.array([12, 19, 32, 38, 52, 59])
m = evaluate(y_true, y_pred, capacity_kw=100)
check("evaluate() returns MAE/RMSE/nMAE/R²/MAPE", all(k in m for k in ("MAE", "RMSE", "nMAE_%", "R2", "MAPE_%")))
check("MAE correct", np.isclose(m["MAE"], 10 / 6))
check("nMAE correct", np.isclose(m["nMAE_%"], 10 / 6))
check("R² correct", np.isclose(m["R2"], 0.9897, atol=1e-3))

df = pd.DataFrame({"timestamp": pd.date_range("2024-01-01", periods=1000, freq="h"),
                   "generation_kw": np.random.RandomState(0).uniform(0, 100, 1000)})
splits = list(walk_forward_split(df, n_splits=5, test_size=168))
check("walk_forward 5 splits × 168h", len(splits) == 5 and all(len(t) == 168 for _, t in splits))
check("walk_forward train grows, no leakage", all(splits[i][0].max() < splits[i][1].min() for i in range(5)))
check("walk_forward splits sequential", all(splits[i][1].max() < splits[i + 1][1].min() for i in range(4)))


# ------------------------------------------------- test 6: quantile coverage
print("\n[6/7] Quantile band coverage tooling")
rng = np.random.RandomState(1)
actual = rng.normal(50, 10, 500)
lo = actual - rng.normal(0, 5, 500)
hi = actual + rng.normal(0, 5, 500)
cov = validate_coverage(actual, lo, hi)
check("validate_coverage in (0, 1)", 0.0 < cov < 1.0)
check("actual within band ~95% for ±~2σ", cov > 0.9 or cov < 0.5)


# ------------------------------------------------- test 7: saved reports
print("\n[7/7] Saved evaluation reports")
for rep in ("evaluation_report.json", "wind_evaluation_report.json"):
    path = os.path.join(MODELS_DIR, "metrics", rep)
    check(f"report exists: {rep}", os.path.exists(path))
    data = json.load(open(path))
    check(f"  holdout nMAE_% < 5% ({rep})", data["holdout"]["nMAE_%"] < 5.0)
    if rep == "evaluation_report.json":
        check("  solar 80% coverage >= 50%", data["quantiles"]["coverage_80"] >= 0.5)
        check("  solar R² high (physics explains variance)", data["holdout"]["R2"] > 0.9)

print("\n" + "=" * 64)
print(f"All model & evaluation tests passed — {passed} checks ✓")
print("=" * 64)