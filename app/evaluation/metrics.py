from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    payload: dict[str, Any] = {"mae": mae, "rmse": rmse}

    if y_true.ndim == 2 and y_true.shape[1] > 1:
        per_horizon: list[dict[str, float]] = []
        for idx in range(y_true.shape[1]):
            per_horizon.append(
                {
                    "step": idx + 1,
                    "mae": float(mean_absolute_error(y_true[:, idx], y_pred[:, idx])),
                    "rmse": float(np.sqrt(mean_squared_error(y_true[:, idx], y_pred[:, idx]))),
                }
            )
        payload["per_horizon"] = per_horizon

    true_sign = np.sign(y_true.reshape(-1))
    pred_sign = np.sign(y_pred.reshape(-1))
    payload["directional_accuracy"] = float(np.mean(true_sign == pred_sign))
    return payload


def classification_metrics(y_true: np.ndarray, logits: np.ndarray) -> dict[str, Any]:
    probs = 1.0 / (1.0 + np.exp(-logits.reshape(-1)))
    labels = (probs >= 0.5).astype(int)
    true_labels = y_true.reshape(-1).astype(int)

    payload: dict[str, Any] = {
        "accuracy": float(accuracy_score(true_labels, labels)),
        "precision": float(precision_score(true_labels, labels, zero_division=0)),
        "recall": float(recall_score(true_labels, labels, zero_division=0)),
        "f1": float(f1_score(true_labels, labels, zero_division=0)),
        "directional_accuracy": float(accuracy_score(true_labels, labels)),
        "confusion_matrix": confusion_matrix(true_labels, labels, labels=[0, 1]).tolist(),
    }

    unique_labels = np.unique(true_labels)
    if len(unique_labels) > 1:
        payload["roc_auc"] = float(roc_auc_score(true_labels, probs))
    else:
        payload["roc_auc"] = None
    return payload
