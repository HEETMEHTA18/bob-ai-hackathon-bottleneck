"""
Bottleneck ML — Model Evaluation
==================================
Computes MODEL.md required metrics, calibration check, and threshold analysis.

Primary metrics:  PR-AUC, Recall, Precision, F1
Secondary metrics: ROC-AUC, Brier score, confusion matrix
Additional:       threshold sweep, calibration, top-feature summary
"""

from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

MODELS_DIR = _ROOT / "models" / "bottleneck"
DATA_DIR   = _ROOT / "data"


def evaluate_failure_model(
    model_name: str = "failure_24h",
    target_col: str = "failure_within_24h",
    threshold:  float = 0.50,
    write_json: bool  = True,
) -> dict:
    """
    Load the saved XGBoost model and evaluate against the held-out test split.

    Returns a metrics dict and optionally writes it to  models/bottleneck/<model_name>_eval.json.
    """
    import xgboost as xgb
    from sklearn.metrics import (
        average_precision_score, recall_score, precision_score,
        f1_score, roc_auc_score, brier_score_loss,
        confusion_matrix, precision_recall_curve,
    )

    # Load model
    model_path = MODELS_DIR / f"{model_name}.json"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    model = xgb.XGBClassifier()
    model.load_model(str(model_path))

    # Load metadata to get feature list
    meta_path = MODELS_DIR / f"{model_name}_metadata.json"
    with open(meta_path) as f:
        metadata = json.load(f)
    feature_list = metadata["feature_list"]

    # Load test data
    from backend.bottleneck.ml.training.train_models import load_training_data, chronological_split
    df = load_training_data()
    _, _, test_df = chronological_split(df)

    X_test = test_df[feature_list].values.astype(np.float32)
    y_test = test_df[target_col].values.astype(int)

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)

    metrics: dict = {
        "model_name"   : model_name,
        "target"       : target_col,
        "evaluated_at" : datetime.utcnow().isoformat(),
        "threshold"    : threshold,
        "test_rows"    : int(len(y_test)),
        "positive_rate": round(float(y_test.mean()), 4),
    }

    if y_test.sum() > 0 and y_test.sum() < len(y_test):
        metrics.update({
            "pr_auc"           : round(float(average_precision_score(y_test, y_prob)), 4),
            "roc_auc"          : round(float(roc_auc_score(y_test, y_prob)), 4),
            "recall"           : round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "precision"        : round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "f1"               : round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "brier_score"      : round(float(brier_score_loss(y_test, y_prob)), 4),
            "confusion_matrix" : confusion_matrix(y_test, y_pred).tolist(),
        })

        # Threshold sweep (precision/recall at various operating points)
        prec_arr, rec_arr, thr_arr = precision_recall_curve(y_test, y_prob)
        sweep = []
        for t in np.arange(0.10, 0.96, 0.10):
            yp = (y_prob >= t).astype(int)
            sweep.append({
                "threshold": round(t, 2),
                "recall"   : round(float(recall_score(y_test, yp, zero_division=0)), 3),
                "precision": round(float(precision_score(y_test, yp, zero_division=0)), 3),
                "f1"       : round(float(f1_score(y_test, yp, zero_division=0)), 3),
            })
        metrics["threshold_sweep"] = sweep

        # Calibration: mean predicted vs. actual positive rate per decile
        bins = np.percentile(y_prob, np.arange(0, 101, 10))
        bins = np.unique(bins)
        cal = []
        for i in range(len(bins) - 1):
            mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
            if mask.sum() > 0:
                cal.append({
                    "pred_mean" : round(float(y_prob[mask].mean()), 3),
                    "actual_rate": round(float(y_test[mask].mean()), 3),
                    "n"         : int(mask.sum()),
                })
        metrics["calibration"] = cal
    else:
        metrics["warning"] = "Test set has too few positive/negative samples for full metrics"

    if write_json:
        out_path = MODELS_DIR / f"{model_name}_eval.json"
        with open(out_path, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"[Eval] Written to {out_path}")

    return metrics


def run_full_evaluation() -> dict:
    """Evaluate all three models and return a combined report."""
    report = {}
    for name, col in [("failure_24h", "failure_within_24h"),
                       ("failure_72h", "failure_within_72h")]:
        try:
            report[name] = evaluate_failure_model(name, col)
            print(f"  {name}: PR-AUC={report[name].get('pr_auc','?')}  "
                  f"F1={report[name].get('f1','?')}")
        except FileNotFoundError as e:
            report[name] = {"error": str(e)}

    # Combine into a single summary
    combined_path = MODELS_DIR / "evaluation_report.json"
    combined = {
        "evaluated_at": datetime.utcnow().isoformat(),
        "models"      : report,
    }
    with open(combined_path, "w") as f:
        json.dump(combined, f, indent=2)
    print(f"[Eval] Full report written to {combined_path}")
    return combined


if __name__ == "__main__":
    run_full_evaluation()
