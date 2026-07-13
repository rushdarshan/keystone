import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from typing import Optional


class Trainer:
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        test_loader: DataLoader,
        lr: float = 0.001,
        epochs: int = 20,
        device: str = "cuda",
        weight_decay: float = 1e-4,
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.test_loader = test_loader
        self.device = device
        self.epochs = epochs
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=epochs)
        self.history = {"train_loss": [], "test_acc": [], "test_loss": []}

    def train_epoch(self):
        self.model.train()
        total_loss = 0
        for x, y in self.train_loader:
            x, y = x.to(self.device), y.to(self.device)
            self.optimizer.zero_grad()
            loss = self.criterion(self.model(x), y)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
        return total_loss / len(self.train_loader)

    @torch.no_grad()
    def evaluate(self):
        self.model.eval()
        correct = 0
        total = 0
        total_loss = 0
        for x, y in self.test_loader:
            x, y = x.to(self.device), y.to(self.device)
            out = self.model(x)
            loss = self.criterion(out, y)
            total_loss += loss.item()
            pred = out.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
        return correct / total, total_loss / len(self.test_loader)

    def run(self) -> dict:
        best_acc = 0.0
        for epoch in range(self.epochs):
            train_loss = self.train_epoch()
            test_acc, test_loss = self.evaluate()
            self.scheduler.step()
            best_acc = max(best_acc, test_acc)
            self.history["train_loss"].append(train_loss)
            self.history["test_acc"].append(test_acc)
            self.history["test_loss"].append(test_loss)
        return {"best_acc": best_acc, "final_acc": test_acc, "history": self.history}

    def count_params(self) -> int:
        return sum(p.numel() for p in self.model.parameters())

    def count_trainable_params(self) -> int:
        return sum(p.numel() for p in self.model.parameters() if p.requires_grad)
