import timm
import pytest
import torch
from torch.utils.data import DataLoader, Subset
from torchvision.datasets import CIFAR100

from src.keystone.data import cifar100_transform
from src.keystone.evaluation import evaluate_accuracy, measure_efficiency


def _model_with_cifar_head():
    model = timm.create_model("vit_small_patch16_dinov3", pretrained=False)
    model.reset_classifier(100)
    return model


def _cifar100_loader(n: int = 100, batch_size: int = 16):
    transform = cifar100_transform()
    ds = CIFAR100(root="data", train=False, download=True, transform=transform)
    subset = Subset(ds, range(min(n, len(ds))))
    return DataLoader(subset, batch_size=batch_size, shuffle=False, num_workers=0)


@pytest.fixture(scope="module")
def model():
    return _model_with_cifar_head()


@pytest.fixture(scope="module")
def cifar100_loader():
    return _cifar100_loader(n=100, batch_size=16)


def test_evaluate_accuracy_returns_expected_keys(model, cifar100_loader):
    result = evaluate_accuracy(model, cifar100_loader, device="cpu")
    assert set(result.keys()) == {"top1_accuracy", "top5_accuracy", "total_samples"}


def test_evaluate_accuracy_total_samples(model, cifar100_loader):
    result = evaluate_accuracy(model, cifar100_loader, device="cpu")
    assert result["total_samples"] == 100


def test_evaluate_accuracy_values_in_range(model):
    loader = _cifar100_loader(n=10, batch_size=10)
    result = evaluate_accuracy(model, loader, device="cpu")
    assert 0.0 <= result["top1_accuracy"] <= 1.0
    assert 0.0 <= result["top5_accuracy"] <= 1.0
    assert result["total_samples"] == 10


def test_evaluate_accuracy_empty_dataloader_returns_zero(model):
    empty_loader = DataLoader([], batch_size=1)
    result = evaluate_accuracy(model, empty_loader, device="cpu")
    assert result["top1_accuracy"] == 0.0
    assert result["top5_accuracy"] == 0.0
    assert result["total_samples"] == 0


def test_measure_efficiency(model):
    sample = torch.randn(1, 3, 224, 224)
    result = measure_efficiency(model, sample, device="cpu", warmup=2, measured=5)
    assert result["throughput_ips"] > 0
    assert result["peak_vram_gb"] >= 0
    assert result["param_count_millions"] > 0


def test_model_stays_in_eval_mode(model, cifar100_loader):
    model.train()
    evaluate_accuracy(model, cifar100_loader, device="cpu")
    assert not model.training


def test_measure_efficiency_model_stays_in_eval_mode(model):
    model.train()
    measure_efficiency(model, torch.randn(1, 3, 224, 224), device="cpu", warmup=1, measured=2)
    assert not model.training
