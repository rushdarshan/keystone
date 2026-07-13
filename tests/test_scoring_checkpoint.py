from pathlib import Path

import torch

from src.keystone.config import PocConfig
from src.keystone.scoring import (
    _load_checkpoint,
    _write_checkpoint,
    build_checkpoint_fingerprint,
)


class DummyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.head = torch.nn.Linear(2, 2)


def _record():
    return {
        "head_idx": 0,
        "layer": 0,
        "head_in_layer": 0,
        "causal_score": 0.5,
        "score_std": 0.1,
        "score_sem": 0.1,
        "time_seconds": 1.0,
        "peak_memory_gb": 0.0,
    }


def test_checkpoint_fingerprint_changes_with_images_and_classifier():
    cfg = PocConfig(device="cpu")
    model = DummyModel()
    images = torch.zeros(2, 3, 2, 2)
    labels = torch.tensor([0, 1])

    baseline = build_checkpoint_fingerprint(model, images, labels, cfg)
    changed_images = images.clone()
    changed_images[0, 0, 0, 0] = 1
    assert build_checkpoint_fingerprint(model, changed_images, labels, cfg) != baseline

    with torch.no_grad():
        model.head.weight[0, 0] += 1
    assert build_checkpoint_fingerprint(model, images, labels, cfg) != baseline


def test_checkpoint_is_resumed_only_for_matching_fingerprint(tmp_path: Path):
    checkpoint = tmp_path / "scores.csv"
    _write_checkpoint(checkpoint, [_record()], fingerprint="matching")

    assert len(_load_checkpoint(checkpoint, fingerprint="matching")) == 1
    assert _load_checkpoint(checkpoint, fingerprint="different") == []
