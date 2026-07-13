import torch

from src.keystone.vit_adapters import discover_head_specs


class Attention(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.num_heads = 2
        self.head_dim = 4
        self.qkv = torch.nn.Linear(8, 24)


class Block(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.attn = Attention()


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks = torch.nn.ModuleList([Block()])


def test_head_specs_use_real_nnsight_source_operation_accessor():
    specs = discover_head_specs(Model())

    assert specs[0]["nnsight_accessor"] == (
        "blocks.0.attn.source.F_scaled_dot_product_attention_0.output[:, 0]"
    )
    assert specs[1]["nnsight_accessor"] == (
        "blocks.0.attn.source.F_scaled_dot_product_attention_0.output[:, 1]"
    )
