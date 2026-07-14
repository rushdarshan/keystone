from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder
from typing import Optional


def build_head_only(builder: ModelBuilder) -> ModelBuilder:

    model = nn.Sequential(
        nn.Flatten(),
        nn.Linear(builder.input_size, builder.width),
        nn.ReLU(),
        nn.Linear(builder.width, builder.num_classes)
    )
    builder.layers = nn.ModuleList([
        nn.Flatten(),
        nn.Linear(builder.input_size, builder.width),
        nn.ReLU(),
        nn.Linear(builder.width, builder.num_classes)
    ])
    return builder


def register_head_only():
    ComponentRegistry.register(ComponentSpec(
        name="head_only",
        description="Minimal MLP: flatten -> linear -> ReLU -> linear (no conv, no norm)",
        build_fn=build_head_only,
        expected_param_delta="~200K params",
        citation="Goodfellow, Bengio, Courville 2016"
    ))
