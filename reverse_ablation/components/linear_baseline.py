from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder
from typing import Optional


def build_linear(builder: ModelBuilder) -> ModelBuilder:
    builder.use_conv = False
    builder.use_patch_embed = False
    builder.use_attention = False
    model = nn.Sequential(
        nn.Flatten(),
        nn.Linear(builder.input_size, builder.num_classes)
    )
    builder.layers = nn.ModuleList([nn.Flatten(), nn.Linear(builder.input_size, builder.num_classes)])
    return builder


def register_linear():
    ComponentRegistry.register(ComponentSpec(
        name="linear",
        description="Single linear layer (logistic regression baseline)",
        build_fn=build_linear,
        expected_param_delta="~30K params (3072->10)",
        citation="Meyes et al. 2019 — Ablation Studies in ANNs"
    ))
