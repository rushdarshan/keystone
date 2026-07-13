from __future__ import annotations

from collections.abc import Sequence

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, Subset


@torch.inference_mode()
def extract_features(
    model: torch.nn.Module,
    dataset: Dataset,
    indices: Sequence[int],
    *,
    batch_size: int,
    device: str,
    num_workers: int = 0,
) -> tuple[torch.Tensor, torch.Tensor]:
    loader = DataLoader(
        Subset(dataset, list(indices)),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )
    feature_batches: list[torch.Tensor] = []
    label_batches: list[torch.Tensor] = []
    model.eval()
    for images, labels in loader:
        features = model(images.to(device))
        if not isinstance(features, torch.Tensor) or features.ndim != 2:
            raise RuntimeError(f"expected [batch, features] backbone output, got {type(features)}")
        feature_batches.append(features.detach().float().cpu())
        label_batches.append(labels.detach().long().cpu())
    return torch.cat(feature_batches), torch.cat(label_batches)


def fit_linear_probe_from_features(
    train_features: torch.Tensor,
    train_labels: torch.Tensor,
    val_features: torch.Tensor,
    val_labels: torch.Tensor,
    *,
    num_classes: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    seed: int,
    device: str,
) -> tuple[torch.nn.Linear, float]:
    if train_features.ndim != 2 or val_features.ndim != 2:
        raise ValueError("probe features must be rank-2 tensors")
    if train_features.shape[1] != val_features.shape[1]:
        raise ValueError("train and validation feature dimensions must match")

    torch.manual_seed(seed)
    train_features = train_features.to(device=device, dtype=torch.float32)
    train_labels = train_labels.to(device=device, dtype=torch.long)
    val_features = val_features.to(device=device, dtype=torch.float32)
    val_labels = val_labels.to(device=device, dtype=torch.long)

    classifier = torch.nn.Linear(train_features.shape[1], num_classes).to(device)
    optimizer = torch.optim.AdamW(
        classifier.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )
    classifier.train()
    for _ in range(epochs):
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(classifier(train_features), train_labels)
        loss.backward()
        optimizer.step()

    classifier.eval()
    with torch.no_grad():
        predictions = classifier(val_features).argmax(dim=-1)
        accuracy = float((predictions == val_labels).float().mean().item())
    return classifier, accuracy


def install_linear_probe(model: torch.nn.Module, classifier: torch.nn.Linear) -> None:
    if not hasattr(model, "head"):
        raise RuntimeError("model does not expose a replaceable classifier head")
    expected_features = getattr(model, "num_features", classifier.in_features)
    if classifier.in_features != expected_features:
        raise ValueError(
            f"probe expects {classifier.in_features} features but model reports {expected_features}"
        )
    model.head = classifier
    model.num_classes = classifier.out_features
