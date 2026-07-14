#!/usr/bin/env python3
"""Pruning orchestrator: score heads, prune, evaluate across ratios/methods/seeds."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import torch
from torch.utils.data import DataLoader
from torchvision import datasets

from src.keystone.analysis import compare_rankings
from src.keystone.baselines import score_gradient, score_magnitude, score_random
from src.keystone.config import PocConfig
from src.keystone.data import cifar100_transform, stratified_subset_indices
from src.keystone.evaluation import evaluate_accuracy, measure_efficiency
from src.keystone.models import load_dinov3
from src.keystone.pruning import get_keystone_head_indices, prune_heads
from src.keystone.probe import extract_features, fit_linear_probe_from_features, install_linear_probe
from src.keystone.scoring import score_all_heads
from src.keystone.utils import format_time, set_seed, write_environment
from src.keystone.vit_adapters import discover_head_specs

# ponytail: module-level constant, no config object needed
METHODS = ("causal", "magnitude", "gradient", "random")
DETERMINISTIC_METHODS = ("causal", "magnitude", "gradient")


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _load_scoring_images(
    n_images: int,
    batch_size: int,
    seed: int,
    device: str,
    num_workers: int = 2,
) -> tuple[torch.Tensor, torch.Tensor, list[int]]:
    transform = cifar100_transform()
    dataset = datasets.CIFAR100(root="./data", train=False, download=True, transform=transform)
    indices = stratified_subset_indices(dataset.targets, n_images, seed, composition_seed=0)
    subset = torch.utils.data.Subset(dataset, indices)
    loader = DataLoader(subset, batch_size=n_images, shuffle=False, num_workers=num_workers)
    images, labels = next(iter(loader))
    return images.to(device), labels.to(device), indices


def _load_eval_dataset(
    n_images: int,
    seed: int,
) -> tuple[torch.utils.data.Dataset, list[int]]:
    transform = cifar100_transform()
    dataset = datasets.CIFAR100(root="./data", train=False, download=True, transform=transform)
    indices = stratified_subset_indices(dataset.targets, n_images, seed)
    return dataset, indices


def _add_layer_info(df: pd.DataFrame, head_specs: list[dict]) -> pd.DataFrame:
    """Ensure DataFrame has layer + head_in_layer columns by merging from head_specs."""
    if "layer" in df.columns and "head_in_layer" in df.columns:
        return df
    spec_map = {s["head_idx"]: (s["layer_idx"], s["head_in_layer"]) for s in head_specs}
    df = df.copy()
    df["layer"] = df["head_idx"].map(lambda h: spec_map[h][0])
    df["head_in_layer"] = df["head_idx"].map(lambda h: spec_map[h][1])
    return df


def _method_score_df(
    scores: dict[str, pd.DataFrame],
    method: str,
    seed: int,
    head_specs: list[dict],
) -> pd.DataFrame:
    """Return a DataFrame with columns [head_idx, layer, head_in_layer, score]."""
    if method == "random":
        df = score_random(len(head_specs), seed)
        df = _add_layer_info(df, head_specs)
        return df
    df = scores[method].copy()
    if "causal_score" in df.columns:
        df = df.rename(columns={"causal_score": "score"})
    return df


def _build_rankings(
    scores: dict[str, pd.DataFrame],
    head_specs: list[dict],
    seeds: tuple[int, ...],
) -> dict[int, dict[str, list[int]]]:
    """Produce {seed: {method: [head_idx sorted by score descending]}}."""
    rankings: dict[int, dict[str, list[int]]] = {}

    for seed in seeds:
        rankings[seed] = {}
        for method in DETERMINISTIC_METHODS:
            if method not in scores:
                continue
            df = scores[method]
            col = "causal_score" if "causal_score" in df.columns else "score"
            rankings[seed][method] = df.sort_values(col, ascending=False)["head_idx"].tolist()

        rand_df = score_random(len(head_specs), seed)
        rankings[seed]["random"] = rand_df["head_idx"].tolist()

    return rankings


def _run_scoring(
    model: torch.nn.Module,
    head_specs: list[dict],
    images: torch.Tensor,
    labels: torch.Tensor,
    cfg: PocConfig,
    output_dir: Path,
    *,
    skip_causal: bool,
    quick: bool,
) -> dict[str, pd.DataFrame]:
    scores: dict[str, pd.DataFrame] = {}

    # --- Causal ---
    causal_csv = output_dir / "causal_scores.csv"
    if skip_causal and causal_csv.exists():
        print("  [scoring] loading cached causal scores (--skip-causal)")
        scores["causal"] = pd.read_csv(causal_csv)
    else:
        if skip_causal:
            print("  [scoring] --skip-causal but no cached scores; running causal scoring anyway")
        print("  [scoring] running CausalHeadRank on all heads...")
        start = time.perf_counter()
        causal_cfg = cfg  # score_all_heads uses cfg.output_dir for checkpoints
        scores["causal"] = score_all_heads(
            model, head_specs, images, labels, causal_cfg,
            checkpoint_name="causal_scores.csv",
        )
        elapsed = time.perf_counter() - start
        print(f"  [scoring] causal complete in {format_time(elapsed)}")

    # --- Magnitude ---
    print("  [scoring] computing magnitude baseline...")
    scores["magnitude"] = score_magnitude(model, head_specs)

    # --- Gradient ---
    if quick:
        print("  [scoring] skipped gradient baseline (--quick)")
    else:
        print("  [scoring] computing gradient baseline...")
        scores["gradient"] = score_gradient(model, head_specs, images, labels, cfg.device)

    return scores


def _run_pruning_loop(
    model: torch.nn.Module,
    head_specs: list[dict],
    scores: dict[str, pd.DataFrame],
    eval_dataset: torch.utils.data.Dataset,
    eval_indices: list[int],
    sample_input: torch.Tensor,
    cfg: PocConfig,
    ratios: tuple[float, ...],
    seeds: tuple[int, ...],
    *,
    skip_eval: bool,
) -> dict[str, dict]:
    NUM_CLASSES = 100
    PROBE_TRAIN_PCT = 0.5
    PROBE_EPOCHS = 10

    results: dict[str, dict] = {}
    active_methods = [m for m in METHODS if m in scores or m == "random"]
    if "gradient" not in scores:
        active_methods = [m for m in active_methods if m != "gradient"]

    for seed in seeds:
        seed_key = str(seed)
        results[seed_key] = {}
        for method in active_methods:
            results[seed_key][method] = {}
            score_df = _method_score_df(scores, method, seed, head_specs)

            for ratio in ratios:
                pct = f"{int(ratio * 100)}%"
                print(f"  [prune] seed={seed} method={method:<10} ratio={pct}")
                keep_indices = get_keystone_head_indices(score_df, ratio, per_layer_floor=1)
                kept_total = sum(len(v) for v in keep_indices.values())
                print(f"    keeping {kept_total}/{len(head_specs)} heads")

                pruned = copy.deepcopy(model)
                prune_heads(pruned, keep_indices)

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                record: dict = {"ratio": float(ratio)}

                if not skip_eval:
                    split = int(len(eval_indices) * PROBE_TRAIN_PCT)
                    train_idx = eval_indices[:split]
                    val_idx = eval_indices[split:]

                    train_feat, train_lbl = extract_features(
                        pruned, eval_dataset, train_idx, device=cfg.device, batch_size=cfg.batch_size,
                    )
                    val_feat, val_lbl = extract_features(
                        pruned, eval_dataset, val_idx, device=cfg.device, batch_size=cfg.batch_size,
                    )

                    probe, probe_acc = fit_linear_probe_from_features(
                        train_feat, train_lbl,
                        val_feat, val_lbl,
                        num_classes=NUM_CLASSES,
                        epochs=PROBE_EPOCHS,
                        learning_rate=0.01,
                        weight_decay=1e-4,
                        seed=cfg.seed,
                        device=cfg.device,
                    )
                    install_linear_probe(pruned, probe)

                    val_loader = DataLoader(
                        torch.utils.data.Subset(eval_dataset, val_idx),
                        batch_size=cfg.batch_size, shuffle=False,
                    )
                    acc = evaluate_accuracy(pruned, val_loader, cfg.device)
                    record.update(acc)
                    record["probe_val_accuracy"] = round(probe_acc, 4)
                    print(f"    probe_acc={probe_acc:.4f}  top1={acc['top1_accuracy']:.4f}  top5={acc['top5_accuracy']:.4f}")

                eff = measure_efficiency(pruned, sample_input, cfg.device)
                record.update(eff)
                print(
                    f"    {eff['throughput_ips']:.1f} ips  "
                    f"{eff['peak_vram_gb']:.2f} GB  "
                    f"{eff['param_count_millions']:.1f}M params"
                )

                results[seed_key][method][str(ratio)] = record

                del pruned
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    return results


def _print_table(results: dict) -> None:
    header = f"{'Seed':<6} {'Method':<12} {'Ratio':<8} {'Top1':<10} {'Top5':<10} {'IPS':<10} {'VRAM(GB)':<10} {'Params(M)':<10}"
    print(f"\n{header}")
    print("-" * len(header))

    for seed_key in sorted(results, key=int):
        seed_results = results[seed_key]
        for method in METHODS:
            if method not in seed_results:
                continue
            for ratio_str in sorted(seed_results[method], key=float):
                r = seed_results[method][ratio_str]
                top1 = r.get("top1_accuracy")
                top5 = r.get("top5_accuracy")
                ips = r.get("throughput_ips", "N/A")
                vram = r.get("peak_vram_gb", "N/A")
                params = r.get("param_count_millions", "N/A")

                t1 = f"{float(top1):.4f}" if isinstance(top1, (int, float)) else str(top1)
                t5 = f"{float(top5):.4f}" if isinstance(top5, (int, float)) else str(top5)
                i = f"{float(ips):.1f}" if isinstance(ips, (int, float)) else str(ips)
                v = f"{float(vram):.2f}" if isinstance(vram, (int, float)) else str(vram)
                p = f"{float(params):.1f}" if isinstance(params, (int, float)) else str(params)

                print(f"{seed_key:<6} {method:<12} {ratio_str:<8} {t1:<10} {t5:<10} {i:<10} {v:<10} {p:<10}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Keystone pruning orchestrator")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--n-images", type=int, default=100)
    parser.add_argument("--n-eval-images", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--ratios", type=str, default="0.25,0.50,0.75,0.90")
    parser.add_argument("--seeds", type=str, default="42,43,44")
    parser.add_argument("--output-dir", default="experiments/pruning")
    parser.add_argument("--model-name", default="vit_base_patch16_dinov3")
    parser.add_argument("--skip-causal", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--pretrained", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    # --quick overrides
    if args.quick:
        args.n_images = 25
        args.n_eval_images = 25
        args.seeds = "42"
        args.skip_eval = True
        args.ratios = "0.25,0.50"
        print("[quick] 25 images, 1 seed, skip eval, skip gradient")

    ratios = tuple(float(r.strip()) for r in args.ratios.split(","))
    seeds = tuple(int(s.strip()) for s in args.seeds.split(","))

    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print("  [device] CUDA unavailable, falling back to CPU")
        device = "cpu"

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = PocConfig(
        seed=args.seed,
        device=device,
        batch_size=args.batch_size,
        n_images=args.n_images,
        n_eval_images=args.n_eval_images,
        model_name=args.model_name,
        pretrained=args.pretrained,
        output_dir=str(output_dir),
    )
    set_seed(cfg.seed)
    write_environment(str(output_dir))

    # --- Load model ---
    print("=== Loading model ===")
    print(f"  model: {cfg.model_name}  pretrained={cfg.pretrained}")
    model = load_dinov3(cfg.model_name, cfg.device, cfg.pretrained)
    head_specs = discover_head_specs(model)
    print(f"  discovered {len(head_specs)} heads across {len({s['layer_idx'] for s in head_specs})} layers")
    if args.quick:
        print(f"  [quick] scoring only 5 heads, skipping pruning")

    # --- Load scoring images ---
    print("\n=== Loading scoring images ===")
    images, labels, _ = _load_scoring_images(cfg.n_images, cfg.batch_size, cfg.seed, cfg.device)
    print(f"  {images.shape[0]} images on {cfg.device}")

    # --- Score heads ---
    print("\n=== Scoring heads ===")
    scoring_specs = head_specs[:5] if args.quick else head_specs
    scores = _run_scoring(
        model, scoring_specs, images, labels, cfg, output_dir,
        skip_causal=args.skip_causal,
        quick=args.quick,
    )

    # --- Save rankings ---
    rankings = _build_rankings(scores, head_specs, seeds)
    _write_json(output_dir / "rankings.json", {
        str(seed): methods for seed, methods in rankings.items()
    })
    print(f"\n  [save] rankings.json ({len(rankings)} seeds)")

    # --- Correlations ---
    print("\n=== Correlations ===")
    if all(k in scores for k in ("causal", "magnitude", "gradient")):
        correlations = compare_rankings(
            scores["causal"],
            scores["magnitude"],
            scores["gradient"],
        )
        _write_json(output_dir / "correlations.json", correlations)
        print(f"  tau(causal,mag) = {correlations['tau_causal_magnitude']}")
        print(f"  tau(causal,grad) = {correlations['tau_causal_gradient']}")
        print(f"  tau(mag,grad)    = {correlations['tau_magnitude_gradient']}")
        print(f"  keystone candidates: {correlations['n_keystone']}/{correlations['total_heads']} "
              f"({correlations['keystone_pct']}%)")
    else:
        print("  skipped (missing gradient scores from --quick)")

    # --- Eval data ---
    print(f"\n=== Loading eval data ({cfg.n_eval_images} images) ===")
    eval_dataset, eval_indices = _load_eval_dataset(cfg.n_eval_images, cfg.seed)
    sample_input = images[:1].clone()
    unpruned_eff = measure_efficiency(model, sample_input, cfg.device)
    print(f"  unpruned: {unpruned_eff['throughput_ips']:.1f} ips, "
          f"{unpruned_eff['peak_vram_gb']:.2f} GB, "
          f"{unpruned_eff['param_count_millions']:.1f}M params")

    # --- Pruning loop ---
    if args.quick:
        print("\n=== Pruning + evaluation ===")
        print("  [quick] skipping pruning — verifying pipeline wiring only")
        results = {"quick": True, "scored_heads": len(scoring_specs), "total_heads": len(head_specs)}
    else:
        print("\n=== Pruning + evaluation ===")
        results = _run_pruning_loop(
            model, head_specs, scores, eval_dataset, eval_indices, sample_input,
            cfg, ratios, seeds,
            skip_eval=args.skip_eval,
        )

        _print_table(results)

    _write_json(output_dir / "results.json", results)
    print(f"\n  [save] results.json")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
