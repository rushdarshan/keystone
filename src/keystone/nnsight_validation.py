from __future__ import annotations

from typing import Any

import torch

from src.keystone.patching import patch_head


def patch_head_with_nnsight(
    model: torch.nn.Module,
    head_spec: dict,
    clean_input: torch.Tensor,
    corrupt_input: torch.Tensor,
    device: str,
) -> dict[str, torch.Tensor]:
    from nnsight import NNsight

    attention = dict(model.named_modules()).get(head_spec["module_name"])
    if attention is None:
        raise RuntimeError(f"could not find attention module {head_spec['module_name']}")
    if not getattr(attention, "fused_attn", False):
        raise RuntimeError("nnsight head patching requires fused scaled-dot-product attention")

    traced_model = NNsight(model)
    traced_attention = _resolve_envoy(traced_model, head_spec["module_name"])
    try:
        sdpa = traced_attention.source.F_scaled_dot_product_attention_0
    except AttributeError as exc:
        raise RuntimeError(
            "NNsight did not expose F_scaled_dot_product_attention_0 for the attention module"
        ) from exc

    head_idx = int(head_spec["head_in_layer"])
    with traced_model.trace(corrupt_input.to(device)):
        corrupt_head_saved = sdpa.output[:, head_idx].detach().clone().save()
        traced_corrupt_saved = traced_model.output.detach().clone().save()

    corrupt_head = _saved_tensor(corrupt_head_saved)
    traced_corrupt = _saved_tensor(traced_corrupt_saved)
    with traced_model.trace(clean_input.to(device)):
        clean_head_saved = sdpa.output[:, head_idx].detach().clone().save()
        sdpa.output[:, head_idx] = corrupt_head
        patched_saved = traced_model.output.detach().clone().save()

    return {
        "clean_head": _saved_tensor(clean_head_saved),
        "corrupt_head": corrupt_head,
        "traced_corrupt": traced_corrupt,
        "patched_output": _saved_tensor(patched_saved),
    }


def validate_nnsight_equivalence(
    model: torch.nn.Module,
    head_spec: dict,
    clean_input: torch.Tensor,
    corrupt_input: torch.Tensor,
    device: str,
    *,
    rtol: float = 1e-5,
    atol: float = 1e-6,
) -> dict[str, Any]:
    with torch.inference_mode():
        baseline_corrupt = model(corrupt_input.to(device)).detach()
        direct_patched = patch_head(model, head_spec, clean_input, corrupt_input, device).detach()

    traced = patch_head_with_nnsight(model, head_spec, clean_input, corrupt_input, device)
    traced_corrupt = traced["traced_corrupt"]
    nnsight_patched = traced["patched_output"]
    head_difference = (traced["clean_head"] - traced["corrupt_head"]).abs()
    baseline_difference = (baseline_corrupt - traced_corrupt).abs()
    patched_difference = (direct_patched - nnsight_patched).abs()

    baseline_equivalent = torch.allclose(baseline_corrupt, traced_corrupt, rtol=rtol, atol=atol)
    patched_equivalent = torch.allclose(direct_patched, nnsight_patched, rtol=rtol, atol=atol)
    non_vacuous = float(head_difference.max().item()) > atol
    return {
        "passed": bool(baseline_equivalent and patched_equivalent and non_vacuous),
        "module_name": head_spec["module_name"],
        "head_in_layer": int(head_spec["head_in_layer"]),
        "nnsight_accessor": head_spec["nnsight_accessor"],
        "captured_head_shape": list(traced["corrupt_head"].shape),
        "baseline_vs_traced_max_abs": float(baseline_difference.max().item()),
        "direct_vs_nnsight_max_abs": float(patched_difference.max().item()),
        "direct_vs_nnsight_mean_abs": float(patched_difference.mean().item()),
        "clean_vs_corrupt_head_max_abs": float(head_difference.max().item()),
        "rtol": rtol,
        "atol": atol,
    }


def _resolve_envoy(model: Any, module_name: str) -> Any:
    current = model
    for part in module_name.split("."):
        current = current[int(part)] if part.isdigit() else getattr(current, part)
    return current


def _saved_tensor(value: Any) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.detach()
    saved = getattr(value, "value", None)
    if isinstance(saved, torch.Tensor):
        return saved.detach()
    raise RuntimeError(f"NNsight saved value did not resolve to a tensor: {type(value).__name__}")
