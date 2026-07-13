import json
from pathlib import Path

import torch


def discover_head_specs(model: torch.nn.Module) -> list[dict]:
    specs = []
    head_idx = 0
    for name, mod in model.named_modules():
        n_heads = _num_attention_heads(mod)
        if n_heads:
            parts = name.split(".")
            block_idx = None
            for i, p in enumerate(parts):
                if p == "blocks" and i + 1 < len(parts):
                    block_idx = int(parts[i + 1]) if i + 1 < len(parts) else None
                    break
            for h in range(n_heads):
                spec = {
                    "head_idx": head_idx,
                    "module_name": name,
                    "layer_idx": block_idx,
                    "head_in_layer": h,
                    "num_heads": n_heads,
                    "head_dim": getattr(mod, "head_dim", None),
                    "nnsight_accessor": (
                        f"{name}.source.F_scaled_dot_product_attention_0.output[:, {h}]"
                    ),
                }
                specs.append(spec)
                head_idx += 1
    return specs


def _num_attention_heads(module: torch.nn.Module) -> int | None:
    if isinstance(module, torch.nn.MultiheadAttention):
        return module.num_heads
    if hasattr(module, "num_heads") and (hasattr(module, "qkv") or hasattr(module, "q_proj")):
        return int(module.num_heads)
    return None


def print_hook_table(specs: list[dict]) -> None:
    print(f"  [adapters] discovered {len(specs)} attention heads")
    for s in specs[:5]:
        print(f"    layer={s['layer_idx']} head={s['head_in_layer']} "
              f"module={s['module_name']} accessor={s['nnsight_accessor']}")
    if len(specs) > 5:
        print(f"    ... and {len(specs) - 5} more")


def write_hook_manifest(specs: list[dict], output_dir: str) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    manifest = path / "head_hooks.json"
    manifest.write_text(json.dumps(specs, indent=2), encoding="utf-8")
    return manifest
