import pytest
import torch

from src.keystone.patching import output_difference


def test_logit_difference_uses_the_ground_truth_class():
    clean = torch.tensor([[0.0, 3.0, 1.0], [4.0, 0.0, 2.0]])
    patched = torch.tensor([[0.0, 1.0, 5.0], [1.0, 0.0, 3.0]])
    labels = torch.tensor([1, 0])

    scores = output_difference(clean, patched, "logit_diff", target_labels=labels)

    torch.testing.assert_close(scores, torch.tensor([2.0, 3.0]))


def test_logit_difference_requires_target_labels():
    output = torch.zeros(2, 3)

    with pytest.raises(ValueError, match="target labels"):
        output_difference(output, output, "logit_diff")


def test_kl_divergence_remains_label_free():
    clean = torch.tensor([[1.0, 2.0]])
    patched = torch.tensor([[2.0, 1.0]])

    score = output_difference(clean, patched, "kl_div")

    assert score.shape == (1,)
    assert score.item() > 0
