from __future__ import annotations
import torch
import torch
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


class AttentionMLP(nn.Module):
    def __init__(self, num_patches=64, embed_dim=128, num_classes=10, num_heads=4):
        super().__init__()
        self.pos_embed = nn.Parameter(torch.randn(1, num_patches, embed_dim) * 0.02)
        self.attn = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.norm = nn.LayerNorm(embed_dim)
        self.fc = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        B = x.shape[0]
        x = x + self.pos_embed
        attn_out, _ = self.attn(self.norm(x), self.norm(x), self.norm(x))
        x = x + attn_out
        x = x.mean(dim=1)
        return self.fc(x)


def build_attention(builder: ModelBuilder) -> ModelBuilder:

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
