import random
import json
import platform
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import torch


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def log_memory(label: str = "") -> float:
    if not torch.cuda.is_available():
        return 0.0
    gb = torch.cuda.max_memory_allocated() / 1e9
    if label:
        print(f"  [mem] {label}: {gb:.2f} GB")
    return gb


def collect_environment() -> dict:
    try:
        import timm
    except ImportError:
        timm = None
    try:
        import nnsight
    except ImportError:
        nnsight = None

    gpu = {}
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        gpu = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_gb": round(props.total_memory / 1e9, 2),
        }

    return {
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "timm_version": getattr(timm, "__version__", None) if timm else None,
        "nnsight_version": getattr(nnsight, "__version__", None) if nnsight else None,
        **gpu,
    }


def write_environment(output_dir: str) -> dict:
    env = collect_environment()
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    return env


def write_failure_report(output_dir: str, error: BaseException, model: torch.nn.Module | None = None) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    modules = []
    if model is not None:
        modules = [name for name, _ in list(model.named_modules())[:20]]

    body = [
        "# CausalHeadRank PoC Failure Report",
        "",
        "## Error",
        "",
        f"```text\n{type(error).__name__}: {error}\n```",
        "",
        "## Environment",
        "",
        "```json",
        json.dumps(collect_environment(), indent=2),
        "```",
        "",
        "## First 20 Model Modules",
        "",
        "```text",
        "\n".join(modules) if modules else "model unavailable",
        "```",
        "",
        "## Attempted Fixes",
        "",
        "- Tried configured DINOv3 model.",
        "- Tried configured DINOv2 fallback when model loading failed.",
        "- Checked attention modules for `num_heads` plus `qkv` or split q/k/v projections.",
    ]
    report = path / "failure_report.md"
    report.write_text("\n".join(body), encoding="utf-8")
    return report


def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"


@contextmanager
def timer(label: str = ""):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    if label:
        print(f"  [time] {label}: {format_time(elapsed)}")
