from __future__ import annotations

from torch import nn

from app.config.schema import ModelConfig
from app.models.cnn1d import CNN1DBaseline
from app.models.gru import GRUBaseline
from app.models.mlp import MLPBaseline


def build_model(
    model_config: ModelConfig,
    *,
    input_window: int,
    input_features: int,
    output_dim: int,
) -> nn.Module:
    name = model_config.name
    if name == "mlp":
        return MLPBaseline(
            input_window=input_window,
            input_features=input_features,
            output_dim=output_dim,
            hidden_dim=model_config.hidden_dim,
            num_layers=model_config.num_layers,
            dropout=model_config.dropout,
        )
    if name == "cnn1d":
        return CNN1DBaseline(
            input_window=input_window,
            input_features=input_features,
            output_dim=output_dim,
            channels=model_config.cnn_channels,
            kernel_size=model_config.cnn_kernel_size,
            dropout=model_config.dropout,
        )
    if name == "gru":
        return GRUBaseline(
            input_features=input_features,
            output_dim=output_dim,
            hidden_size=model_config.gru_hidden_size,
            num_layers=model_config.gru_num_layers,
            dropout=model_config.dropout,
        )
    raise ValueError(f"Unsupported model type: {name}")
