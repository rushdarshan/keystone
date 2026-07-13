import torch

from src.keystone.probe import fit_linear_probe_from_features, install_linear_probe


class DummyBackbone(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.head = torch.nn.Identity()
        self.num_features = 2
        self.num_classes = 0

    def forward(self, inputs):
        return self.head(inputs)


def test_linear_probe_learns_separable_features_and_installs_on_backbone():
    train_features = torch.tensor([
        [-2.0, -1.0],
        [-1.0, -2.0],
        [-2.0, -2.0],
        [2.0, 1.0],
        [1.0, 2.0],
        [2.0, 2.0],
    ])
    train_labels = torch.tensor([0, 0, 0, 1, 1, 1])

    classifier, accuracy = fit_linear_probe_from_features(
        train_features,
        train_labels,
        train_features,
        train_labels,
        num_classes=2,
        epochs=100,
        learning_rate=0.1,
        weight_decay=0.0,
        seed=3,
        device="cpu",
    )

    assert accuracy == 1.0
    backbone = DummyBackbone()
    install_linear_probe(backbone, classifier)
    assert backbone.head is classifier
    assert backbone.num_classes == 2
    assert backbone(torch.tensor([[2.0, 1.0]])).argmax(dim=-1).item() == 1
