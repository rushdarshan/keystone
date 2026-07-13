import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Subset
import numpy as np


def get_cifar_loaders(
    batch_size: int = 128,
    cifar100: bool = False,
    num_workers: int = 0,
    subset: int = None,
):
    CIFAR = torchvision.datasets.CIFAR100 if cifar100 else torchvision.datasets.CIFAR10
    num_classes = 100 if cifar100 else 10

    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    train_set = CIFAR(root="./data", train=True, download=True, transform=transform_train)
    test_set = CIFAR(root="./data", train=False, download=True, transform=transform_test)

    if subset is not None:
        rng = np.random.default_rng(42)
        indices = rng.choice(len(train_set), min(subset, len(train_set)), replace=False)
        train_set = Subset(train_set, indices)

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    return train_loader, test_loader, num_classes
