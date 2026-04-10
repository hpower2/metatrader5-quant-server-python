from __future__ import annotations

import torch
from torch import nn


class MLPBaseline(nn.Module):
    def __init__(self, *, input_window: int, input_features: int, output_dim: int, hidden_dim: int, num_layers: int, dropout: float) -> None:
        super().__init__()
        flattened = input_window * input_features
        layers: list[nn.Module] = [nn.Linear(flattened, hidden_dim), nn.ReLU(), nn.Dropout(dropout)]
        for _ in range(max(0, num_layers - 1)):
            layers.extend([nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout)])
        layers.append(nn.Linear(hidden_dim, output_dim))
        self.model = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x.reshape(x.size(0), -1))
