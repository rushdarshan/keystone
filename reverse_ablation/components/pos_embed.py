from __future__ import annotations
import torch
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder
import math


class LearnedPosEmbed(nn.Module):
    def __init__(self, num_patches, embed_dim):
        super().__init__()
        self.pos_embed = nn.Parameter(torch.randn(1, num_patches, embed_dim) * 0.02)

    def forward(self, x):
        return x + self.pos_embed


class SinusoidalPosEmbed(nn.Module):
    def __init__(self, num_patches, embed_dim):
        super().__init__()
        pe = torch.zeros(num_patches, embed_dim)
        position = torch.arange(0, num_patches, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, embed_dim, 2).float() * (-math.log(10000.0) / embed_dim))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe


class PosEmbedMLP(nn.Module):
    def __init__(self, input_size=3072, embed_dim=256, num_classes=10):
        super().__init__()
        self.fc1 = nn.Linear(input_size, embed_dim)
        self.pos_embed = LearnedPosEmbed(1, embed_dim)
        self.fc2 = nn.Linear(embed_dim, embed_dim)
        self.relu = nn.ReLU()
        self.fc3 = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        B = x.shape[0]
        x = x.view(B, -1)
        x = self.fc1(x).unsqueeze(1)
        x = self.pos_embed(x)
        x = self.fc2(x.squeeze(1))
        x = self.relu(x)
        return self.fc3(x)


def build_pos_embed(builder: ModelBuilder) -> ModelBuilder:
    model = PosEmbedMLP(input_size=builder.input_size, embed_dim=256, num_classes=builder.num_classes)
    builder.layers = nn.ModuleList([model])
    return builder


def register_pos_embed():
    ComponentRegistry.register(ComponentSpec(
        name="pos_embed",
        description="Add positional encoding (learned) to MLP",
        build_fn=build_pos_embed,
        expected_param_delta="+256 params",
        citation="Vaswani et al. 2017; Dosovitskiy et al. 2021"
    ))
