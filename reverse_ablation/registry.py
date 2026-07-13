from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
import torch
import torch.nn as nn


@dataclass
class ComponentSpec:
    name: str
    description: str
    build_fn: Callable[[int, int, int, int], nn.Module]
    expected_param_delta: str
    citation: str = ""


class ModelBuilder:
    def __init__(self, input_size: int = 3072, num_classes: int = 10, img_size: int = 32, in_channels: int = 3):
        self.input_size = input_size
        self.num_classes = num_classes
        self.img_size = img_size
        self.in_channels = in_channels
        self.layers: nn.ModuleList = nn.ModuleList()
        self.depth = 0
        self.width = 64
        self.use_conv = False
        self.use_residual = False
        self.use_batchnorm = False
        self.use_dropout = False
        self.use_layer_norm = False
        self.use_attention = False
        self.use_patch_embed = False
        self.use_pos_embed = False

    def build(self) -> nn.Module:
        seq = nn.Sequential(*self.layers)
        return seq


class ComponentRegistry:
    _components: Dict[str, ComponentSpec] = {}

    @classmethod
    def register(cls, spec: ComponentSpec):
        cls._components[spec.name] = spec

    @classmethod
    def get(cls, name: str) -> ComponentSpec:
        return cls._components[name]

    @classmethod
    def list(cls) -> List[str]:
        return list(cls._components.keys())

    @classmethod
    def build_sequence(cls, names: List[str], builder: ModelBuilder) -> nn.Module:
        for name in names:
            spec = cls.get(name)
            builder = spec.build_fn(builder)
        return builder.build()


def register(fn: Callable) -> ComponentSpec:
    spec = fn(None)
    ComponentRegistry.register(spec)
    return spec
