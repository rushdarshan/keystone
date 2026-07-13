from .cifar import get_cifar_loaders


def get_task(name: str, batch_size: int = 128):
    if name == "cifar10":
        return get_cifar_loaders(batch_size=batch_size, cifar100=False)
    elif name == "cifar100":
        return get_cifar_loaders(batch_size=batch_size, cifar100=True)
    else:
        raise ValueError(f"Unknown task: {name}")
