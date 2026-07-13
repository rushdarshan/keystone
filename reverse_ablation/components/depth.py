from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


def build_depth(builder: ModelBuilder) -> ModelBuilder:
    layers = [nn.Flatten()]
    in_dim = builder.input_size
    num_hidden = 3
    hidden_sizes = [builder.width * (2 ** i) for i in range(num_hidden)]
    for h in hidden_sizes:
        layers.append(nn.Linear(in_dim, h))
        layers.append(nn.ReLU())
        in_dim = h
    layers.append(nn.Linear(in_dim, builder.num_classes))
    builder.layers = nn.ModuleList(layers)
    return builder


def register_depth():
    ComponentRegistry.register(ComponentSpec(
        name="depth",
        description="Multiple hidden layers (3-layer MLP)",
        build_fn=build_depth,
        expected_param_delta="+300K-1M params depending on width",
        citation="Bengio et al. 2007 — Greedy Layer-Wise Training of Deep Networks"
    ))
