from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


def build_width(builder: ModelBuilder) -> ModelBuilder:
    layers = [nn.Flatten()]
    in_dim = builder.input_size
    expanded_width = builder.width * 4
    layers.append(nn.Linear(in_dim, expanded_width))
    layers.append(nn.ReLU())
    layers.append(nn.Linear(expanded_width, builder.num_classes))
    builder.layers = nn.ModuleList(layers)
    return builder


def register_width():
    ComponentRegistry.register(ComponentSpec(
        name="width",
        description="Increased hidden dimension (256 -> 1024)",
        build_fn=build_width,
        expected_param_delta="+2M params",
        citation="Kaplan et al. 2020 — Scaling Laws for Neural Language Models"
    ))
