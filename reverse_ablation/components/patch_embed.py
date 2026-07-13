from __future__ import annotations
import torch
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder
import math


class PatchEmbed(nn.Module):
    def __init__(self, in_channels=3, img_size=32, patch_size=4, embed_dim=128):
        super().__init__()
        self.num_patches = (img_size // patch_size) ** 2
        self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        x = self.proj(x)
        x = x.flatten(2).transpose(1, 2)
        return x


class TinyViT(nn.Module):
    def __init__(self, in_channels=3, img_size=32, patch_size=4, embed_dim=128, depth=4, num_heads=4, num_classes=10):
        super().__init__()
        self.patch_embed = PatchEmbed(in_channels, img_size, patch_size, embed_dim)
        self.num_patches = self.patch_embed.num_patches
        self.pos_embed = nn.Parameter(torch.randn(1, self.num_patches + 1, embed_dim) * 0.02)
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim) * 0.02)
        self.blocks = nn.ModuleList([
            nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads, dim_feedforward=embed_dim*4, activation='gelu', batch_first=True, dropout=0.1)
            for _ in range(depth)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        B = x.shape[0]
        x = self.patch_embed(x)
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        x = x + self.pos_embed
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)
        return self.head(x[:, 0])


def build_patch_embed(builder: ModelBuilder) -> ModelBuilder:
    builder.use_patch_embed = True
    builder.use_attention = True
    import torch
    model = TinyViT(
        in_channels=builder.in_channels,
        img_size=builder.img_size,
        patch_size=4,
        embed_dim=128,
        depth=4,
        num_heads=4,
        num_classes=builder.num_classes,
    )
    builder.layers = nn.ModuleList([model])
    return builder


def register_patch_embed():
    ComponentRegistry.register(ComponentSpec(
        name="patch_embed",
        description="Patch embedding layer (ViT-style, no conv backbone)",
        build_fn=build_patch_embed,
        expected_param_delta="+1.5M params",
        citation="Dosovitskiy et al. 2021 — An Image is Worth 16x16 Words (ViT; arXiv:2010.11929)"
    ))
