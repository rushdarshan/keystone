import pytest
import torch
import timm

from src.keystone.pruning import prune_heads


NUM_LAYERS = 12
NUM_HEADS = 12
HEAD_DIM = 64
EMBED_DIM = 768


def _make_model():
    return timm.create_model("vit_base_patch16_dinov3", pretrained=False)


def _make_images(batch: int = 2):
    return torch.randn(batch, 3, 224, 224)


def test_prune_half_heads_per_layer():
    model = _make_model()
    images = _make_images()
    keep_indices = {i: list(range(6)) for i in range(NUM_LAYERS)}

    with torch.no_grad():
        out_before = model(images)

    result = prune_heads(model, keep_indices)

    assert result is model

    for i in range(NUM_LAYERS):
        attn = model.blocks[i].attn
        assert attn.num_heads == 6
        assert attn.qkv.out_features == 3 * 6 * HEAD_DIM
        assert attn.qkv.weight.shape == (3 * 6 * HEAD_DIM, EMBED_DIM)
        assert attn.proj.in_features == 6 * HEAD_DIM
        assert attn.proj.weight.shape == (EMBED_DIM, 6 * HEAD_DIM)

    with torch.no_grad():
        out_after = model(images)

    assert out_after.shape == out_before.shape


def test_keep_all_heads_noop():
    model = _make_model()
    attn = model.blocks[0].attn

    original_qkv_weight = attn.qkv.weight.data.clone()
    original_proj_weight = attn.proj.weight.data.clone()
    original_qkv_bias = attn.qkv.bias.data.clone() if attn.qkv.bias is not None else None
    original_proj_bias = attn.proj.bias.data.clone() if attn.proj.bias is not None else None
    original_num_heads = attn.num_heads

    keep_indices = {0: list(range(NUM_HEADS))}
    prune_heads(model, keep_indices)

    assert attn.num_heads == original_num_heads
    assert torch.equal(attn.qkv.weight.data, original_qkv_weight)
    assert torch.equal(attn.proj.weight.data, original_proj_weight)
    if original_qkv_bias is not None:
        assert torch.equal(attn.qkv.bias.data, original_qkv_bias)
    if original_proj_bias is not None:
        assert torch.equal(attn.proj.bias.data, original_proj_bias)


def test_empty_keep_list_raises():
    model = _make_model()

    with pytest.raises(ValueError, match="Must keep at least 1 attention head"):
        prune_heads(model, {0: []})


def test_out_of_range_head_index_raises():
    model = _make_model()

    with pytest.raises(ValueError, match="out of range"):
        prune_heads(model, {0: [12]})

    model2 = _make_model()
    with pytest.raises(ValueError, match="out of range"):
        prune_heads(model2, {0: [-1]})


def test_prune_heads_returns_same_object():
    model = _make_model()
    keep_indices = {0: [0, 1, 2]}
    result = prune_heads(model, keep_indices)
    assert result is model


def test_forward_output_shape():
    model = _make_model()
    images = _make_images(batch=4)

    keep_indices = {i: [0, 2, 4, 6, 8, 10] for i in range(NUM_LAYERS)}
    prune_heads(model, keep_indices)

    with torch.no_grad():
        output = model(images)

    assert output.shape[0] == images.shape[0]
    assert output.shape == (4, model.embed_dim)
