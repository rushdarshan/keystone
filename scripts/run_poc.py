#!/usr/bin/env python3
"""CausalHeadRank PoC: validate class-aware activation patching on ViTs."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from torchvision import datasets

from src.keystone.analysis import determine_verdict, estimate_total_runtime, kendall_tau, top_k_overlap
from src.keystone.config import PocConfig
from src.keystone.data import cifar100_transform, stratified_subset_indices
from src.keystone.models import load_dinov3, load_fallback
from src.keystone.nnsight_validation import validate_nnsight_equivalence
from src.keystone.probe import extract_features, fit_linear_probe_from_features, install_linear_probe
from src.keystone.scoring import score_all_heads
from src.keystone.utils import format_time, log_memory, set_seed, write_environment, write_failure_report
from src.keystone.vit_adapters import discover_head_specs, print_hook_table, write_hook_manifest


def load_images(
    cfg: PocConfig,
    *,
    fake_data: bool = False,
) -> tuple[torch.Tensor, torch.Tensor, list[int]]:
    transform = cifar100_transform()
    if fake_data:
        dataset = datasets.FakeData(
            size=max(cfg.n_images * 4, 100),
            image_size=(3, 224, 224),
            num_classes=100,
            transform=transform,
            random_offset=0,
        )
        targets = [int(dataset[index][1]) for index in range(len(dataset))]
    else:
        dataset = datasets.CIFAR100(root="./data", train=False, download=True, transform=transform)
        targets = dataset.targets

    indices = stratified_subset_indices(
        targets,
        cfg.n_images,
        cfg.seed,
        composition_seed=cfg.sample_composition_seed,
    )
    subset = torch.utils.data.Subset(dataset, indices)
    loader = torch.utils.data.DataLoader(
        subset,
        batch_size=cfg.n_images,
        num_workers=cfg.num_workers,
        shuffle=False,
    )
    images, labels = next(iter(loader))
    return images.to(cfg.device), labels.to(cfg.device), indices


def load_model(cfg: PocConfig) -> tuple[torch.nn.Module, list[dict]]:
    try:
        model = load_dinov3(cfg.model_name, cfg.device, cfg.pretrained)
    except Exception as exc:
        print(f"  [model] {cfg.model_name} failed: {exc}")
        try:
            model = load_fallback(cfg.fallback_model, cfg.device, cfg.pretrained)
        except Exception as fallback_exc:
            raise RuntimeError(f"primary and fallback model loading failed: {fallback_exc}") from exc

    head_specs = discover_head_specs(model)
    if not head_specs:
        sample_modules = [name for name, _ in list(model.named_modules())[:10]]
        raise RuntimeError(
            "No attention heads found. Expected modules with `num_heads` and qkv projections. "
            f"First modules: {sample_modules}"
        )
    return model, head_specs


def fit_cifar100_probe(model: torch.nn.Module, cfg: PocConfig) -> float:
    dataset = datasets.CIFAR100(root="./data", train=True, download=True, transform=cifar100_transform())
    train_indices = stratified_subset_indices(
        dataset.targets,
        cfg.probe_train_images,
        cfg.seed + 10_000,
        composition_seed=cfg.sample_composition_seed,
    )
    train_set = set(train_indices)
    remaining_indices = [index for index in range(len(dataset)) if index not in train_set]
    remaining_targets = [dataset.targets[index] for index in remaining_indices]
    val_local_indices = stratified_subset_indices(
        remaining_targets,
        cfg.probe_val_images,
        cfg.seed + 20_000,
        composition_seed=cfg.sample_composition_seed,
    )
    val_indices = [remaining_indices[index] for index in val_local_indices]

    started = time.perf_counter()
    train_features, train_labels = _extract_features_with_backoff(model, dataset, train_indices, cfg)
    val_features, val_labels = _extract_features_with_backoff(model, dataset, val_indices, cfg)
    classifier, accuracy = fit_linear_probe_from_features(
        train_features,
        train_labels,
        val_features,
        val_labels,
        num_classes=100,
        epochs=cfg.probe_epochs,
        learning_rate=cfg.probe_learning_rate,
        weight_decay=cfg.probe_weight_decay,
        seed=cfg.seed,
        device=cfg.device,
    )
    install_linear_probe(model, classifier)

    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(classifier.state_dict(), output_dir / "linear_probe.pt")
    _write_json(output_dir / "probe_metrics.json", {
        "validation_accuracy": accuracy,
        "minimum_accuracy": cfg.probe_min_accuracy,
        "train_images": len(train_indices),
        "validation_images": len(val_indices),
        "epochs": cfg.probe_epochs,
        "elapsed_seconds": time.perf_counter() - started,
        "train_test_overlap": 0,
    })
    return accuracy


def _extract_features_with_backoff(
    model: torch.nn.Module,
    dataset: torch.utils.data.Dataset,
    indices: list[int],
    cfg: PocConfig,
) -> tuple[torch.Tensor, torch.Tensor]:
    batch_size = min(cfg.probe_batch_size, len(indices))
    while True:
        try:
            print(f"  [probe] extracting {len(indices)} features at batch size {batch_size}")
            return extract_features(
                model,
                dataset,
                indices,
                batch_size=batch_size,
                device=cfg.device,
                num_workers=cfg.num_workers,
            )
        except torch.cuda.OutOfMemoryError:
            if batch_size == 1:
                raise
            batch_size = max(1, batch_size // 2)
            torch.cuda.empty_cache()
            print(f"  [probe] CUDA OOM; retrying at batch size {batch_size}")


def run_batch_sweep(
    model: torch.nn.Module,
    head_specs: list[dict],
    images: torch.Tensor,
    labels: torch.Tensor,
    cfg: PocConfig,
) -> None:
    print("\n=== Batch-size sweep ===")
    results = []
    for batch_size in [2, 4, 8, 16]:
        if batch_size > images.shape[0]:
            continue
        sweep_cfg = replace(cfg, batch_size=batch_size)
        df = score_all_heads(
            model,
            head_specs[:1],
            images,
            labels,
            sweep_cfg,
            checkpoint_name=f"batch_sweep_bs{batch_size}.csv",
        )
        seconds = float(df["time_seconds"].iloc[0])
        peak = float(df["peak_memory_gb"].max())
        throughput = 3600 / seconds if seconds > 0 else 0.0
        results.append((batch_size, seconds, peak, throughput))
        print(f"  bs={batch_size}: {format_time(seconds)}, peak={peak:.2f} GB, {throughput:.2f} heads/hour")

    viable = [row for row in results if row[2] < 10.0]
    if viable:
        best = max(viable, key=lambda row: row[3])
        print(f"  recommended batch size: {best[0]}")


def run_stability_test(
    model: torch.nn.Module,
    head_specs: list[dict],
    base_images: torch.Tensor,
    base_labels: torch.Tensor,
    base_indices: list[int],
    cfg: PocConfig,
    *,
    fake_data: bool,
) -> tuple[bool, dict, object]:
    rankings = []
    sample_records = []
    base_class_counts = Counter(base_labels.detach().cpu().tolist())

    for repeat in range(cfg.stability_repeats):
        repeat_cfg = replace(cfg, seed=cfg.seed + repeat)
        set_seed(repeat_cfg.seed)
        if repeat == 0:
            images, labels, indices = base_images, base_labels, base_indices
        else:
            images, labels, indices = load_images(repeat_cfg, fake_data=fake_data)
            if set(indices) == set(base_indices):
                raise RuntimeError("stability subsets are identical; refusing to compute a tautological tau")
            if Counter(labels.detach().cpu().tolist()) != base_class_counts:
                raise RuntimeError("stability subsets do not preserve class composition")

        checkpoint = f"q3_seed_{repeat_cfg.seed}_scores.csv"
        ranking = score_all_heads(model, head_specs, images, labels, repeat_cfg, checkpoint_name=checkpoint)
        rankings.append(ranking)
        sample_records.append({
            "seed": repeat_cfg.seed,
            "indices": indices,
            "overlap_with_baseline": len(set(indices) & set(base_indices)),
            "class_histogram": dict(sorted(Counter(labels.detach().cpu().tolist()).items())),
            "checkpoint": checkpoint,
        })

    taus = [kendall_tau(rankings[0], ranking) for ranking in rankings[1:]]
    overlaps = [top_k_overlap(rankings[0], ranking, cfg.stability_top_k) for ranking in rankings[1:]]
    report = {
        "repeats": cfg.stability_repeats,
        "target_tau": 0.7,
        "minimum_tau": 0.6,
        "mean_tau": statistics.fmean(taus),
        "min_tau": min(taus),
        "taus_vs_baseline": taus,
        "top_k": cfg.stability_top_k,
        "top_k_overlap_vs_baseline": overlaps,
        "samples": sample_records,
    }
    _write_json(Path(cfg.output_dir) / "stability_report.json", report)
    passed = report["mean_tau"] >= 0.7 and report["min_tau"] >= 0.6
    return passed, report, rankings[0]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="CausalHeadRank PoC")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--n-images", type=int, default=100)
    parser.add_argument("--model-name", default="vit_base_patch16_dinov3")
    parser.add_argument("--fallback-model", default="vit_base_patch14_dinov2")
    parser.add_argument("--output-dir", default="experiments/causal_headrank_poc_v2")
    parser.add_argument("--metric", choices=["logit_diff", "kl_div", "feature_diff"], default="logit_diff")
    parser.add_argument("--max-heads", type=int, default=144)
    parser.add_argument("--no-pretrained", action="store_true", help="Use random weights for wiring checks")
    parser.add_argument("--fake-data", action="store_true", help="Use synthetic images instead of CIFAR-100")
    parser.add_argument("--skip-probe", action="store_true", help="Wiring-only mode; requires --metric feature_diff")
    parser.add_argument("--probe-train-images", type=int, default=5000)
    parser.add_argument("--probe-val-images", type=int, default=1000)
    parser.add_argument("--probe-batch-size", type=int, default=32)
    parser.add_argument("--probe-epochs", type=int, default=100)
    parser.add_argument("--probe-min-accuracy", type=float, default=0.10)
    parser.add_argument("--stability-repeats", type=int, default=3)
    parser.add_argument("--stability-top-k", type=int, default=20)
    parser.add_argument("--sweep-batch-size", action="store_true")
    parser.add_argument("--skip-q2", action="store_true", help="Skip 10-head measurable-effect gate")
    parser.add_argument("--skip-q3", action="store_true", help="Skip stability test")
    parser.add_argument("--skip-q4", action="store_true", help="Skip runtime estimation")
    parser.add_argument("--skip-q5", action="store_true", help="Skip memory profile")
    args = parser.parse_args()

    if args.skip_probe and args.metric != "feature_diff":
        parser.error("--skip-probe is wiring-only and requires --metric feature_diff")
    if args.stability_repeats < 2:
        parser.error("--stability-repeats must be at least 2")

    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print("  [device] CUDA unavailable, using CPU")
        device = "cpu"

    cfg = PocConfig(
        seed=args.seed,
        device=device,
        batch_size=args.batch_size,
        n_images=args.n_images,
        model_name=args.model_name,
        fallback_model=args.fallback_model,
        pretrained=not args.no_pretrained,
        output_dir=args.output_dir,
        metric=args.metric,
        probe_train_images=args.probe_train_images,
        probe_val_images=args.probe_val_images,
        probe_batch_size=args.probe_batch_size,
        probe_epochs=args.probe_epochs,
        probe_min_accuracy=args.probe_min_accuracy,
        stability_repeats=args.stability_repeats,
        stability_top_k=args.stability_top_k,
    )
    set_seed(cfg.seed)
    write_environment(cfg.output_dir)
    results: dict[str, bool | None] = {
        "Q1": None,
        "Q0_probe": None,
        "Q2": None,
        "Q3": None,
        "Q4": None,
        "Q5": None,
    }
    details: dict[str, object] = {}
    scored_for_runtime = None

    print("\n=== Q1: model discovery and nnsight one-head equivalence ===")
    try:
        model, head_specs = load_model(cfg)
        print_hook_table(head_specs)
        hook_manifest = write_hook_manifest(head_specs, cfg.output_dir)
        expected = 144
        generator = torch.Generator(device="cpu").manual_seed(cfg.seed)
        validation_inputs = torch.randn(2, 3, 224, 224, generator=generator).to(cfg.device)
        equivalence = validate_nnsight_equivalence(
            model,
            head_specs[0],
            validation_inputs[:1],
            validation_inputs[1:],
            cfg.device,
        )
        _write_json(Path(cfg.output_dir) / "nnsight_equivalence.json", equivalence)
        results["Q1"] = len(head_specs) == expected and equivalence["passed"]
        details["Q1"] = {
            "discovered_heads": len(head_specs),
            "expected_heads": expected,
            "hook_manifest": str(hook_manifest),
            "equivalence": equivalence,
        }
        print(f"  discovered: {len(head_specs)}/{expected} heads")
        print(f"  direct vs nnsight max abs: {equivalence['direct_vs_nnsight_max_abs']:.3e}")
        print(f"  -> {'PASS' if results['Q1'] else 'FAIL'}")
        if not results["Q1"]:
            raise RuntimeError("nnsight equivalence gate failed")
    except Exception as exc:
        report = write_failure_report(cfg.output_dir, exc)
        print(f"  -> FAIL ({exc})")
        print(f"  failure report: {report}")
        results["Q1"] = False
        return 1

    if not args.skip_probe:
        print("\n=== Q0: fit class-aware CIFAR-100 readout ===")
        try:
            accuracy = fit_cifar100_probe(model, cfg)
            results["Q0_probe"] = accuracy >= cfg.probe_min_accuracy
            details["Q0_probe"] = {"validation_accuracy": accuracy, "minimum": cfg.probe_min_accuracy}
            print(f"  validation accuracy: {accuracy:.2%}")
            print(f"  -> {'PASS' if results['Q0_probe'] else 'FAIL'} (>= {cfg.probe_min_accuracy:.0%})")
            if not results["Q0_probe"]:
                _write_json(Path(cfg.output_dir) / "results.json", {"results": results, "details": details, "verdict": "NO-GO"})
                return 1
        except Exception as exc:
            report = write_failure_report(cfg.output_dir, exc, model)
            print(f"  -> FAIL ({exc})")
            print(f"  failure report: {report}")
            results["Q0_probe"] = False
            return 1
    else:
        print("\n=== Q0: SKIPPED (explicit feature-space wiring mode) ===")

    head_specs = head_specs[: min(args.max_heads, len(head_specs))]

    print("\n=== Loading held-out images ===")
    images, labels, sample_indices = load_images(cfg, fake_data=args.fake_data)
    details["dataset"] = {"split": "synthetic" if args.fake_data else "test", "indices": sample_indices}
    print(f"  loaded {images.shape[0]} stratified images on {cfg.device}")

    if args.sweep_batch_size:
        run_batch_sweep(model, head_specs, images, labels, cfg)

    if not args.skip_q2:
        q2_label = "class-aware" if cfg.metric != "feature_diff" else "feature-space wiring"
        print(f"\n=== Q2: measurable {q2_label} patching effect ===")
        try:
            q2_heads = head_specs[: min(10, len(head_specs))]
            df_q2 = score_all_heads(model, q2_heads, images, labels, cfg, checkpoint_name="q2_head_scores.csv")
            mean_score = float(df_q2["causal_score"].mean())
            q2_threshold = 1e-6 if cfg.metric != "feature_diff" else 1e-12
            results["Q2"] = mean_score > q2_threshold
            details["Q2"] = {
                "mean_score": mean_score,
                "heads": len(q2_heads),
                "threshold": q2_threshold,
            }
            scored_for_runtime = df_q2
            print(f"  mean target-class difference over {len(q2_heads)} heads: {mean_score:.6e}")
            print(f"  -> {'PASS' if results['Q2'] else 'FAIL'} (> {q2_threshold:.0e})")
        except Exception as exc:
            report = write_failure_report(cfg.output_dir, exc, model)
            print(f"  -> FAIL ({exc})")
            print(f"  failure report: {report}")
            results["Q2"] = False

    if not args.skip_q3 and results.get("Q2") is not False:
        print("\n=== Q3: independent-subset rank stability ===")
        try:
            passed, stability, scored_for_runtime = run_stability_test(
                model,
                head_specs,
                images,
                labels,
                sample_indices,
                cfg,
                fake_data=args.fake_data,
            )
            results["Q3"] = passed
            details["Q3"] = stability
            print(f"  tau mean={stability['mean_tau']:.3f}, minimum={stability['min_tau']:.3f}")
            print(f"  top-{stability['top_k']} overlaps: {stability['top_k_overlap_vs_baseline']}")
            print(f"  -> {'PASS' if passed else 'FAIL'} (mean >= 0.7 and minimum >= 0.6)")
        except Exception as exc:
            report = write_failure_report(cfg.output_dir, exc, model)
            print(f"  -> FAIL ({exc})")
            print(f"  failure report: {report}")
            results["Q3"] = False

    if not args.skip_q4:
        print("\n=== Q4: runtime estimation ===")
        if scored_for_runtime is None:
            print("  -> SKIPPED (no scoring results available)")
        else:
            estimate = estimate_total_runtime(scored_for_runtime, total_heads=144)
            results["Q4"] = estimate["estimate_seconds"] <= 12 * 3600
            details["Q4"] = estimate
            print(
                "  estimate: "
                f"{format_time(estimate['estimate_seconds'])} "
                f"[{format_time(estimate['low_seconds'])}, {format_time(estimate['high_seconds'])}] "
                f"({estimate['method']})"
            )
            print(f"  -> {'PASS' if results['Q4'] else 'FAIL'} (<= 12h)")

    if not args.skip_q5:
        print("\n=== Q5: memory profile ===")
        peak = log_memory("global peak")
        if scored_for_runtime is not None and not scored_for_runtime.empty:
            peak = max(peak, float(scored_for_runtime["peak_memory_gb"].max()))
        results["Q5"] = peak < 11.0
        details["Q5"] = {"peak_memory_gb": peak, "budget_gb": 11.0}
        print(f"  peak memory: {peak:.2f} GB")
        print(f"  -> {'PASS' if results['Q5'] else 'FAIL'} (< 11 GB)")

    print("\n" + "=" * 50)
    print("CausalHeadRank PoC Results")
    print("=" * 50)
    for question, passed in results.items():
        print(f"  {question}: {'SKIPPED' if passed is None else ('PASS' if passed else 'FAIL')}")

    research_mode = not args.skip_probe and cfg.metric != "feature_diff"
    verdict = determine_verdict(results, research_mode=research_mode)
    print(f"\n  Verdict: {verdict}")
    _write_json(Path(cfg.output_dir) / "results.json", {
        "results": results,
        "details": details,
        "metric": cfg.metric,
        "research_mode": research_mode,
        "verdict": verdict,
    })
    return 1 if verdict == "NO-GO" else 0


if __name__ == "__main__":
    sys.exit(main())
