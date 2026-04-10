import numpy as np

from app.evaluation.metrics import classification_metrics, regression_metrics


def test_regression_metrics_shape_and_values():
    y_true = np.array([[0.1], [0.0], [-0.1]], dtype=float)
    y_pred = np.array([[0.09], [0.01], [-0.11]], dtype=float)
    metrics = regression_metrics(y_true, y_pred)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert 0.0 <= metrics["directional_accuracy"] <= 1.0


def test_classification_metrics_include_confusion_matrix():
    y_true = np.array([[1], [0], [1], [0]], dtype=float)
    logits = np.array([[2.0], [-1.0], [1.5], [-2.0]], dtype=float)
    metrics = classification_metrics(y_true, logits)
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "confusion_matrix" in metrics
