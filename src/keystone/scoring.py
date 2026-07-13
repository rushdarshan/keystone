from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import pandas as pd
import torch

from src.keystone.config import PocConfig
from src.keystone.patching import build_corrupt_indices, output_difference, patch_head
from src.keystone.utils import log_memory


def score_all_heads(
    model: torch.nn.Module,
    head_specs: list[dict],
    images: torch.Tensor,
    labels: torch.Tensor,
    cfg: PocConfig,
    *,
    checkpoint_name: str = "head_scores.csv",
) -> pd.DataFrame:
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / checkpoint_name
    fingerprint = build_checkpoint_fingerprint(model, images, labels, cfg)
    records = _load_checkpoint(checkpoint_path, fingerprint=fingerprint)
    completed = {int(r["head_idx"]) for r in records}

    corrupt_indices = build_corrupt_indices(labels)
    clean_outputs = _clean_output_cache(model, images, cfg)

    for local_idx, spec in enumerate(head_specs):
        head_idx = int(spec.get("head_idx", local_idx))
        if head_idx in completed:
            continue

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

        start = time.perf_counter()
        per_sample_scores: list[torch.Tensor] = []

        for start_idx in range(0, images.shape[0], cfg.batch_size):
            end_idx = min(start_idx + cfg.batch_size, images.shape[0])
            clean_batch = images[start_idx:end_idx]
            corrupt_batch = images[corrupt_indices[start_idx:end_idx]]
            clean_batch_outputs = clean_outputs[start_idx:end_idx]
            patched_outputs = patch_head(model, spec, clean_batch, corrupt_batch, cfg.device)
            target_labels = labels[start_idx:end_idx] if cfg.metric == "logit_diff" else None
            per_sample_scores.append(
                output_difference(
                    clean_batch_outputs,
                    patched_outputs,
                    cfg.metric,
                    target_labels=target_labels,
                ).detach().cpu()
            )

        scores = torch.cat(per_sample_scores)
        elapsed = time.perf_counter() - start
        peak_mem = log_memory(f"head {head_idx} (layer={spec['layer_idx']}, h={spec['head_in_layer']})")

        record = {
            "head_idx": head_idx,
            "layer": spec["layer_idx"],
            "head_in_layer": spec["head_in_layer"],
            "causal_score": float(scores.mean().item()),
            "score_std": float(scores.std(unbiased=False).item()),
            "score_sem": float((scores.std(unbiased=False) / max(scores.numel() ** 0.5, 1)).item()),
            "time_seconds": elapsed,
            "peak_memory_gb": peak_mem,
        }
        records.append(record)

        if len(records) % cfg.checkpoint_every == 0 or len(records) == len(head_specs):
            _write_checkpoint(checkpoint_path, records, fingerprint=fingerprint)
            print(f"  [scoring] checkpointed {len(records)}/{len(head_specs)} heads")

    return pd.DataFrame(records).sort_values("head_idx").reset_index(drop=True)


def _clean_output_cache(model: torch.nn.Module, images: torch.Tensor, cfg: PocConfig) -> torch.Tensor:
    outputs = []
    with torch.no_grad():
        for start_idx in range(0, images.shape[0], cfg.batch_size):
            end_idx = min(start_idx + cfg.batch_size, images.shape[0])
            outputs.append(model(images[start_idx:end_idx].to(cfg.device)).detach())
    return torch.cat(outputs, dim=0)


def build_checkpoint_fingerprint(
    model: torch.nn.Module,
    images: torch.Tensor,
    labels: torch.Tensor,
    cfg: PocConfig,
) -> str:
    digest = hashlib.sha256(b"keystone-class-aware-v2")
    fingerprint_config = {
        "batch_size": cfg.batch_size,
        "corruption_strategy": cfg.corruption_strategy,
        "metric": cfg.metric,
        "model_name": cfg.model_name,
        "pretrained": cfg.pretrained,
    }
    digest.update(json.dumps(fingerprint_config, sort_keys=True).encode("utf-8"))
    _update_tensor_hash(digest, images)
    _update_tensor_hash(digest, labels)

    head = getattr(model, "head", None)
    if isinstance(head, torch.nn.Module):
        for name, tensor in sorted(head.state_dict().items()):
            digest.update(name.encode("utf-8"))
            _update_tensor_hash(digest, tensor)
    return digest.hexdigest()


def _update_tensor_hash(digest: hashlib._Hash, tensor: torch.Tensor) -> None:
    value = tensor.detach().cpu().contiguous()
    digest.update(str(value.dtype).encode("ascii"))
    digest.update(str(tuple(value.shape)).encode("ascii"))
    digest.update(value.numpy().tobytes())


def _metadata_path(checkpoint_path: Path) -> Path:
    return checkpoint_path.with_suffix(".meta.json")


def _load_checkpoint(checkpoint_path: Path, *, fingerprint: str) -> list[dict]:
    if not checkpoint_path.exists():
        return []
    metadata_path = _metadata_path(checkpoint_path)
    if not metadata_path.exists():
        print(f"  [scoring] ignoring legacy checkpoint without metadata: {checkpoint_path}")
        return []
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("fingerprint") != fingerprint:
        print(f"  [scoring] ignoring stale checkpoint for different inputs: {checkpoint_path}")
        return []
    df = pd.read_csv(checkpoint_path)
    print(f"  [scoring] resuming {len(df)} completed heads from {checkpoint_path}")
    return df.to_dict("records")


def _atomic_replace(src: Path, dst: Path, *, retries: int = 3, delay: float = 0.1) -> None:
    for attempt in range(retries):
        try:
            os.replace(src, dst)
            return
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def _write_checkpoint(checkpoint_path: Path, records: list[dict], *, fingerprint: str) -> None:
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records).sort_values("head_idx")
    temporary_path = checkpoint_path.with_suffix(checkpoint_path.suffix + ".tmp")
    frame.to_csv(temporary_path, index=False)

    metadata = {
        "fingerprint": fingerprint,
        "record_count": len(records),
        "schema": "keystone-head-scores-v2",
    }
    metadata_path = _metadata_path(checkpoint_path)
    temporary_metadata = metadata_path.with_suffix(metadata_path.suffix + ".tmp")
    temporary_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    _atomic_replace(temporary_path, checkpoint_path)
    _atomic_replace(temporary_metadata, metadata_path)
