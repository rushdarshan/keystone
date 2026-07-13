from __future__ import annotations
import torch.nn as nn
from ..registry import ComponentRegistry, ComponentSpec, ModelBuilder


class ResidualBlock(nn.Module):
    def __init__(self, in_planes, planes, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_planes, planes, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes),
            )

    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return self.relu(out)


class ResNetLike(nn.Module):
    def __init__(self, num_classes=10, width=64):
        super().__init__()
        self.conv1 = nn.Conv2d(3, width, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(width)
        self.relu = nn.ReLU(inplace=True)
        self.layer1 = nn.Sequential(ResidualBlock(width, width), ResidualBlock(width, width))
        self.layer2 = nn.Sequential(ResidualBlock(width, width*2, stride=2), ResidualBlock(width*2, width*2))
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(width*2, num_classes)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


def build_residual(builder: ModelBuilder) -> ModelBuilder:
    builder.use_residual = True
    builder.use_conv = True
    builder.use_batchnorm = True
    builder.layers = nn.ModuleList([ResNetLike(num_classes=builder.num_classes, width=builder.width)])
    return builder


def register_residual():
    ComponentRegistry.register(ComponentSpec(
        name="residual",
        description="Skip connections (ResNet-style residual blocks)",
        build_fn=build_residual,
        expected_param_delta="+500K params",
        citation="He et al. 2016 — Deep Residual Learning for Image Recognition (arXiv:1512.03385)"
    ))
