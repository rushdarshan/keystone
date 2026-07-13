"""Pareto curves and correlation plots for pruning results."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_pareto_curve(results_json: Path | str | dict, output_path: Path | str) -> str:
    """Plot accuracy vs sparsity Pareto curves for each pruning method.

    Args:
        results_json: Path to results.json or dict with structure:
            {seed: {method: {ratio: {top1_accuracy: float}}}}
        output_path: Where to save the PNG.

    Returns:
        Path to saved figure.
    """
    if isinstance(results_json, (str, Path)):
        with open(results_json) as f:
            data = json.load(f)
    else:
        data = results_json

    methods = {}
    for seed, seed_data in data.items():
        for method, method_data in seed_data.items():
            if method not in methods:
                methods[method] = {"ratios": [], "accuracies": []}
            for ratio_str, metrics in method_data.items():
                ratio = float(ratio_str)
                acc = metrics.get("top1_accuracy", 0)
                methods[method]["ratios"].append(ratio)
                methods[method]["accuracies"].append(acc)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = {"causal": "#2196F3", "magnitude": "#FF9800", "gradient": "#4CAF50", "random": "#9E9E9E"}

    for method_name, method_results in methods.items():
        ratios = np.array(method_results["ratios"])
        accs = np.array(method_results["accuracies"])
        sorted_idx = np.argsort(ratios)
        color = colors.get(method_name, "#607D8B")
        ax.plot(
            ratios[sorted_idx] * 100,
            accs[sorted_idx] * 100,
            marker="o",
            label=method_name,
            color=color,
            linewidth=2,
            markersize=6,
        )

    ax.set_xlabel("Sparsity (% heads removed)", fontsize=12)
    ax.set_ylabel("Top-1 Accuracy (%)", fontsize=12)
    ax.set_title("CIFAR-100 Accuracy vs Pruning Ratio", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return str(output_path)


def plot_head_distribution(scores_df, output_path: Path | str) -> str:
    """Plot keystone head count per layer as a bar chart.

    Args:
        scores_df: DataFrame with columns [head_idx, layer, score].
        output_path: Where to save the PNG.

    Returns:
        Path to saved figure.
    """
    import pandas as pd

    n_layers = scores_df["layer"].nunique()
    top_score_threshold = scores_df["score"].quantile(0.75)

    layer_counts = (
        scores_df[scores_df["score"] >= top_score_threshold]
        .groupby("layer")
        .size()
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    layers = range(n_layers)
    counts = [layer_counts.get(layer, 0) for layer in layers]

    ax.bar(layers, counts, color="#2196F3", alpha=0.8)
    ax.set_xlabel("Layer Index", fontsize=12)
    ax.set_ylabel("Keystone Head Count (top 25%)", fontsize=12)
    ax.set_title("Keystone Head Distribution Across Layers", fontsize=14)
    ax.set_xticks(layers)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return str(output_path)
