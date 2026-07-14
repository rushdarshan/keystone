from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


def build_convolution(builder: ModelBuilder) -> ModelBuilder:

    model = nn.Sequential(
        nn.Conv2d(builder.in_channels, 32, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(32, 64, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(64 * 8 * 8, builder.width),
        nn.ReLU(),
        nn.Linear(builder.width, builder.num_classes),
    )
    builder.layers = nn.ModuleList(list(model))
    return builder


def register_convolution():
    ComponentRegistry.register(ComponentSpec(
        name="convolution",
        description="Add convolutional layers (2 conv+pool blocks)",
        build_fn=build_convolution,
        expected_param_delta="+50K params",
        citation="LeCun et al. 1989 — Backpropagation Applied to Handwritten Zip Code Recognition; Krizhevsky et al. 2012 — AlexNet"
    ))
