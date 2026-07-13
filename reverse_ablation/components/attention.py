from __future__ import annotations
import torch
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder
import math


class SelfAttention(nn.Module):
    def __init__(self, embed_dim, num_heads=4):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.qkv = nn.Linear(embed_dim, embed_dim * 3)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.scale = self.head_dim ** -0.5

    def forward(self, x):
        B, N, D = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        x = (attn @ v).transpose(1, 2).reshape(B, N, D)
        return self.proj(x)


class AttentionMLP(nn.Module):
    def __init__(self, num_patches=64, embed_dim=128, num_classes=10, num_heads=4):
        super().__init__()
        self.pos_embed = nn.Parameter(torch.randn(1, num_patches, embed_dim) * 0.02)
        self.attn = SelfAttention(embed_dim, num_heads)
        self.norm = nn.LayerNorm(embed_dim)
        self.fc = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        B = x.shape[0]
        x = x + self.pos_embed
        x = x + self.attn(self.norm(x))
        x = x.mean(dim=1)
        return self.fc(x)


def build_attention(builder: ModelBuilder) -> ModelBuilder:
    builder.use_attention = True
    num_patches = 64
    embed_dim = 128
    model = AttentionMLP(num_patches=num_patches, embed_dim=embed_dim, num_classes=builder.num_classes, num_heads=4)
    builder.layers = nn.ModuleList([model])
    return builder


def register_attention():
    ComponentRegistry.register(ComponentSpec(
        name="attention",
        description="Multi-head self-attention (transformer encoder block)",
        build_fn=build_attention,
        expected_param_delta="+150K params",
        citation="Vaswani et al. 2017 — Attention Is All You Need (arXiv:1706.03762)"
    ))
