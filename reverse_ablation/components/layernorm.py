from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


def build_layernorm(builder: ModelBuilder) -> ModelBuilder:
    layers = [nn.Flatten()]
    layers.append(nn.Linear(builder.input_size, builder.width))
    layers.append(nn.LayerNorm(builder.width))
    layers.append(nn.ReLU())
    layers.append(nn.Linear(builder.width, builder.num_classes))
    builder.layers = nn.ModuleList(layers)
    return builder


def register_layernorm():
    ComponentRegistry.register(ComponentSpec(
        name="layernorm",
        description="Add Layer Normalization",
        build_fn=build_layernorm,
        expected_param_delta="+512 params",
        citation="Ba et al. 2016 — Layer Normalization (arXiv:1607.06450)"
    ))
