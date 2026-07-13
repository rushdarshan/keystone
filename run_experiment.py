#!/usr/bin/env python3
"""
Reverse Ablation — Minimum Viable Architecture Discovery

Usage:
    python run_experiment.py --mode sequential   # build-up sequence
    python run_experiment.py --mode independent  # each component trained alone
    python run_experiment.py --mode pareto       # multiple sequences for Pareto frontier
"""
import argparse
import pandas as pd
from reverse_ablation.experiment import ReverseAblationExperiment
from reverse_ablation.analysis.pareto import save_plots
from reverse_ablation.components import register_all


BUILD_UP_SEQUENCE = [
    "linear",
    "activation",
    "depth",
    "width",
    "convolution",
    "residual",
    "batchnorm",
    "dropout",
    "layernorm",
    "attention",
    "patch_embed",
]

INDEPENDENT = [
    "linear",
    "head_only",
    "activation",
    "depth",
    "width",
    "convolution",
    "residual",
    "batchnorm",
    "dropout",
    "layernorm",
    "attention",
    "patch_embed",
    "pos_embed",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sequential", "independent", "pareto", "all"], default="sequential")
    parser.add_argument("--task", default="cifar10", choices=["cifar10", "cifar100"])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--subset", type=int, default=None, help="Limit training samples (for quick tests)")
    args = parser.parse_args()

    register_all()

    exp = ReverseAblationExperiment(
        task=args.task,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        subset=args.subset,
    )

    tag = f"{args.task}_e{args.epochs}"

    if args.mode in ("sequential", "all"):
        print("\n=== Sequential Build-Up Ablation ===")
        results = exp.run_sequence(BUILD_UP_SEQUENCE, tag=f"{tag}_sequential")
        df = pd.DataFrame(results)
        df.to_csv(f"experiments/{tag}_sequential.csv", index=False)
        save_plots(df, f"experiments/{tag}_sequential")

    if args.mode in ("independent", "all"):
        print("\n=== Independent Component Evaluation ===")
        results = exp.run_all_independent(INDEPENDENT, tag=f"{tag}_independent")
        df = pd.DataFrame(results)
        df.to_csv(f"experiments/{tag}_independent.csv", index=False)
        save_plots(df, f"experiments/{tag}_independent")

    if args.mode in ("pareto", "all"):
        print("\n=== Pareto Frontier (multiple sequences) ===")
        seqs = [
            BUILD_UP_SEQUENCE,
            ["linear", "head_only", "convolution", "residual"],
            ["linear", "head_only", "patch_embed", "attention"],
        ]
        df = exp.run_pareto_sequence(seqs, tag=f"{tag}_pareto")
        save_plots(df, f"experiments/{tag}_pareto")

    print("\nDone!")


if __name__ == "__main__":
    main()
