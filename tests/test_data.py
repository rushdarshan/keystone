import pytest

from src.keystone.data import stratified_subset_indices


def _histogram(targets, indices):
    histogram = {}
    for index in indices:
        label = targets[index]
        histogram[label] = histogram.get(label, 0) + 1
    return histogram


def test_stratified_subsets_change_images_but_preserve_class_composition():
    targets = [label for label in range(3) for _ in range(4)]

    first = stratified_subset_indices(targets, n_samples=6, seed=11)
    second = stratified_subset_indices(targets, n_samples=6, seed=12)

    assert len(first) == len(set(first)) == 6
    assert len(second) == len(set(second)) == 6
    assert set(first) != set(second)
    assert _histogram(targets, first) == _histogram(targets, second) == {0: 2, 1: 2, 2: 2}


def test_stratified_subsets_keep_selected_classes_fixed_when_sample_is_small():
    targets = [label for label in range(100) for _ in range(3)]

    first = stratified_subset_indices(targets, n_samples=50, seed=1, composition_seed=7)
    second = stratified_subset_indices(targets, n_samples=50, seed=2, composition_seed=7)

    assert set(targets[index] for index in first) == set(targets[index] for index in second)
    assert set(first) != set(second)


def test_stratified_subset_rejects_oversized_request():
    with pytest.raises(ValueError, match="only contains"):
        stratified_subset_indices([0, 0, 1], n_samples=4, seed=0)
