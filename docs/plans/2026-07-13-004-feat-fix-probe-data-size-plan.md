---
title: Fix Probe Dataset Size and Re-Run Pruning Benchmark
type: feat
status: active
date: 2026-07-13
origin: docs/brainstorms/keystone-neurons-requirements.md
---

# Fix Probe Dataset Size and Re-Run Pruning Benchmark

## Overview

The current pruning evaluation uses only 100 eval images for a 100-class CIFAR-100 probe — that's ~1 image per class. Probe accuracy collapses to noise floor (2-11%) regardless of pruning quality. This plan increases probe data to 5000 images (50 per class), re-runs the benchmark at all 4 sparsity ratios, and produces meaningful accuracy comparisons.

---

## Requirements Trace

- R1. Increase probe training data from 100 to 5000 images
- R2. Increase probe epochs from 10 to 50 for convergence
- R3. Re-run benchmark at 25%, 50%, 75%, 90% sparsity with 1 seed
- R4. Produce Pareto curve comparing all methods

---

## Implementation Units

- U1. **Update eval function with configurable probe size and epochs**

**Goal:** Make probe training data size and epochs configurable in the pruning orchestrator.

**Requirements:** R1, R2

**Dependencies:** None

**Files:**
- Modify: `scripts/run_pruning.py` (add `--probe-train-images` and `--probe-epochs` args)

**Approach:**
- Add `--probe-train-images` (default 2500) and `--probe-epochs` (default 50) CLI args
- Pass them to `_run_pruning_loop()` which uses them in probe fitting

**Verification:**
- `--probe-train-images 5000 --probe-epochs 50` flag accepted without error

- U2. **Re-run full benchmark**

**Goal:** Run pruning benchmark with adequate probe data at all 4 ratios.

**Requirements:** R3, R4

**Dependencies:** U1

**Files:**
- Execute: `scripts/run_pruning.py`

**Approach:**
- Run with `--skip-causal --n-images 50 --n-eval-images 5000 --probe-train-images 2500 --probe-epochs 50 --ratios "0.25,0.50,0.75,0.90" --seeds "42"`
- Reuses cached causal scores from previous run
- Generates results.json and Pareto curve

**Verification:**
- All 4 methods × 4 ratios have accuracy values
- Accuracy significantly above random (1%) at 25% sparsity
- Pareto curve shows meaningful degradation trend

---

## Risks

| Risk | Mitigation |
|------|------------|
| 5000-image probe extraction OOMs on 6GB VRAM | Use smaller batch_size (2) |
| Runtime exceeds 30 min for full run | Accept 1 seed instead of 3 |

---

## Sources

- Audit finding #1: probe is data-starved at 100 images
- Previous full_run: 200 eval images, 10 probe epochs
