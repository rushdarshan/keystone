# Keystone — Causal Importance-Guided Structured Pruning for Vision Transformers

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-ee4c2c.svg)](https://pytorch.org/)
[![Tests](https://img.shields.io/badge/tests-40%20passed-green.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

## Overview

Keystone investigates whether **activation-patching-derived causal importance** provides a complementary pruning signal for structured compression of Vision Transformers. In ecology, a keystone species has disproportionate influence on its ecosystem — removing it causes cascading collapse. Similarly, certain attention heads in ViTs carry outsized causal importance that conventional pruning metrics (magnitude, gradient) can systematically miss.

CausalHeadRank scores each of 144 attention heads in DINOv3 ViT-B/16 via activation patching, then physically removes the lowest-scoring heads at 25-90% sparsity ratios and measures accuracy drop. The pipeline compares causal importance against magnitude, gradient, and random baselines to answer: **do causal scores beat conventional metrics for pruning decisions?**

## Installation

```bash
git clone https://github.com/rushdarshan/keystone.git && cd keystone
pip install torch torchvision nnsight timm scipy scikit-learn matplotlib pandas tqdm pytest
```

## Quick Start

```bash
# Feasibility PoC (validates nnsight hooks, scoring, stability)
python scripts/run_poc.py

# Quick pruning wiring check (fast, no pretrained weights)
python scripts/run_pruning.py --quick --no-pretrained

# Full pruning experiment
python scripts/run_pruning.py --output-dir experiments/my_run
```

## How It Works

```
  CIFAR-100               CausalHeadRank                Structured Pruning          Evaluation
  ────────                ──────────────                ─────────────────          ──────────
  Clean/corrupt  ──>   Score all 144 heads     ──>   Rank heads by         ──>   Pareto curves
  image pairs           via activation patching        causal importance          at 4 sparsity ratios
                              │                              │
                              ▼                              ▼
                       Stability check               Physically remove
                       (Kendall tau)                 heads + rebuild attn
```

1. **Score** — Patch each attention head's output with a corrupted activation from a different-class image. Measure the output change (logit difference, KL divergence).
2. **Compare** — Compute Kendall tau between causal scores and magnitude/gradient/random rankings. Identify "keystone heads" (high causal, low magnitude).
3. **Prune** — Physically slice QKV and projection weights to remove the lowest-ranked heads. Rebuild attention modules with reduced head count.
4. **Evaluate** — Measure post-prune accuracy, FLOPs, throughput on CIFAR-100. Plot Pareto curves across all methods.

## Results

**Feasibility PoC** — DINOv3 ViT-B/16, CIFAR-100, RTX 4050 (6.44 GB VRAM):

| Gate | Threshold | Result |
|------|-----------|--------|
| Q0 — Linear probe accuracy | ≥ 10% | **80.7%** |
| Q1 — Head discovery | 144 heads | **144/144** |
| Q2 — Measurable patching effect | — | **Pass** |
| Q3 — Ranking stability (Kendall τ) | ≥ 0.7 | **0.849** (mean) |
| Q4 — Runtime estimate | ≤ 12h | **198s** |
| Q5 — Peak VRAM | < 11 GB | **0.61 GB** |
| **Verdict** | | **GO** |

## Project Structure

```
src/keystone/
├── __init__.py            # Package metadata
├── config.py              # PocConfig dataclass
├── models.py              # DINOv3/DINOv2 loading
├── vit_adapters.py        # Head discovery and module mapping
├── data.py                # CIFAR-100 transforms, stratified sampling
├── patching.py            # Activation patching engine
├── nnsight_validation.py  # NN-sight equivalence validation
├── scoring.py             # Causal importance scoring + checkpointing
├── probe.py               # Linear probe training on frozen features
├── pruning.py             # Structured head removal surgery
├── baselines.py           # Magnitude, gradient, random scoring
├── evaluation.py          # Accuracy + efficiency measurement
├── analysis.py            # Kendall tau, compare_rankings, verdicts
├── visualization.py       # Pareto plots, head distribution
└── utils.py               # Seeding, memory logging, environment

scripts/
├── run_poc.py             # PoC orchestrator (6-gate validator)
└── run_pruning.py         # Pruning experiment orchestrator

tests/                     # 40 tests, all passing
```

## Citation

```bibtex
@misc{keystone2026,
  title  = {Keystone: Causal Importance-Guided Structured Pruning for Vision Transformers},
  author = {},
  year   = {2026},
  note   = {arXiv preprint}
}
```

## License

MIT
