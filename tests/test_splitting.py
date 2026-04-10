import numpy as np

from app.config.schema import SplitConfig, WalkForwardConfig
from app.datasets.splitting import chronological_split_indices, walk_forward_slices


def test_chronological_split_order_and_non_overlap():
    split = SplitConfig(train_ratio=0.7, validation_ratio=0.15, test_ratio=0.15, gap=3)
    indices = chronological_split_indices(200, split)

    train = indices["train"]
    validation = indices["validation"]
    test = indices["test"]

    assert train[-1] < validation[0]
    assert validation[-1] < test[0]
    assert np.intersect1d(train, validation).size == 0
    assert np.intersect1d(validation, test).size == 0


def test_walk_forward_slices_generate_multiple_folds():
    config = WalkForwardConfig(
        enabled=True,
        train_windows=50,
        validation_windows=20,
        test_windows=20,
        step_windows=10,
        max_folds=4,
    )
    folds = walk_forward_slices(200, config)
    assert len(folds) == 4
    assert folds[0]["train_start"] == 0
    assert folds[1]["train_start"] == 10
