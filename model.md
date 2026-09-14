# MODEL.md
## GridMind AI — Model Development Specification
### Forecast Engine: Architecture, Parameters, Training Protocol & Resources

**Scope:** This document is the single source of truth for model development. It covers the solar hybrid model, the wind ML model, the uncertainty layer, feature schemas, hyperparameter grids, evaluation protocol, and every external resource (datasets, libraries, docs) needed to build it. Aligned with `TRD.md` §5 and `work1.md` Phases 2–4.

---

## 0. Model Inventory

| ID | Name | Target | Type | Priority |
|----|------|--------|------|----------|
| M0-S | Persistence (Solar) | Baseline floor | Naive lag | Must-have |
| M0-W | Persistence (Wind) | Baseline floor | Naive lag | Must-have |
| M1-S | pvlib Physics Model | Solar power (clear-sky + actual) | Physics | Must-have |
| M2-S | XGBoost Residual Corrector | Solar residual (actual − physics) | Gradient boosting | Must-have |
| M3-S | Hybrid Solar Forecast | Solar power, final | M1-S + M2-S | Must-have |
| M1-W | LightGBM Wind Model | Wind power | Gradient boosting | Must-have |
| M2-W | XGBoost Wind Model (alt) | Wind power | Gradient boosting | Should-have (A/B) |
| M4 | Quantile Models (P10/P50/P90) | Uncertainty band | Quantile GBM | Should-have |
| M5 | WindFM (pretrained) | Wind power, zero-shot | Foundation model, inference-only | Nice-to-have |

**Non-negotiable rule:** No model ships without being compared against its persistence baseline (M0) on the same test window. A model that doesn't beat persistence at a given horizon is not reported as "the" forecast for that horizon.

---

## 1. Solar Model — M3-S (Hybrid Physics + ML)

### 1.1 Pipeline

```
GHI, DNI, DHI, temp_air, wind_speed  (Open-Meteo forecast)
                │
                ▼
        pvlib ModelChain  ──────────────►  physics_estimate (kW)
                │
                ▼
   actual_generation − physics_estimate  =  residual (training only)
                │
                ▼
   XGBoost Regressor(features)  ──────►  residual_correction (kW)
                │
                ▼
   final_forecast = physics_estimate + residual_correction
```

### 1.2 M1-S — pvlib Physics Baseline

**Library:** `pvlib-python`
**Core object:** `pvlib.modelchain.ModelChain`

**Required site parameters (from site registration, TRD §7 `/sites`):**

```python
site_params = {
    "latitude": float,          # degrees
    "longitude": float,         # degrees
    "altitude": float,          # meters, default 0 if unknown
    "surface_tilt": float,      # degrees, default = latitude (rule of thumb)
    "surface_azimuth": float,   # degrees, default 180 (north hemisphere south-facing)
    "capacity_kw": float,       # DC nameplate capacity
    "temp_coeff_pmax": -0.0040, # %/°C, default generic c-Si module
    "system_losses_pct": 14.0,  # default pvlib PVWatts loss model total
}
```

**Model chain configuration:**

```python
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain

location = Location(latitude=site["latitude"], longitude=site["longitude"],
                     altitude=site["altitude"], tz="Asia/Kolkata")

system = PVSystem(
    surface_tilt=site["surface_tilt"],
    surface_azimuth=site["surface_azimuth"],
    module_parameters={"pdc0": site["capacity_kw"] * 1000, "gamma_pdc": -0.0040},
    inverter_parameters={"pdc0": site["capacity_kw"] * 1000},
    temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
        "sapm"]["open_rack_glass_glass"],
)

mc = ModelChain(system, location,
                 dc_model="pvwatts", ac_model="pvwatts",
                 aoi_model="physical", spectral_model="no_loss")

# weather_df columns required: ghi, dni, dhi, temp_air, wind_speed (indexed by tz-aware datetime)
mc.run_model(weather_df)
physics_estimate_watts = mc.results.ac
```

**Fallback (if DNI/DHI unavailable from forecast source):** use `pvlib.irradiance.erbs` or `pvlib.irradiance.disc` to decompose GHI into DNI/DHI before running the chain. Never block the pipeline on missing irradiance components — fall back to `pvlib.clearsky.ineichen` scaled by a cloud-cover-derived clear-sky index if Open-Meteo GHI is missing.

### 1.3 M2-S — XGBoost Residual Corrector

**Target variable:** `residual = actual_generation_kw − physics_estimate_kw`

**Feature vector (17 features):**

| # | Feature | Type | Source |
|---|---------|------|--------|
| 1 | `ghi` | float | weather |
| 2 | `dni` | float | weather |
| 3 | `dhi` | float | weather |
| 4 | `temp_air` | float | weather |
| 5 | `wind_speed` | float | weather |
| 6 | `humidity` | float | weather |
| 7 | `cloud_cover_pct` | float | weather |
| 8 | `hour_sin`, `hour_cos` | float | cyclical encode of hour-of-day |
| 9 | `doy_sin`, `doy_cos` | float | cyclical encode of day-of-year |
| 10 | `solar_elevation` | float | `pvlib.solarposition.get_solarposition` |
| 11 | `solar_azimuth` | float | pvlib |
| 12 | `clearsky_index` | float | `ghi / clearsky_ghi` |
| 13 | `lag_1h_generation` | float | shifted actual (inference: last known) |
| 14 | `lag_24h_generation` | float | shifted actual |
| 15 | `rolling_mean_24h` | float | trailing window |
| 16 | `rolling_std_24h` | float | trailing window |
| 17 | `physics_estimate_kw` | float | M1-S output (used as a feature too — lets the corrector learn where physics is systematically off) |

**XGBoost hyperparameters (starting grid — tune via time-series CV, §4):**

```python
import xgboost as xgb

xgb_params = {
    "objective": "reg:squarederror",
    "n_estimators": 400,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 5,
    "reg_alpha": 0.1,       # L1
    "reg_lambda": 1.0,      # L2
    "gamma": 0.0,
    "tree_method": "hist",
    "early_stopping_rounds": 30,
    "eval_metric": "mae",
    "random_state": 42,
    "n_jobs": -1,
}

model = xgb.XGBRegressor(**xgb_params)
model.fit(
    X_train, y_train_residual,
    eval_set=[(X_val, y_val_residual)],
    verbose=False,
)
```

**Hyperparameter search space (if time allows — `RandomizedSearchCV` with `TimeSeriesSplit`, not `KFold`):**

```python
param_dist = {
    "max_depth": [3, 4, 5, 6, 8],
    "learning_rate": [0.01, 0.03, 0.05, 0.1],
    "n_estimators": [200, 400, 600, 800],
    "subsample": [0.6, 0.7, 0.8, 0.9, 1.0],
    "colsample_bytree": [0.6, 0.7, 0.8, 0.9, 1.0],
    "min_child_weight": [1, 3, 5, 7],
    "reg_lambda": [0.5, 1.0, 2.0, 5.0],
}
```

Budget: ≤30 iterations given 48h constraint — do not over-invest here; feature quality matters more than hyperparameter search (per TRD §5 design principle).

### 1.4 Inference (Final Forecast)

```python
final_forecast_kw = physics_estimate_kw + residual_model.predict(X_inference)
final_forecast_kw = final_forecast_kw.clip(lower=0, upper=site["capacity_kw"])  # physical bounds
```

---

## 2. Wind Model — M1-W (LightGBM, primary)

No physics-equivalent to pvlib exists in scope, so wind is direct weather → power regression.

### 2.1 Feature Vector (15 features)

| # | Feature | Type | Notes |
|---|---------|------|-------|
| 1 | `wind_speed_10m` | float | forecast, m/s |
| 2 | `wind_speed_hub` | float | extrapolated via power-law: `v_hub = v_10m * (h_hub/10)^alpha`, `alpha=0.14` default |
| 3 | `wind_direction_deg` | float | forecast |
| 4 | `wind_dir_sin`, `wind_dir_cos` | float | cyclical encode |
| 5 | `air_temp` | float | affects air density |
| 6 | `pressure` | float | affects air density |
| 7 | `air_density` | float | derived: `p / (287.05 * (T+273.15))` |
| 8 | `hour_sin`, `hour_cos` | float | cyclical |
| 9 | `month_sin`, `month_cos` | float | cyclical seasonal |
| 10 | `lag_1h_generation` | float | |
| 11 | `lag_24h_generation` | float | |
| 12 | `rolling_mean_6h` | float | wind is burstier — shorter window than solar |
| 13 | `turbine_rated_capacity_kw` | float | site param |
| 14 | `power_curve_estimate` | float | see §2.2 |
| 15 | `wind_speed_std_3h` | float | turbulence proxy |

### 2.2 Power-Curve Feature (physics-informed prior for wind, cheap to compute)

Even without pvlib-equivalent tooling, inject a simplified cubic power-curve estimate as a feature — this gives the GBM a physically sane prior to correct, same philosophy as the solar hybrid:

```python
def power_curve_estimate(v, v_cutin=3.0, v_rated=12.0, v_cutout=25.0, p_rated_kw=100.0):
    if v < v_cutin or v > v_cutout:
        return 0.0
    if v >= v_rated:
        return p_rated_kw
    # cubic region between cut-in and rated
    return p_rated_kw * ((v - v_cutin) / (v_rated - v_cutin)) ** 3
```

Use manufacturer power-curve points if available in site metadata; otherwise default to the generic cubic curve above with `v_cutin=3`, `v_rated=12`, `v_cutout=25` (typical utility-scale turbine values).

### 2.3 LightGBM Hyperparameters

```python
import lightgbm as lgb

lgb_params = {
    "objective": "regression",
    "metric": "mae",
    "boosting_type": "gbdt",
    "num_leaves": 31,
    "max_depth": -1,
    "learning_rate": 0.05,
    "n_estimators": 500,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "min_child_samples": 20,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "random_state": 42,
    "n_jobs": -1,
    "verbosity": -1,
}

model = lgb.LGBMRegressor(**lgb_params)
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)],
)
```

### 2.4 M2-W — XGBoost Alternative (A/B comparison)

Reuse the XGBoost config from §1.3, retargeted at raw `generation_kw` (not residual) with the wind feature set from §2.1. Report both LightGBM and XGBoost in the evaluation table (§4) — ship whichever wins on validation nMAE, default to LightGBM if within noise (it's faster to retrain and slightly better suited to smaller tabular datasets typical of Kaggle turbine SCADA logs).

### 2.5 M5 — WindFM (Optional, Inference-Only)

- **Use case:** benchmark comparison only, never the primary shipped model.
- **Integration constraint:** pretrained weights, zero-shot inference — do NOT attempt training/fine-tuning within the 48h window (per TRD §10 scope boundary).
- **Fallback:** if integration friction appears in the first 2 hours of attempting it, drop it — it is explicitly "nice-to-have."

---

## 3. Uncertainty Layer — M4 (P10 / P50 / P90)

### 3.1 Approach A — Quantile LightGBM (primary)

Train three separate LightGBM models with the quantile objective, same feature set as §1.3 / §2.1:

```python
quantiles = {"p10": 0.1, "p50": 0.5, "p90": 0.9}
quantile_models = {}

for name, alpha in quantiles.items():
    params = dict(lgb_params)  # base params from §2.3
    params.update({"objective": "quantile", "alpha": alpha})
    m = lgb.LGBMRegressor(**params)
    m.fit(X_train, y_train)
    quantile_models[name] = m
```

**Constraint enforcement (quantile crossing fix):** after prediction, sort per-row so `p10 <= p50 <= p90` always holds:

```python
import numpy as np
preds = np.sort(np.stack([p10_pred, p50_pred, p90_pred], axis=1), axis=1)
p10_pred, p50_pred, p90_pred = preds[:, 0], preds[:, 1], preds[:, 2]
```

### 3.2 Approach B — Residual Distribution Fallback

If quantile models underfit (validation coverage far from nominal — see §3.3), fall back to empirical residual sampling:

```python
residuals = y_val - point_forecast_val   # from the shipped point model (M3-S or M1-W)
p10_offset = np.percentile(residuals, 10)
p90_offset = np.percentile(residuals, 90)

p10_forecast = point_forecast + p10_offset
p90_forecast = point_forecast + p90_offset
```

Bucket residuals by hour-of-day or clear-sky index bin for a sharper (non-constant-width) band if time allows.

### 3.3 Calibration Check (mandatory before shipping)

```python
coverage_80 = np.mean((y_true >= p10_pred) & (y_true <= p90_pred))
# Target: coverage_80 ≈ 0.80 (±0.05 acceptable for hackathon scope)
```

Report this number on the pitch deck's methodology slide — judges asking "how do you know your confidence bands mean anything" is a predictable question (per PRD §8).

---

## 4. Evaluation Protocol

### 4.1 Validation Strategy — Walk-Forward, Never Random Split

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5, test_size=24*7)  # 7-day rolling test windows
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    # fit, predict, accumulate metrics per horizon bucket
```

### 4.2 Metrics (computed per horizon: 24h / 48h / 72h — never blended)

```python
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluate(y_true, y_pred, capacity_kw):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    nmae_pct = (mae / capacity_kw) * 100
    r2 = r2_score(y_true, y_pred)
    mask = y_true > 0.05 * capacity_kw   # avoid MAPE blow-up near zero generation
    mape_pct = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.any() else None
    forecast_reliability_score = 100 * (1 - nmae_pct / 100)
    return {
        "MAE": mae, "RMSE": rmse, "nMAE_%": nmae_pct,
        "R2": r2, "MAPE_%": mape_pct,
        "Forecast_Reliability_Score": forecast_reliability_score,
    }
```

### 4.3 Required Comparison Table (per horizon, per source)

| Model | 24h nMAE | 48h nMAE | 72h nMAE | 24h RMSE | R² |
|-------|----------|----------|----------|----------|-----|
| M0-S Persistence | — | — | — | — | — |
| M1-S pvlib only | — | — | — | — | — |
| M3-S Hybrid (shipped) | — | — | — | — | — |
| M0-W Persistence | — | — | — | — | — |
| M1-W LightGBM (shipped) | — | — | — | — | — |
| M2-W XGBoost | — | — | — | — | — |

**Target band (illustrative, calibrate against actual dataset — do not hard-code as a promise):** Forecast Reliability Score of 80–92% at 24h, 75–88% at 48h, 70–85% at 72h, corresponding to nMAE of roughly 8–20% depending on horizon. Always report the number the model actually produces on the held-out set, not this target range.

---

## 5. Feature Engineering — Shared Utility Code

```python
# backend/forecasting/features.py

import numpy as np
import pandas as pd
import pvlib

def add_cyclical_time_features(df: pd.DataFrame, col: str, period: int, prefix: str) -> pd.DataFrame:
    df[f"{prefix}_sin"] = np.sin(2 * np.pi * df[col] / period)
    df[f"{prefix}_cos"] = np.cos(2 * np.pi * df[col] / period)
    return df

def add_solar_position(df: pd.DataFrame, latitude: float, longitude: float) -> pd.DataFrame:
    solpos = pvlib.solarposition.get_solarposition(df.index, latitude, longitude)
    df["solar_elevation"] = solpos["apparent_elevation"].values
    df["solar_azimuth"] = solpos["azimuth"].values
    return df

def add_lag_and_rolling(df: pd.DataFrame, target_col: str,
                         lags=(1, 24), windows=(24,)) -> pd.DataFrame:
    for lag in lags:
        df[f"lag_{lag}h_generation"] = df[target_col].shift(lag)
    for w in windows:
        df[f"rolling_mean_{w}h"] = df[target_col].shift(1).rolling(w).mean()
        df[f"rolling_std_{w}h"] = df[target_col].shift(1).rolling(w).std()
    return df

def air_density(pressure_hpa: pd.Series, temp_c: pd.Series) -> pd.Series:
    R_specific = 287.05  # J/(kg·K), dry air
    return (pressure_hpa * 100) / (R_specific * (temp_c + 273.15))
```

---

## 6. Datasets & External Resources

### 6.1 Primary Training Data

| Resource | Purpose | Link Type | Notes |
|----------|---------|-----------|-------|
| Kaggle — Solar Power Generation Data | Historical solar generation + weather sensor readings | Kaggle dataset | Search: "Solar Power Generation Data" (Kaggle, includes 2 plant generation + weather sensor CSVs) |
| Kaggle — Wind Turbine SCADA Dataset | Historical turbine power + wind speed/direction | Kaggle dataset | Search: "Wind Turbine SCADA Dataset" |
| Open-Meteo Historical Weather API | GHI/DNI/DHI, temp, wind, humidity, pressure — no API key | REST API | `https://archive-api.open-meteo.com/v1/archive` |
| Open-Meteo Forecast API | 16-day forecast weather, no API key | REST API | `https://api.open-meteo.com/v1/forecast` |
| NREL NSRDB (stretch) | High-quality irradiance data, India coverage available | REST API (free key) | Use only if Open-Meteo GHI/DNI/DHI proves too coarse |

### 6.2 Libraries & Documentation

| Library | Version pin | Docs |
|---------|-------------|------|
| `pvlib-python` | `>=0.10` | pvlib.readthedocs.io — see `ModelChain` and `pvwatts` model docs |
| `xgboost` | `>=2.0` | xgboost.readthedocs.io — `XGBRegressor`, quantile objective (`reg:quantileerror`, XGBoost ≥2.0) |
| `lightgbm` | `>=4.0` | lightgbm.readthedocs.io — quantile objective, `early_stopping` callback API |
| `scikit-learn` | `>=1.3` | `TimeSeriesSplit`, metrics module |
| `pandas` / `numpy` | latest stable | — |
| `fastapi` / `uvicorn` | latest stable | for serving inference endpoints per TRD §7 |

### 6.3 Reference Implementation (UI/prototype scaffolding only — not model logic)

- `mehakagg1313/SOLAR-AND-WIND-ENERGY-PREDICTION` (GitHub) — reuse for frontend scaffolding ideas only, per workflow.md Phase 0. Do not reuse its ML approach (timestamp+profile input is not a valid forecasting design — see prior analysis). Note the bundled "Solartec" template's CC-BY-4.0 attribution requirement if any UI asset is reused (PRD §8).

### 6.4 Model Artifact Storage

```
models/
├── solar/
│   ├── physics_config.json         # site params used by ModelChain
│   ├── xgb_residual_v1.json        # XGBoost native format
│   └── quantile_p10_p50_p90/
│       ├── p10.txt                 # LightGBM native format
│       ├── p50.txt
│       └── p90.txt
├── wind/
│   ├── lgbm_wind_v1.txt
│   ├── xgb_wind_v1.json
│   └── quantile_p10_p50_p90/
└── metrics/
    └── evaluation_report.json      # output of §4.2, versioned per training run
```

Save/load pattern:

```python
model.save_model("models/solar/xgb_residual_v1.json")   # XGBoost
booster = lgb.Booster(model_file="models/wind/lgbm_wind_v1.txt")  # LightGBM
```

---

## 7. Training Entry Point (Reference Script Skeleton)

```python
# notebooks/solar_training.py  (mirror as .ipynb per TRD §3)

import pandas as pd
from backend.weather.provider import fetch_historical_weather
from backend.forecasting.features import (
    add_cyclical_time_features, add_solar_position, add_lag_and_rolling,
)
from backend.forecasting.solar import run_physics_model, train_residual_model
from backend.forecasting.evaluate import evaluate, walk_forward_split

# 1. Load
generation_df = pd.read_csv("data/raw/solar_generation.csv", parse_dates=["timestamp"])
weather_df = fetch_historical_weather(lat=site_lat, lon=site_lon,
                                       start=generation_df.timestamp.min(),
                                       end=generation_df.timestamp.max())

# 2. Merge + feature engineer
df = generation_df.merge(weather_df, on="timestamp", how="inner")
df = add_cyclical_time_features(df, "hour", 24, "hour")
df = add_cyclical_time_features(df, "day_of_year", 365, "doy")
df = add_solar_position(df, site_lat, site_lon)
df = add_lag_and_rolling(df, "generation_kw")
df = df.dropna()

# 3. Physics baseline
df["physics_estimate_kw"] = run_physics_model(df, site_params)
df["residual"] = df["generation_kw"] - df["physics_estimate_kw"]

# 4. Train/val split (walk-forward, §4.1)
for train_idx, val_idx in walk_forward_split(df, n_splits=5, horizon_hours=72):
    X_train, y_train = df.loc[train_idx, FEATURE_COLS], df.loc[train_idx, "residual"]
    X_val, y_val = df.loc[val_idx, FEATURE_COLS], df.loc[val_idx, "residual"]

    model = train_residual_model(X_train, y_train, X_val, y_val)  # §1.3 config
    final_pred = df.loc[val_idx, "physics_estimate_kw"] + model.predict(X_val)

    metrics = evaluate(df.loc[val_idx, "generation_kw"], final_pred, site_params["capacity_kw"])
    print(metrics)

model.save_model("models/solar/xgb_residual_v1.json")
```

---

## 8. Debug Checklist (Run Before Every Demo)

```python
assert (final_forecast_kw >= 0).all(), "Negative generation — clip not applied"
assert (final_forecast_kw <= site["capacity_kw"] * 1.02).all(), "Forecast exceeds nameplate capacity"
assert not X_train.isna().any().any(), "NaNs in feature matrix — check lag/rolling window warmup"
assert p10_pred.le(p50_pred).all() and p50_pred.le(p90_pred).all(), "Quantile crossing not resolved"
assert model_metrics["nMAE_%"] < persistence_metrics["nMAE_%"], "Model does not beat persistence baseline"
```

If any assertion fails during the pre-demo run, fall back one tier: hybrid → physics-only → persistence. Never present a model that fails its own baseline check.

---

## 9. Cross-References

- Decision-engine consumption of these outputs → `TRD.md` §6
- API contract exposing forecast/uncertainty → `TRD.md` §7 (`GET /forecast/{site_id}`)
- Task-level ownership and hour allocation → `work1.md` Phases 2–4
- Judge-facing accuracy framing (do not overclaim) → `PRD.md` §8
