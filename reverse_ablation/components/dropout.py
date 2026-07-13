from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


def build_dropout(builder: ModelBuilder) -> ModelBuilder:
    layers = [nn.Flatten()]
    layers.append(nn.Linear(builder.input_size, builder.width))
    layers.append(nn.ReLU())
    layers.append(nn.Dropout(0.3))
    layers.append(nn.Linear(builder.width, builder.num_classes))
    builder.layers = nn.ModuleList(layers)
    return builder


def register_dropout():
    ComponentRegistry.register(ComponentSpec(
        name="dropout",
        description="Add Dropout regularization (p=0.3)",
        build_fn=build_dropout,
        expected_param_delta="+0 params",
        citation="Srivastava et al. 2014 — Dropout (arXiv:1207.0580)"
    ))
