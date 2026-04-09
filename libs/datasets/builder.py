from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import Field

from libs.common.config import QuantSettings, get_settings
from libs.common.types import PlatformModel
from libs.common.time import parse_api_datetime
from libs.features.engineering import FeatureConfig, compute_features, join_multi_timeframe_features
from libs.labels.engine import LabelConfig, create_labels
from libs.storage.db import db_session, get_engine
from libs.storage.repositories import ArtifactRepository, CandleRepository


class SplitConfig(PlatformModel):
    train_ratio: float = 0.7
    validation_ratio: float = 0.15
    test_ratio: float = 0.15
    train_bars: int | None = None
    validation_bars: int | None = None
    test_bars: int | None = None


class WalkForwardConfig(PlatformModel):
    train_bars: int = 2000
    validation_bars: int = 500
    test_bars: int = 500
    step_bars: int = 500


class DatasetBuildConfig(PlatformModel):
    dataset_name: str
    symbol: str
    timeframe: str
    total_bars: int | None = None
    start: str | None = None
    end: str | None = None
    split: SplitConfig = Field(default_factory=SplitConfig)
    walk_forward: WalkForwardConfig = Field(default_factory=WalkForwardConfig)
    feature_config: FeatureConfig = Field(default_factory=FeatureConfig)
    label_config: LabelConfig = Field(default_factory=LabelConfig)
    higher_timeframe: str | None = None
    export_parquet: bool = True
    write_to_database: bool = False
    database_table_name: str | None = None


@dataclass
class DatasetBuildArtifacts:
    dataset: pd.DataFrame
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    walk_forward_slices: list[dict[str, int]]
    artifact_dir: Path


class DatasetBuilder:
    def __init__(self, settings: QuantSettings | None = None) -> None:
        self.settings = settings or get_settings()

    def load_base_frame(self, config: DatasetBuildConfig) -> pd.DataFrame:
        with db_session() as session:
            repo = CandleRepository(session)
            return repo.to_frame(
                symbol=config.symbol,
                timeframe=config.timeframe,
                start=parse_api_datetime(config.start) if config.start else None,
                end=parse_api_datetime(config.end) if config.end else None,
                limit=config.total_bars,
            )

    def build(self, config: DatasetBuildConfig) -> DatasetBuildArtifacts:
        base_frame = self.load_base_frame(config)
        feature_frame = compute_features(base_frame, config.feature_config)

        if config.higher_timeframe:
            with db_session() as session:
                repo = CandleRepository(session)
                higher_frame = repo.to_frame(symbol=config.symbol, timeframe=config.higher_timeframe)
            higher_features = compute_features(higher_frame, config.feature_config)
            feature_frame = join_multi_timeframe_features(feature_frame, higher_features, config.higher_timeframe.lower())

        labelled = create_labels(feature_frame, config.label_config)
        cleaned = labelled.dropna().reset_index(drop=True)
        train, validation, test = self._split(cleaned, config.split)
        walk_forward = self._build_walk_forward(cleaned, config.walk_forward)
        artifact_dir = self._export(cleaned, train, validation, test, walk_forward, config)

        if config.write_to_database and config.database_table_name:
            cleaned.to_sql(config.database_table_name, get_engine(), if_exists="replace", index=False)

        with db_session() as session:
            artifact_repo = ArtifactRepository(session)
            artifact_repo.create_dataset_manifest(
                name=config.dataset_name,
                config=config.model_dump(mode="json"),
                artifact_path=artifact_dir,
                train_rows=len(train),
                validation_rows=len(validation),
                test_rows=len(test),
            )

        return DatasetBuildArtifacts(
            dataset=cleaned,
            train=train,
            validation=validation,
            test=test,
            walk_forward_slices=walk_forward,
            artifact_dir=artifact_dir,
        )

    def _split(self, frame: pd.DataFrame, config: SplitConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        use_bar_split = any(value is not None for value in (config.train_bars, config.validation_bars, config.test_bars))

        if use_bar_split:
            train_bars = config.train_bars or 0
            validation_bars = config.validation_bars or 0
            raw_test_bars = config.test_bars
            requested_test_bars = raw_test_bars if raw_test_bars is not None and raw_test_bars > 0 else None

            if train_bars <= 0:
                raise ValueError("split.train_bars must be greater than 0 when using bar-based split")
            if validation_bars < 0:
                raise ValueError("split.validation_bars cannot be negative")
            if raw_test_bars is not None and raw_test_bars < 0:
                raise ValueError("split.test_bars cannot be negative")

            if train_bars + validation_bars > len(frame):
                raise ValueError(
                    f"Requested train+validation bars ({train_bars + validation_bars}) exceed available dataset rows ({len(frame)})"
                )

            remaining = len(frame) - train_bars - validation_bars
            if requested_test_bars is not None:
                if requested_test_bars > remaining:
                    raise ValueError(
                        f"Requested test bars ({requested_test_bars}) exceed remaining rows after train+validation ({remaining})"
                    )
                test_bars = requested_test_bars
            else:
                test_bars = remaining

            if test_bars <= 0:
                raise ValueError("No rows left for test split after applying train/validation bars")

            train_end = train_bars
            validation_end = train_end + validation_bars
            test_end = validation_end + test_bars
            train = frame.iloc[:train_end].copy()
            validation = frame.iloc[train_end:validation_end].copy()
            test = frame.iloc[validation_end:test_end].copy()
            return train, validation, test

        train_end = int(len(frame) * config.train_ratio)
        validation_end = train_end + int(len(frame) * config.validation_ratio)
        train = frame.iloc[:train_end].copy()
        validation = frame.iloc[train_end:validation_end].copy()
        test = frame.iloc[validation_end:].copy()
        return train, validation, test

    def _build_walk_forward(self, frame: pd.DataFrame, config: WalkForwardConfig) -> list[dict[str, int]]:
        slices: list[dict[str, int]] = []
        start = 0
        while start + config.train_bars + config.validation_bars + config.test_bars <= len(frame):
            slices.append(
                {
                    "train_start": start,
                    "train_end": start + config.train_bars,
                    "validation_end": start + config.train_bars + config.validation_bars,
                    "test_end": start + config.train_bars + config.validation_bars + config.test_bars,
                }
            )
            start += config.step_bars
        return slices

    def _export(
        self,
        dataset: pd.DataFrame,
        train: pd.DataFrame,
        validation: pd.DataFrame,
        test: pd.DataFrame,
        walk_forward: list[dict[str, int]],
        config: DatasetBuildConfig,
    ) -> Path:
        artifact_dir = self.settings.dataset_output_dir / config.dataset_name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        if config.export_parquet:
            dataset.to_parquet(artifact_dir / "dataset.parquet", index=False)
            train.to_parquet(artifact_dir / "train.parquet", index=False)
            validation.to_parquet(artifact_dir / "validation.parquet", index=False)
            test.to_parquet(artifact_dir / "test.parquet", index=False)
        pd.DataFrame(walk_forward).to_json(artifact_dir / "walk_forward.json", orient="records", indent=2)
        return artifact_dir
