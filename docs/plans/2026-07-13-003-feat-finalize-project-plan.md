---
title: Finalize Project — Experiment, Documentation, and Publication
type: feat
status: active
date: 2026-07-13
origin: docs/brainstorms/keystone-neurons-requirements.md
---

# Finalize Project — Experiment, Documentation, and Publication

## Overview

The pipeline is built (pruning surgery, baselines, evaluation). This plan runs the full experiment with pretrained weights on CIFAR-100, generates results and plots, writes a README and paper draft, and pushes everything to GitHub for arXiv/publication readiness.

---

## Problem Frame

All code exists but the experiment hasn't been run with real data. The project needs concrete results (Pareto curves, correlation metrics, keystone head distribution) to be publication-ready. The README is empty and there's no paper draft.

---

## Requirements Trace

- R1. Run full CIFAR-100 benchmark with pretrained DINOv3 at 3 seeds × 4 ratios × 4 methods
- R2. Generate Pareto curves, Kendall τ correlation plots, keystone head distribution
- R3. Write comprehensive README with results, setup, and usage
- R4. Write paper draft following the origin doc's outline
- R5. Push to GitHub with clean state

---

## Scope Boundaries

- Run experiment with pretrained weights on CIFAR-100
- Generate publication-quality plots
- README with badges, setup, usage, results
- Paper draft with results filled in
- MVTec, cross-model transfer, SparseViT/DepGraph — out of scope (future work)

---

## Implementation Units

- U1. **Run full CIFAR-100 experiment**

**Goal:** Execute `scripts/run_pruning.py` with pretrained weights on CIFAR-100 to produce real results.

**Requirements:** R1

**Dependencies:** None

**Files:**
- Execute: `scripts/run_pruning.py`

**Approach:**
- Run with `--n-images 100 --seed 42 --output-dir experiments/full_run` (single seed for speed)
- Confirm results.json, rankings.json, correlations.json, environment.json produced
- Verify all 4 methods × all ratios produce valid accuracy numbers

**Verification:**
- Results JSON has accuracy values for all methods and ratios
- Correlations JSON has Kendall tau values
- No OOM errors

- U2. **Generate plots and analysis**

**Goal:** Produce Pareto curves, correlation scatter plots, and keystone head distribution.

**Requirements:** R2

**Dependencies:** U1

**Files:**
- Execute: `src/keystone/visualization.py` (already built)
- Create: `experiments/full_run/pareto_curve.png`, `experiments/full_run/head_distribution.png`

**Approach:**
- Run `plot_pareto_curve()` on `results.json` → save to experiments dir
- Run `plot_head_distribution()` on causal scores → save to experiments dir
- Generate a summary table of results

**Verification:**
- PNG files exist and contain visible plots
- Pareto curve shows all 4 methods with decreasing accuracy at higher sparsity

- U3. **Write README**

**Goal:** Comprehensive project README on GitHub.

**Requirements:** R3

**Dependencies:** U1, U2

**Files:**
- Create: `README.md`

**Approach:**
- Title: Keystone — Causal Importance-Guided Structured Pruning for Vision Transformers
- Badges: Python 3.13, PyTorch, tests passing, license
- Sections: Overview, Installation, Quick Start, How It Works (diagram), Results (with plots), Project Structure, Citation

**Verification:**
- README renders correctly on GitHub
- All commands work when copy-pasted

- U4. **Write paper draft**

**Goal:** arXiv-ready paper draft following the origin doc's outline.

**Requirements:** R4

**Dependencies:** U1, U2

**Files:**
- Create: `paper/keystone-paper.md` or `paper/main.tex`

**Approach:**
- Follow the origin doc's 9-section outline (Introduction → Conclusion)
- Fill in results from U1
- Include Pareto curves as figures
- Target: ~6-8 pages, ICLR workshop format

**Verification:**
- All sections present
- Results section has real numbers
- Bibliography includes CAP, Vi-CD, SparseViT, DepGraph

- U5. **Final push**

**Goal:** Clean repo state, push everything to GitHub.

**Requirements:** R5

**Dependencies:** U1, U2, U3, U4

**Files:**
- Modify: `README.md`, `paper/`

**Approach:**
- Add paper/ to tracked files
- Update .gitignore if needed
- Commit and push to origin master

**Verification:**
- GitHub repo shows README, results, paper
- All links work

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Full experiment OOMs on 6GB VRAM | Run with `--batch-size 2` or fewer eval images |
| Pretrained DINOv3 download fails | Use DINOv2 fallback |
| CIFAR-100 download slow | Already cached in data/ dir |

---

## Sources & References

- **Origin document:** [docs/brainstorms/keystone-neurons-requirements.md](../brainstorms/keystone-neurons-requirements.md)
- Related plans: `docs/plans/2026-07-13-002-feat-full-structured-pruning-pipeline-plan.md`
