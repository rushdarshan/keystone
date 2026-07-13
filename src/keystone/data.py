from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Sequence


def cifar100_transform():
    from torchvision import transforms

    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def stratified_subset_indices(
    targets: Sequence[int],
    n_samples: int,
    seed: int,
    *,
    composition_seed: int = 0,
) -> list[int]:
    """Sample balanced class counts while varying examples across seeds."""
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    if n_samples > len(targets):
        raise ValueError(f"dataset only contains {len(targets)} examples, requested {n_samples}")

    by_class: dict[int, list[int]] = defaultdict(list)
    for index, target in enumerate(targets):
        by_class[int(target)].append(index)
    if not by_class:
        raise ValueError("targets must not be empty")

    class_order = sorted(by_class)
    random.Random(composition_seed).shuffle(class_order)

    counts = {label: 0 for label in class_order}
    remaining = n_samples
    while remaining:
        allocated = False
        for label in class_order:
            if counts[label] >= len(by_class[label]):
                continue
            counts[label] += 1
            remaining -= 1
            allocated = True
            if remaining == 0:
                break
        if not allocated:
            raise ValueError("could not allocate the requested stratified subset")

    rng = random.Random(seed)
    selected: list[int] = []
    for label in class_order:
        candidates = by_class[label].copy()
        rng.shuffle(candidates)
        selected.extend(candidates[:counts[label]])
    rng.shuffle(selected)
    return selected
