import numpy as np
import pandas as pd
import pytest
import timm
import torch

from src.keystone.baselines import score_gradient, score_magnitude, score_random
from src.keystone.vit_adapters import discover_head_specs


@pytest.fixture(scope="module")
def model():
    m = timm.create_model("vit_base_patch16_224", pretrained=False, num_classes=1000)
    return m.eval()


@pytest.fixture(scope="module")
def head_specs(model):
    return discover_head_specs(model)


def test_magnitude_happy_path(model, head_specs):
    df = score_magnitude(model, head_specs)

    assert len(df) == len(head_specs) == 144
    assert set(df.columns) >= {"head_idx", "layer", "head_in_layer", "score"}
    assert (df["score"] >= 0).all()
    assert df["score"].is_monotonic_decreasing


def test_gradient_differs_from_magnitude(model, head_specs):
    images = torch.randn(8, 3, 224, 224)
    labels = torch.randint(0, 1000, (8,))

    df_mag = score_magnitude(model, head_specs)
    df_grad = score_gradient(model, head_specs, images, labels, "cpu")

    assert len(df_grad) == len(df_mag)
    assert set(df_grad.columns) >= {"head_idx", "layer", "head_in_layer", "score"}
    assert not np.allclose(df_mag["score"].values, df_grad["score"].values)


def test_random_is_permutation():
    n = 144
    df = score_random(n, seed=42)

    assert len(df) == n
    assert set(df.columns) >= {"head_idx", "score"}
    assert set(df["score"].tolist()) == set(range(n))


def test_random_different_seeds():
    n = 100
    df1 = score_random(n, seed=1)
    df2 = score_random(n, seed=2)

    mapping1 = dict(zip(df1["head_idx"], df1["score"]))
    mapping2 = dict(zip(df2["head_idx"], df2["score"]))
    assert mapping1 != mapping2


def test_gradient_handles_missing_grads(model, head_specs):
    frozen: list[torch.Tensor] = []
    for name, mod in model.named_modules():
        if hasattr(mod, "qkv") and mod.qkv is not None and hasattr(mod, "num_heads"):
            mod.qkv.weight.requires_grad = False
            frozen.append(mod.qkv.weight)

    try:
        images = torch.randn(3, 3, 224, 224)
        labels = torch.randint(0, 1000, (3,))
        df = score_gradient(model, head_specs, images, labels, "cpu")
        assert len(df) == len(head_specs)
        assert not df["score"].isna().any()
        assert not (df["score"] == float("inf")).any()
        assert (df["score"] >= 0).all()
    finally:
        for w in frozen:
            w.requires_grad = True


def test_magnitude_deterministic(model, head_specs):
    df1 = score_magnitude(model, head_specs)
    df2 = score_magnitude(model, head_specs)

    pd.testing.assert_frame_equal(df1, df2)


def test_gradient_produces_finite_values(model, head_specs):
    images = torch.randn(4, 3, 224, 224)
    labels = torch.randint(0, 1000, (4,))

    df = score_gradient(model, head_specs, images, labels, "cpu")

    assert len(df) == len(head_specs)
    assert not df["score"].isna().any()
    assert not (df["score"] == float("inf")).any()
