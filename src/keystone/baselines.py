from __future__ import annotations

import numpy as np
import pandas as pd
import torch


def score_magnitude(model: torch.nn.Module, head_specs: list[dict]) -> pd.DataFrame:
    records: list[dict] = []
    module_cache: dict[str, torch.nn.Module] = {}

    for spec in head_specs:
        name = spec["module_name"]
        if name not in module_cache:
            module_cache[name] = dict(model.named_modules())[name]
        mod = module_cache[name]

        h = int(spec["head_in_layer"])
        n_heads = int(spec["num_heads"])
        hd = _resolve_head_dim(spec, mod)

        if hasattr(mod, "qkv") and mod.qkv is not None:
            w = mod.qkv.weight
            q_s, q_e = h * hd, (h + 1) * hd
            k_s, k_e = n_heads * hd + h * hd, n_heads * hd + (h + 1) * hd
            v_s, v_e = 2 * n_heads * hd + h * hd, 2 * n_heads * hd + (h + 1) * hd
            q_norm = w[q_s:q_e, :].norm(p=2).item()
            k_norm = w[k_s:k_e, :].norm(p=2).item()
            v_norm = w[v_s:v_e, :].norm(p=2).item()
        else:
            q_norm = mod.q_proj.weight[h * hd : (h + 1) * hd, :].norm(p=2).item()
            k_norm = mod.k_proj.weight[h * hd : (h + 1) * hd, :].norm(p=2).item()
            v_norm = mod.v_proj.weight[h * hd : (h + 1) * hd, :].norm(p=2).item()

        proj_norm = mod.proj.weight[:, h * hd : (h + 1) * hd].norm(p=2).item()

        score = (q_norm**2 + k_norm**2 + v_norm**2 + proj_norm**2) ** 0.5
        records.append(
            {
                "head_idx": spec["head_idx"],
                "layer": spec["layer_idx"],
                "head_in_layer": spec["head_in_layer"],
                "score": round(score, 6),
            }
        )

    return pd.DataFrame(records).sort_values("score", ascending=False).reset_index(drop=True)


def score_gradient(
    model: torch.nn.Module,
    head_specs: list[dict],
    images: torch.Tensor,
    labels: torch.Tensor,
    device: str,
) -> pd.DataFrame:
    criterion = torch.nn.CrossEntropyLoss()
    unique_names = {s["module_name"] for s in head_specs}
    module_cache = {name: dict(model.named_modules())[name] for name in unique_names}

    head_scores = {s["head_idx"]: 0.0 for s in head_specs}

    for i in range(images.shape[0]):
        model.zero_grad()

        img = images[i : i + 1].to(device)
        lbl = labels[i : i + 1].to(device)

        output = model(img)
        loss = criterion(output, lbl)
        loss.backward()

        for spec in head_specs:
            mod = module_cache[spec["module_name"]]
            h = int(spec["head_in_layer"])
            n_heads = int(spec["num_heads"])
            hd = _resolve_head_dim(spec, mod)

            if hasattr(mod, "qkv") and mod.qkv is not None:
                w = mod.qkv.weight
                g = mod.qkv.weight.grad
                q_s, q_e = h * hd, (h + 1) * hd
                k_s, k_e = n_heads * hd + h * hd, n_heads * hd + (h + 1) * hd
                v_s, v_e = 2 * n_heads * hd + h * hd, 2 * n_heads * hd + (h + 1) * hd

                q_w = w[q_s:q_e, :]
                k_w = w[k_s:k_e, :]
                v_w = w[v_s:v_e, :]
                q_g = g[q_s:q_e, :] if g is not None else torch.zeros_like(q_w)
                k_g = g[k_s:k_e, :] if g is not None else torch.zeros_like(k_w)
                v_g = g[v_s:v_e, :] if g is not None else torch.zeros_like(v_w)
            else:
                s, e = h * hd, (h + 1) * hd
                q_w = mod.q_proj.weight[s:e, :]
                k_w = mod.k_proj.weight[s:e, :]
                v_w = mod.v_proj.weight[s:e, :]
                q_g = mod.q_proj.weight.grad
                k_g = mod.k_proj.weight.grad
                v_g = mod.v_proj.weight.grad
                q_g = q_g[s:e, :] if q_g is not None else torch.zeros_like(q_w)
                k_g = k_g[s:e, :] if k_g is not None else torch.zeros_like(k_w)
                v_g = v_g[s:e, :] if v_g is not None else torch.zeros_like(v_w)

            p_s, p_e = h * hd, (h + 1) * hd
            proj_w = mod.proj.weight[:, p_s:p_e]
            proj_g = mod.proj.weight.grad
            proj_g = proj_g[:, p_s:p_e] if proj_g is not None else torch.zeros_like(proj_w)

            taylor_qkv = (q_w * q_g).norm(p=2).item() ** 2
            taylor_qkv += (k_w * k_g).norm(p=2).item() ** 2
            taylor_qkv += (v_w * v_g).norm(p=2).item() ** 2
            taylor_proj = (proj_w * proj_g).norm(p=2).item() ** 2

            head_scores[spec["head_idx"]] += (taylor_qkv + taylor_proj) ** 0.5

    n = max(images.shape[0], 1)
    records = []
    for spec in head_specs:
        records.append(
            {
                "head_idx": spec["head_idx"],
                "layer": spec["layer_idx"],
                "head_in_layer": spec["head_in_layer"],
                "score": round(head_scores[spec["head_idx"]] / n, 6),
            }
        )

    return pd.DataFrame(records).sort_values("score", ascending=False).reset_index(drop=True)


def score_random(n_heads: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    scores = rng.permutation(n_heads).tolist()
    records = [{"head_idx": i, "score": float(scores[i])} for i in range(n_heads)]
    return pd.DataFrame(records).sort_values("score", ascending=False).reset_index(drop=True)


def _resolve_head_dim(spec: dict, mod: torch.nn.Module) -> int:
    hd = spec.get("head_dim")
    if hd is not None:
        return int(hd)
    n_heads = int(spec["num_heads"])
    if hasattr(mod, "qkv") and mod.qkv is not None:
        return mod.qkv.out_features // (3 * n_heads)
    return mod.q_proj.out_features // n_heads
