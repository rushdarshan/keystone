"""Structured attention-head removal for Vision Transformers."""

from __future__ import annotations

import types

import torch
import torch.nn as nn
import torch.nn.functional as F


def prune_heads(model: nn.Module, keep_indices: dict[int, list[int]]) -> nn.Module:
    """Remove attention heads from a ViT model in-place.

    Args:
        model: A ViT model (DINOv3, DINOv2, etc.) with blocks.N.attn modules.
        keep_indices: Dict mapping layer_idx -> list of head indices to KEEP.
                      e.g., {0: [0,1,2], 1: [0,3,5]} keeps heads 0,1,2 in layer 0
                      and heads 0,3,5 in layer 1. All other heads are removed.

    Returns:
        The same model (mutated in-place) with heads pruned.
    """
    for layer_idx, keep_heads in keep_indices.items():
        block = model.blocks[layer_idx]
        attn = block.attn
        attn = _prune_attention_heads(attn, keep_heads)
        block.attn = attn
    return model


def _prune_attention_heads(attn: nn.Module, keep_heads: list[int]) -> nn.Module:
    """Prune heads from a single attention module.

    Works with EvaAttention (DINOv3) and Attention (DINOv2, standard ViT).

    EvaAttention layout:
      qkv: nn.Linear(embed_dim, 3 * num_heads * head_dim)
      proj: nn.Linear(num_heads * head_dim, embed_dim)
      num_heads: int
      head_dim: int (usually embed_dim // num_heads)

    Each head spans head_dim channels in qkv output and head_dim columns in proj input.
    QKV layout: [Q_chunk (num_heads*head_dim), K_chunk, V_chunk] stacked vertically.
    """
    if not keep_heads:
        raise ValueError(f"Must keep at least 1 attention head per layer, got {keep_heads}")

    num_heads = attn.num_heads
    head_dim = attn.head_dim if hasattr(attn, 'head_dim') else attn.qkv.out_features // (3 * num_heads)

    keep_set = set(keep_heads)
    if not keep_set.issubset(set(range(num_heads))):
        raise ValueError(f"Head indices {keep_set - set(range(num_heads))} out of range [0, {num_heads-1}]")

    if len(keep_heads) == num_heads:
        return attn

    keep_heads = sorted(keep_heads)
    new_num_heads = len(keep_heads)
    new_attn_dim = new_num_heads * head_dim

    qkv_keep_indices = []
    for offset in range(3):
        base = offset * num_heads * head_dim
        for h in keep_heads:
            start = base + h * head_dim
            qkv_keep_indices.extend(range(start, start + head_dim))

    qkv_keep = torch.tensor(qkv_keep_indices, dtype=torch.long, device=attn.qkv.weight.device)

    attn.qkv.weight = nn.Parameter(attn.qkv.weight.data[qkv_keep, :].clone())
    if attn.qkv.bias is not None:
        attn.qkv.bias = nn.Parameter(attn.qkv.bias.data[qkv_keep].clone())
    attn.qkv.out_features = 3 * new_attn_dim

    proj_keep_indices = []
    for h in keep_heads:
        start = h * head_dim
        proj_keep_indices.extend(range(start, start + head_dim))

    proj_keep = torch.tensor(proj_keep_indices, dtype=torch.long, device=attn.proj.weight.device)

    attn.proj.weight = nn.Parameter(attn.proj.weight.data[:, proj_keep].clone())
    attn.proj.in_features = new_attn_dim

    attn.num_heads = new_num_heads

    attn.attn_dim = new_attn_dim
    if hasattr(attn, 'head_dim') and num_heads != 0:
        attn.head_dim = head_dim
    if hasattr(attn, 'inner_dim'):
        attn.inner_dim = new_attn_dim

    _update_bias_dims(attn, num_heads, head_dim, keep_heads, new_attn_dim)

    if type(attn).__name__ != 'EvaAttention':
        raise TypeError(
            f"Unsupported attention type: {type(attn).__name__}. "
            "Pruning only supports EvaAttention (DINOv3). "
            "Standard ViT Attention uses a different forward that is incompatible."
        )

    _patch_eva_attention_forward(attn)

    return attn


def _update_bias_dims(
    attn: nn.Module,
    old_num_heads: int,
    head_dim: int,
    keep_heads: list[int],
    new_attn_dim: int,
) -> None:
    """Slice per-head bias tensors (q_bias, k_bias, v_bias) for EvaAttention."""
    for bias_name in ('q_bias', 'k_bias', 'v_bias'):
        bias = getattr(attn, bias_name, None)
        if bias is not None and bias.dim() == 1 and bias.shape[0] == old_num_heads * head_dim:
            head_indices = torch.tensor(
                [i for h in keep_heads for i in range(h * head_dim, (h + 1) * head_dim)],
                dtype=torch.long,
                device=bias.device,
            )
            setattr(attn, bias_name, nn.Parameter(bias.data[head_indices].clone()))


def _patch_eva_attention_forward(attn: nn.Module) -> None:
    """Monkey-patch EvaAttention.forward to use self.attn_dim for the reshape.

    EvaAttention.forward uses ``C`` (the input embed_dim) to reshape the attention
    output: ``x.reshape(B, N, C)``.  After pruning fewer heads the combined dimension
    ``num_heads * head_dim`` is smaller than ``C``, causing a shape mismatch.

    This replacement is a one-to-one copy of the upstream forward except the reshape
    line and an explicit ``F`` import so the unqualified name resolves.
    """
    cls_name = type(attn).__name__
    if cls_name != 'EvaAttention':
        return

    try:
        from timm.layers import apply_rot_embed_cat, resolve_self_attn_mask, maybe_add_mask  # type: ignore[import-untyped]
    except ImportError:
        return

    def patched_forward(
        self,
        x,
        rope=None,
        attn_mask=None,
        is_causal=False,
    ):
        B, N, C = x.shape
        gate = self.gate(x).sigmoid() if self.gate is not None else None

        if self.qkv is not None:
            if self.q_bias is None:
                qkv = self.qkv(x)
            else:
                qkv_bias = torch.cat((self.q_bias, self.k_bias, self.v_bias))
                if self.qkv_bias_separate:
                    qkv = self.qkv(x)
                    qkv += qkv_bias
                else:
                    qkv = F.linear(x, weight=self.qkv.weight, bias=qkv_bias)
            qkv = qkv.reshape(B, N, 3, self.num_heads, -1).permute(2, 0, 3, 1, 4)
            q, k, v = qkv.unbind(0)
        else:
            q = self.q_proj(x).reshape(B, N, self.num_heads, -1).transpose(1, 2)
            k = self.k_proj(x).reshape(B, N, self.num_heads, -1).transpose(1, 2)
            v = self.v_proj(x).reshape(B, N, self.num_heads, -1).transpose(1, 2)

        q, k = self.q_norm(q), self.k_norm(k)

        if rope is not None:
            npt = self.num_prefix_tokens
            half = getattr(self, 'rotate_half', False)
            q = torch.cat(
                [q[:, :, :npt, :], apply_rot_embed_cat(q[:, :, npt:, :], rope, half=half)],
                dim=2,
            ).type_as(v)
            k = torch.cat(
                [k[:, :, :npt, :], apply_rot_embed_cat(k[:, :, npt:, :], rope, half=half)],
                dim=2,
            ).type_as(v)

        if self.fused_attn:
            x = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=attn_mask,
                dropout_p=self.attn_drop.p if self.training else 0.0,
                is_causal=is_causal,
            )
        else:
            q = q * self.scale
            attn_mat = q @ k.transpose(-2, -1)
            attn_bias = resolve_self_attn_mask(N, attn_mat, attn_mask, is_causal=is_causal)
            attn_mat = maybe_add_mask(attn_mat, attn_bias)
            attn_mat = attn_mat.softmax(dim=-1)
            attn_mat = self.attn_drop(attn_mat)
            x = attn_mat @ v

        x = x.transpose(1, 2).reshape(B, N, self.attn_dim)
        x = self.norm(x)
        if gate is not None:
            x = x * gate
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

    attn.forward = types.MethodType(patched_forward, attn)


def get_keystone_head_indices(
    scores_df: "pd.DataFrame",
    pruning_ratio: float,
    per_layer_floor: int = 1,
) -> dict[int, list[int]]:
    """Convert head scores + pruning ratio into per-layer keep indices.

    Args:
        scores_df: DataFrame with columns [head_idx, layer, score].
        pruning_ratio: Fraction of heads to REMOVE (0.25 = keep 75%).
        per_layer_floor: Minimum heads to keep per layer.

    Returns:
        Dict mapping layer_idx -> list of head_in_layer indices to KEEP.
    """
    import pandas as pd
    if not isinstance(scores_df, pd.DataFrame):
        raise TypeError("scores_df must be a pandas DataFrame")

    total_heads = len(scores_df)
    to_remove = int(total_heads * pruning_ratio)
    keep_count = total_heads - to_remove

    if keep_count < per_layer_floor:
        raise ValueError(
            f"Global keep count ({keep_count}) < per-layer floor ({per_layer_floor}) "
            f"at pruning ratio {pruning_ratio}"
        )

    scores_sorted = scores_df.sort_values("score", ascending=False)

    layer_counts = scores_df.groupby("layer").size().to_dict()
    n_layers = len(layer_counts)

    floor_total = n_layers * per_layer_floor
    remaining = keep_count - floor_total

    keep_per_layer = {layer: per_layer_floor for layer in layer_counts}

    used = set()
    for layer in layer_counts:
        floor_heads = scores_sorted[scores_sorted["layer"] == layer].head(per_layer_floor)
        for h in floor_heads["head_in_layer"]:
            used.add((layer, h))

    remaining_heads = scores_sorted[~scores_sorted.apply(
        lambda r: (r["layer"], r["head_in_layer"]) in used, axis=1
    )]

    for _, row in remaining_heads.iterrows():
        if remaining <= 0:
            break
        layer = int(row["layer"])
        if keep_per_layer[layer] < layer_counts[layer]:
            keep_per_layer[layer] += 1
            remaining -= 1

    result = {}
    top_by_score = scores_sorted.groupby("layer").apply(
        lambda g: g.nlargest(keep_per_layer[g.name], "score")["head_in_layer"].tolist(),
        include_groups=False,
    )
    for layer, heads in top_by_score.items():
        result[int(layer)] = sorted(heads)

    return result
