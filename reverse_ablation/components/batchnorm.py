from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


def build_batchnorm(builder: ModelBuilder) -> ModelBuilder:
    layers = [nn.Flatten()]
    layers.append(nn.Linear(builder.input_size, builder.width))
    layers.append(nn.BatchNorm1d(builder.width))
    layers.append(nn.ReLU())
    layers.append(nn.Linear(builder.width, builder.num_classes))
    builder.layers = nn.ModuleList(layers)
    return builder


def register_batchnorm():
    ComponentRegistry.register(ComponentSpec(
        name="batchnorm",
        description="Add Batch Normalization after linear layers",
        build_fn=build_batchnorm,
        expected_param_delta="+512 params (affine transform per channel)",
        citation="Ioffe & Szegedy 2015 — Batch Normalization (arXiv:1502.03167)"
    ))
