from __future__ import annotations

import torch
from torch import nn


class CNN1DBaseline(nn.Module):
    def __init__(
        self,
        *,
        input_window: int,
        input_features: int,
        output_dim: int,
        channels: int,
        kernel_size: int,
        dropout: float,
    ) -> None:
        super().__init__()
        padding = kernel_size // 2
        self.feature_extractor = nn.Sequential(
            nn.Conv1d(input_features, channels, kernel_size=kernel_size, padding=padding),
            nn.ReLU(),
            nn.Conv1d(channels, channels, kernel_size=kernel_size, padding=padding),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Dropout(dropout),
        )
        self.head = nn.Linear(channels, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input shape: (batch, window, features) -> CNN expects (batch, features, window)
        features = self.feature_extractor(x.transpose(1, 2))
        return self.head(features)
