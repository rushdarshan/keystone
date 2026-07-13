from pathlib import Path

import pandas as pd
import pytest

from src.keystone.visualization import plot_head_distribution, plot_pareto_curve


def test_plot_pareto_curve_creates_nonempty_png(tmp_path):
    data = {
        "seed_42": {
            "causal": {"0.1": {"top1_accuracy": 0.85}, "0.3": {"top1_accuracy": 0.82}, "0.5": {"top1_accuracy": 0.78}},
            "magnitude": {"0.1": {"top1_accuracy": 0.84}, "0.3": {"top1_accuracy": 0.80}, "0.5": {"top1_accuracy": 0.75}},
        }
    }
    out = tmp_path / "pareto.png"

    result = plot_pareto_curve(data, out)

    assert result == str(out)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_plot_head_distribution_creates_nonempty_png(tmp_path):
    scores = pd.DataFrame({
        "head_idx": list(range(48)),
        "layer": [i // 4 for i in range(48)],
        "score": [float(i % 10) for i in range(48)],
    })
    out = tmp_path / "distribution.png"

    result = plot_head_distribution(scores, out)

    assert result == str(out)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_pareto_curve_single_method(tmp_path):
    data = {
        "seed_0": {
            "random": {"0.2": {"top1_accuracy": 0.70}, "0.4": {"top1_accuracy": 0.65}, "0.6": {"top1_accuracy": 0.60}},
        }
    }
    out = tmp_path / "single.png"

    result = plot_pareto_curve(data, out)

    assert Path(result).exists()
    assert Path(result).stat().st_size > 0
