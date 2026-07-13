from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


def build_activation(builder: ModelBuilder) -> ModelBuilder:
    layers = [nn.Flatten()]
    layers.append(nn.Linear(builder.input_size, builder.width))
    layers.append(nn.ReLU())
    layers.append(nn.Linear(builder.width, builder.num_classes))
    builder.layers = nn.ModuleList(layers)
    return builder


def register_activation():
    ComponentRegistry.register(ComponentSpec(
        name="activation",
        description="Add ReLU non-linearity between linear layers",
        build_fn=build_activation,
        expected_param_delta="+0 params (activation is parameter-free)",
        citation="Nair & Hinton 2010 — Rectified Linear Units"
    ))
