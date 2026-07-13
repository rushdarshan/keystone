"""Post-prune accuracy evaluation for Vision Transformers."""

from __future__ import annotations

import torch
import torch.nn as nn
from torch.utils.data import DataLoader


@torch.no_grad()
def evaluate_accuracy(
    model: nn.Module,
    dataloader: DataLoader,
    device: str | torch.device = "cuda",
) -> dict:
    """Evaluate top-1 and top-5 accuracy of a (possibly pruned) ViT.

    Args:
        model: ViT model in eval mode.
        dataloader: DataLoader yielding (images, labels) batches.
        device: Torch device.

    Returns:
        Dict with keys: top1_accuracy, top5_accuracy, total_samples.
    """
    model.eval()
    model.to(device)

    correct_top1 = 0
    correct_top5 = 0
    total = 0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        logits = model(images)

        # top-1
        _, pred_top1 = logits.max(dim=1)
        correct_top1 += (pred_top1 == labels).sum().item()

        # top-5
        _, pred_top5 = logits.topk(5, dim=1)
        correct_top5 += pred_top5.eq(labels.view(-1, 1)).any(dim=1).sum().item()

        total += labels.size(0)

    return {
        "top1_accuracy": correct_top1 / total if total > 0 else 0.0,
        "top5_accuracy": correct_top5 / total if total > 0 else 0.0,
        "total_samples": total,
    }


@torch.no_grad()
def measure_efficiency(
    model: nn.Module,
    sample_input: torch.Tensor,
    device: str | torch.device = "cuda",
    warmup: int = 10,
    measured: int = 50,
) -> dict:
    """Measure throughput, peak VRAM, and parameter count.

    Args:
        model: ViT model in eval mode.
        sample_input: Single sample tensor [1, 3, H, W].
        device: Torch device.
        warmup: Number of warmup forward passes.
        measured: Number of measured forward passes.

    Returns:
        Dict with keys: throughput_ips (inferences/sec), peak_vram_gb,
                        param_count_millions, flops_estimate (approximate).
    """
    model.eval()
    model.to(device)

    # Warmup
    sample = sample_input.to(device)
    for _ in range(warmup):
        _ = model(sample)

    # Sync and measure
    if device != "cpu" and torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()

    end = torch.cuda.Event(enable_timing=True) if device != "cpu" and torch.cuda.is_available() else None

    if end is not None:
        start = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(measured):
            _ = model(sample)
        end.record()
        torch.cuda.synchronize()
        elapsed = start.elapsed_time(end) / 1000.0  # seconds
        peak_vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
    else:
        import time
        t0 = time.perf_counter()
        for _ in range(measured):
            _ = model(sample)
        elapsed = time.perf_counter() - t0
        peak_vram = 0.0

    throughput = measured / elapsed if elapsed > 0 else 0.0
    param_count = sum(p.numel() for p in model.parameters()) / 1e6

    return {
        "throughput_ips": round(throughput, 2),
        "peak_vram_gb": round(peak_vram, 4),
        "param_count_millions": round(param_count, 2),
    }
