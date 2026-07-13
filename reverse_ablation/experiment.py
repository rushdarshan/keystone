import torch
import numpy as np
import pandas as pd
import time
import json
from pathlib import Path
from typing import List, Optional
from .registry import ComponentRegistry, ModelBuilder
from .trainer import Trainer
from .tasks import get_task
from .components import register_all


register_all()


class ReverseAblationExperiment:
    def __init__(
        self,
        task: str = "cifar10",
        batch_size: int = 128,
        epochs: int = 20,
        lr: float = 0.001,
        seed: int = 42,
        device: str = None,
        subset: int = None,
    ):
        self.task = task
        self.batch_size = batch_size
        self.epochs = epochs
        self.lr = lr
        self.seed = seed
        self.subset = subset
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.results_dir = Path("experiments")
        self.results_dir.mkdir(exist_ok=True)
        torch.manual_seed(seed)
        np.random.seed(seed)

    def _get_builder(self) -> ModelBuilder:
        train_loader, test_loader, num_classes = get_task(self.task, self.batch_size, subset=self.subset)
        return ModelBuilder(
            input_size=3072,
            num_classes=num_classes,
            img_size=32,
            in_channels=3,
        ), train_loader, test_loader

    def run_sequence(self, component_names: List[str], tag: str = "default"):
        builder, train_loader, test_loader = self._get_builder()
        results = []

        for i, name in enumerate(component_names):
            print(f"\n{'='*60}")
            print(f"Step {i+1}/{len(component_names)}: Adding component '{name}'")
            print(f"{'='*60}")

            spec = ComponentRegistry.get(name)
            builder = spec.build_fn(builder)
            model = builder.build()

            param_count = sum(p.numel() for p in model.parameters())

            trainer = Trainer(
                model=model,
                train_loader=train_loader,
                test_loader=test_loader,
                lr=self.lr,
                epochs=self.epochs,
                device=self.device,
            )

            t0 = time.time()
            result = trainer.run()
            elapsed = time.time() - t0

            result.update({
                "component": name,
                "step": i + 1,
                "params": param_count,
                "trainable_params": trainer.count_trainable_params(),
                "time_seconds": elapsed,
                "epochs": self.epochs,
            })
            results.append(result)
            print(f"  Params: {param_count:,}")
            print(f"  Best Acc: {result['best_acc']:.4f}")
            print(f"  Time: {elapsed:.1f}s")

        self._save_results(results, tag)
        return results

    def run_all_independent(self, component_names: List[str], tag: str = "independent"):
        results = []
        train_loader, test_loader, _ = get_task(self.task, self.batch_size, subset=self.subset)

        for name in component_names:
            print(f"\n{'='*60}")
            print(f"Independent run: '{name}'")
            print(f"{'='*60}")

            spec = ComponentRegistry.get(name)
            builder = ModelBuilder(input_size=3072, num_classes=10, img_size=32, in_channels=3)
            builder = spec.build_fn(builder)
            model = builder.build()

            param_count = sum(p.numel() for p in model.parameters())

            trainer = Trainer(
                model=model,
                train_loader=train_loader,
                test_loader=test_loader,
                lr=self.lr,
                epochs=self.epochs,
                device=self.device,
            )

            t0 = time.time()
            result = trainer.run()
            elapsed = time.time() - t0

            result.update({
                "component": name,
                "params": param_count,
                "time_seconds": elapsed,
                "epochs": self.epochs,
            })
            results.append(result)
            print(f"  Params: {param_count:,}")
            print(f"  Best Acc: {result['best_acc']:.4f}")

        self._save_results(results, tag)
        return results

    def run_pareto_sequence(self, sequences: List[List[str]], tag: str = "pareto"):
        all_results = []
        for seq in sequences:
            results = self.run_sequence(seq, tag=f"{tag}_seq")
            all_results.extend(results)
        df = pd.DataFrame(all_results)
        df = df.sort_values("params")
        pareto = []
        best_acc = 0.0
        for _, row in df.iterrows():
            if row["best_acc"] > best_acc:
                best_acc = row["best_acc"]
                pareto.append(row)
        pareto_df = pd.DataFrame(pareto)
        pareto_df.to_csv(self.results_dir / f"{tag}_pareto.csv", index=False)
        return pareto_df

    def _save_results(self, results, tag):
        df = pd.DataFrame(results)
        path = self.results_dir / f"{tag}_results.csv"
        df.to_csv(path, index=False)
        print(f"\nSaved to {path}")
