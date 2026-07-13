import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


class ParetoAnalyzer:
    def __init__(self, results: pd.DataFrame):
        self.df = results.sort_values("params")
        self.pareto = self._compute_pareto()

    def _compute_pareto(self):
        pareto = []
        best_acc = 0.0
        for _, row in self.df.iterrows():
            if row["best_acc"] > best_acc:
                best_acc = row["best_acc"]
                pareto.append(row)
        return pd.DataFrame(pareto)

    def marginal_gains(self):
        gains = []
        prev_acc = 0.0
        prev_params = 0
        for _, row in self.pareto.iterrows():
            acc_gain = row["best_acc"] - prev_acc
            param_cost = row["params"] - prev_params
            efficiency = acc_gain / max(param_cost, 1) * 1e6
            gains.append({
                "component": row["component"],
                "accuracy": row["best_acc"],
                "params": row["params"],
                "marginal_acc_gain": acc_gain,
                "marginal_param_cost": param_cost,
                "efficiency_micro": efficiency,
            })
            prev_acc = row["best_acc"]
            prev_params = row["params"]
        return pd.DataFrame(gains)


def save_plots(results: pd.DataFrame, output_dir: str = "experiments"):
    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    analyzer = ParetoAnalyzer(results)
    gains = analyzer.marginal_gains()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax = axes[0, 0]
    ax.plot(gains["params"] / 1e6, gains["accuracy"] * 100, "bo-", linewidth=2, markersize=8)
    for _, r in gains.iterrows():
        ax.annotate(r["component"], (r["params"] / 1e6, r["accuracy"] * 100), fontsize=8, ha="center")
    ax.set_xlabel("Parameters (millions)")
    ax.set_ylabel("Test Accuracy (%)")
    ax.set_title("Pareto Frontier: Accuracy vs Parameters")
    ax.grid(True, alpha=0.3)

    ax = axes[0, 1]
    colors = ["green" if g > 0 else "red" for g in gains["marginal_acc_gain"]]
    ax.bar(range(len(gains)), gains["marginal_acc_gain"] * 100, color=colors)
    ax.set_xticks(range(len(gains)))
    ax.set_xticklabels(gains["component"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Marginal Accuracy Gain (pp)")
    ax.set_title("Marginal Benefit of Each Component")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3)

    ax = axes[1, 0]
    ax.bar(range(len(gains)), gains["efficiency_micro"], color="purple", alpha=0.7)
    ax.set_xticks(range(len(gains)))
    ax.set_xticklabels(gains["component"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Efficiency (acc gain / million params)")
    ax.set_title("Component Efficiency")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3)

    ax = axes[1, 1]
    sizes = gains["params"] / gains["params"].max() * 500 + 50
    ax.scatter(gains["accuracy"] * 100, gains["efficiency_micro"], s=sizes, alpha=0.6, c=range(len(gains)), cmap="viridis")
    for _, r in gains.iterrows():
        ax.annotate(r["component"], (r["accuracy"] * 100, r["efficiency_micro"]), fontsize=8)
    ax.set_xlabel("Test Accuracy (%)")
    ax.set_ylabel("Efficiency")
    ax.set_title("Accuracy-Efficiency Tradeoff")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = out / "pareto_analysis.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved pareto analysis to {path}")

    gains.to_csv(out / "marginal_gains.csv", index=False)
    print(f"Saved marginal gains to {out / 'marginal_gains.csv'}")


def plot_pareto_frontier(results_df, save_path="experiments/pareto_frontier.png"):
    save_plots(results_df, Path(save_path).parent)


def marginal_benefit_plot(results_df, save_path="experiments/marginal_benefit.png"):
    pass


def component_efficiency_table(results_df):
    analyzer = ParetoAnalyzer(results_df)
    return analyzer.marginal_gains()
