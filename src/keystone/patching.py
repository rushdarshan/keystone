from __future__ import annotations

from types import MethodType
from typing import Any

import torch
import torch.nn.functional as F


def build_corrupt_indices(clean_labels: torch.Tensor) -> torch.Tensor:
    indices = []
    n = clean_labels.shape[0]
    for i in range(n):
        indices.append(_find_corrupt_idx(clean_labels, i, n))
    return torch.tensor(indices, device=clean_labels.device, dtype=torch.long)


def patch_head(
    model: torch.nn.Module,
    head_spec: dict,
    clean_input: torch.Tensor,
    corrupt_input: torch.Tensor,
    device: str = "cuda",
) -> torch.Tensor:
    """Replace one clean attention-head output with the paired corrupt output."""
    module = _get_module(model, head_spec["module_name"])
    head_idx = int(head_spec["head_in_layer"])
    original_forward = module.forward
    captured: dict[str, torch.Tensor] = {}

    def capture_forward(attn_module: torch.nn.Module, x: torch.Tensor, *args: Any, **kwargs: Any) -> torch.Tensor:
        return _attention_forward(attn_module, x, args, kwargs, capture=captured, head_idx=head_idx)

    def patch_forward(attn_module: torch.nn.Module, x: torch.Tensor, *args: Any, **kwargs: Any) -> torch.Tensor:
        replacement = captured.get("head")
        if replacement is None:
            raise RuntimeError("Corrupt head activation was not captured before patching")
        return _attention_forward(attn_module, x, args, kwargs, replacement=replacement, head_idx=head_idx)

    try:
        module.forward = MethodType(capture_forward, module)
        with torch.no_grad():
            model(corrupt_input.to(device))

        module.forward = MethodType(patch_forward, module)
        with torch.no_grad():
            return model(clean_input.to(device))
    finally:
        module.forward = original_forward


def output_difference(
    clean_output: torch.Tensor,
    patched_output: torch.Tensor,
    metric: str,
    *,
    target_labels: torch.Tensor | None = None,
) -> torch.Tensor:
    if metric == "kl_div":
        clean_log_probs = F.log_softmax(clean_output, dim=-1)
        patched_log_probs = F.log_softmax(patched_output, dim=-1)
        return F.kl_div(patched_log_probs, clean_log_probs.exp(), reduction="none").sum(dim=-1)

    if metric == "feature_diff":
        target = clean_output.detach().abs().argmax(dim=-1)
    elif metric == "logit_diff":
        if target_labels is None:
            raise ValueError("logit_diff requires target labels")
        target = target_labels.to(device=clean_output.device, dtype=torch.long)
        if target.shape[0] != clean_output.shape[0]:
            raise ValueError("target labels must match the output batch size")
    else:
        raise ValueError(f"unsupported patching metric: {metric}")
    row = torch.arange(clean_output.shape[0], device=clean_output.device)
    return (clean_output[row, target] - patched_output[row, target]).abs()


def _find_corrupt_idx(labels: torch.Tensor, current_idx: int, n: int) -> int:
    current_class = labels[current_idx].item()
    for offset in range(1, n):
        candidate = (current_idx + offset) % n
        if labels[candidate].item() != current_class:
            return candidate
    return (current_idx + 1) % n


def _get_module(model: torch.nn.Module, module_name: str) -> torch.nn.Module:
    modules = dict(model.named_modules())
    if module_name not in modules:
        raise RuntimeError(f"Could not find module {module_name}")
    return modules[module_name]


def _attention_forward(
    module: torch.nn.Module,
    x: torch.Tensor,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    *,
    head_idx: int,
    capture: dict[str, torch.Tensor] | None = None,
    replacement: torch.Tensor | None = None,
) -> torch.Tensor:
    rope = kwargs.get("rope", args[0] if len(args) > 0 else None)
    attn_mask = kwargs.get("attn_mask", args[1] if len(args) > 1 else None)
    is_causal = kwargs.get("is_causal", args[2] if len(args) > 2 else False)

    batch, tokens, channels = x.shape
    gate = module.gate(x).sigmoid() if getattr(module, "gate", None) is not None else None

    if getattr(module, "qkv", None) is not None:
        qkv = _compute_qkv(module, x)
        qkv = qkv.reshape(batch, tokens, 3, module.num_heads, -1).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)
    else:
        q = module.q_proj(x).reshape(batch, tokens, module.num_heads, -1).transpose(1, 2)
        k = module.k_proj(x).reshape(batch, tokens, module.num_heads, -1).transpose(1, 2)
        v = module.v_proj(x).reshape(batch, tokens, module.num_heads, -1).transpose(1, 2)

    q, k = module.q_norm(q), module.k_norm(k)
    if rope is not None:
        q, k = _apply_rope(module, q, k, v, rope)

    dropout = module.attn_drop.p if module.training else 0.0
    head_outputs = F.scaled_dot_product_attention(
        q,
        k,
        v,
        attn_mask=attn_mask,
        dropout_p=dropout,
        is_causal=is_causal,
    )

    if capture is not None:
        capture["head"] = head_outputs[:, head_idx].detach()
    if replacement is not None:
        head_outputs = head_outputs.clone()
        head_outputs[:, head_idx] = replacement.to(device=head_outputs.device, dtype=head_outputs.dtype)

    attn_dim = getattr(module, "attn_dim", channels)
    x = head_outputs.transpose(1, 2).reshape(batch, tokens, attn_dim)
    x = module.norm(x)
    if gate is not None:
        x = x * gate
    x = module.proj(x)
    return module.proj_drop(x)


def _compute_qkv(module: torch.nn.Module, x: torch.Tensor) -> torch.Tensor:
    if getattr(module, "q_bias", None) is None:
        return module.qkv(x)

    qkv_bias = torch.cat((module.q_bias, module.k_bias, module.v_bias))
    if getattr(module, "qkv_bias_separate", False):
        qkv = module.qkv(x)
        return qkv + qkv_bias
    return F.linear(x, weight=module.qkv.weight, bias=qkv_bias)


def _apply_rope(
    module: torch.nn.Module,
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    rope: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    try:
        from timm.models.eva import apply_rot_embed_cat
    except ImportError as exc:
        raise RuntimeError("RoPE attention patching requires timm.models.eva.apply_rot_embed_cat") from exc

    npt = getattr(module, "num_prefix_tokens", 0)
    half = getattr(module, "rotate_half", False)
    q = torch.cat([q[:, :, :npt, :], apply_rot_embed_cat(q[:, :, npt:, :], rope, half=half)], dim=2).type_as(v)
    k = torch.cat([k[:, :, :npt, :], apply_rot_embed_cat(k[:, :, npt:, :], rope, half=half)], dim=2).type_as(v)
    return q, k
