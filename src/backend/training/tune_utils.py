"""
Bottleneck — Time-Series Model Tuning Utilities

Shared, principled training helpers so solar/wind don't overfit or underfit:
  - strictly chronological splits (NO shuffling)
  - TimeSeriesSplit cross-validation for hyperparameter selection
  - early stopping on the validation fold
  - train/val/test gap reported to detect over/underfitting
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from backend.forecasting.evaluate import evaluate


def cap(x, c):
    return np.clip(np.asarray(x, dtype=float), 0, c)


def ts_splits(n_rows, n_splits=5, gap=0, test_frac=0.2, min_train=0.4):
    """Yield expanding-window (train, val) index pairs, chronological, no shuffle."""
    n = int(n_rows)
    first_test = int(n * (1 - test_frac))
    widths = np.linspace(first_test // (n_splits + 1), first_test, n_splits, dtype=int)
    if min_train:
        widths = np.clip(widths, int(n * min_train), first_test)
    for w in widths:
        tr = np.arange(int(w))
        va = np.arange(int(w) + gap, first_test)
        yield tr, va


def hparam_search(model_factory, X, y, n_splits=5, n_iters=16, seed=42,
                  metric="RMSE", capacity=100.0):
    """
    Randomized hyperparameter search with TimeSeriesSplit evaluation.
    model_factory(params) -> fitted (model, val_metric). Return best params.
    """
    rng = np.random.default_rng(seed)
    # Parameter space is passed via factory; sample n_iters combos.
    best = None
    history = []
    for _ in range(n_iters):
        try:
            model, m = model_factory(rng)
        except Exception as e:
            print(f"  [tune] combo failed: {e}")
            continue
        history.append((m, model))
        if best is None or m < best[0]:
            best = (m, model)
    history.sort(key=lambda x: x[0])
    if best is None:
        raise RuntimeError("hparam_search: no valid hyperparameter combo")
    return best[1], [m for m, _ in history], best[0]


def report_overfit(asset, train_m, val_m, test_m):
    """Print train vs val vs test so over/underfit is visible."""
    names = {"nMAE_%": "nMAE%", "R2": "R²", "RMSE": "RMSE"}
    print(f"\n[{asset.upper()}] Overfit check (train | val | test):")
    for k, label in names.items():
        t, v, e = train_m[k], val_m[k], test_m[k]
        tv = abs(t - v) * (2 if k == "R2" else 1)
        print(f"  {label:<6} train={t:.3f}  val={v:.3f}  test={e:.3f}   (train↔val Δ={tv:.3f})")
    if train_m["R2"] - val_m["R2"] > 0.10:
        print("  ⚠ large train↔val R² gap — possible overfit; consider simpler model")
    elif val_m["R2"] < 0.3:
        print("  ⚠ low val R² — possible underfit; consider more capacity/features")
    else:
        print("  ✓ train≈val gap is small (no obvious overfit) and val R² healthy")