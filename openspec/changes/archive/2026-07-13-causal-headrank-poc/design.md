## Context

The full research project requires scoring 144 attention heads by causal importance using activation patching. This PoC validates the core technical assumption before committing to the full implementation. The PoC is a single-phase gating milestone — pass and we proceed; fail and we document the failure mode and reassess.

The existing codebase has a `reverse_ablation/` research package and `run_experiment.py` CLI entry point. This PoC creates a separate `src/keystone/` package alongside the existing code, with no shared dependencies between the two.

## Goals / Non-Goals

**Goals:**
- Load DINOv3 ViT-B/16 and verify nnsight can hook attention heads
- Score all 144 heads by causal importance using activation patching on CIFAR-100
- Measure ranking stability (Kendall τ) across different image subsets
- Profile GPU memory and per-head runtime
- Produce a Go/No-Go report with 4 binary pass/fail results

**Non-Goals:**
- Structured pruning implementation (deferred to later milestone)
- Any baseline comparisons (SparseViT, DepGraph, magnitude, gradient)
- MVTec anomaly detection pipeline
- Classification evaluation (linear probes, fine-tuning)
- Cross-model transfer experiments
- Paper figures or statistical analysis beyond Kendall τ
- Optimization of any kind (correctness and measurement first)

## Decisions

### 1. Corruption strategy: cross-class swapping instead of Vi-CD inpainting

**Chosen:** For each CIFAR-100 image, pair it with a random image from a different class. The "corrupted" input is the paired image. Activation patching replaces the head's output on the clean forward with its output on the corrupted forward.

**Alternatives considered:**
- Vi-CD segmentation + inpainting: production-quality but requires an external segmentation model and adds a dependency. Unnecessary overhead for a PoC that only needs a measurable intervention effect.
- Gaussian noise corruption: simpler but provides a weaker causal signal and doesn't match the final paper's methodology.
- Mean ablation (replace with mean activation across dataset): commonly used in LLM circuit analysis but requires a separate forward pass to compute means.

**Rationale:** Cross-class swapping is the standard approach from ACDC and similar circuit discovery work. It guarantees that the corrupted input produces different activations (strong causal signal), requires zero additional dependencies, and matches what the full project will use for CIFAR-100.

### 2. Patching metric: logit difference

**Chosen:** Measure the change in the target class logit between clean and patched forward passes. A large drop = high causal importance for that head.

**Alternatives considered:**
- KL divergence between clean and patched output distributions: more sensitive but harder to interpret and more expensive to compute.
- Cross-entropy loss change: tied to a specific loss function, less general.
- Attention output norm: correlates with magnitude, not causal importance — defeats the purpose.

**Rationale:** Logit difference is the standard metric in Vi-CD and ACDC. It directly measures how much a head contributes to the model's classification decision. It's cheap to compute (no loss function needed) and interpretable (Δ logit directly relates to confidence).

### 3. Module structure: flat package with one patching module

**Chosen:**

```
src/keystone/
├── __init__.py
├── config.py                # dataclass for PoC config
├── models.py                # DINOv3 loader via timm
├── vit_adapters.py          # head spec discovery + nnsight hooks
├── patching.py              # activation patching engine (~200 lines)
├── scoring.py               # head scoring + ranking
├── analysis.py              # stability metrics (Kendall τ)
├── utils.py                 # seeding, memory profiling, logging
```

**Rationale:** For a ~300-line PoC, a single `patching.py` module is more navigable than a `patching/` directory with 4 files. The PoC only implements activation patching (not attribution patching), so subdirectories add hierarchy without benefit. If the full project needs EAP later, the module can be promoted to a package.

### 4. Incremental validation gates: 1 → 10 → 144 heads

**Chosen:** Score ONE head first. If that produces a measurable effect (Q2a), score TEN heads (Q2b). Only after 10 heads succeed, proceed to all 144 (Q3+). Each gate is a hard dependency — fail early, fail cheap.

**Rationale:** If nnsight's intervention mechanism has edge cases (broken gradients, wrong module reference, silent incorrect output), catching it on head 0 costs 2 seconds instead of 6 hours. The 10-head gate catches memory leaks and runtime instability before committing to the full sweep. This mirrors the review feedback: "treat each question as its own mini-project."

### 5. Memory management: sequential head processing with explicit cache clearing

**Chosen:** Process heads one at a time. After each head scores, explicitly clear CUDA cache and log peak memory. If memory grows monotonically across heads, we have a leak and fail the PoC.

**Rationale:** nnsight retains computational graphs for gradient computation. Scoring 144 heads sequentially without clearing cache may accumulate graph references and overflow 12GB by head 80. Explicit `torch.cuda.empty_cache()` after each head bounds memory to the worst single head, not 144× the average head. If this strategy fails (memory still grows), we switch to subprocess isolation (spawn a process per batch of heads, killing it after each batch).

### 6. Stability measurement: τ ≥ 0.7 target, ≥ 0.6 minimum

**Chosen:** Run scoring twice with different random image subsets (100 vs 200 images). Compute Kendall rank correlation between the two rankings. Target: τ ≥ 0.7. Minimum acceptable: τ ≥ 0.6.

**Rationale:** Kendall τ measures rank agreement regardless of absolute score values, which is what matters for pruning decisions (ordering heads by importance, not predicting exact importance values). τ ≥ 0.7 is the standard threshold for "strong agreement." However, this is a feasibility PoC — τ = 0.66 should trigger investigation (larger sample, different corruption, different metric), not project abandonment. The binary gate uses the minimum bar (0.6) and reports the target status separately.

### 7. Runtime estimation: warmup + linear model + 95% CI

**Chosen:** Skip the first 5 heads (warmup — CUDA init, graph compilation, cache warming). Fit a linear model (time_per_head = β₀ + β₁ × head_idx) on heads 6-15. Predict total = ∑(β₀ + β₁ × i) for i = 16..143, with 95% CI.

**Rationale:** Early heads are systematically slower (CUDA kernel compilation, cache misses). Using mean × 144 overestimates total because later heads benefit from warm caches and compiled graphs. A linear model with 95% CI accounts for both the warmup effect and the variance across heads.

### 8. Reproducibility: seed everything + environment logging

**Chosen:** `torch.manual_seed()`, `numpy.random.seed()`, `random.seed()` all set to the same value before each scoring run. CUDA deterministic mode enabled during scoring. Every experiment output directory contains `environment.json` with python/torch/timm/nnsight/CUDA/GPU versions.

**Rationale:** Without fixing seeds, two "identical" runs could differ due to random image sampling. Without environment metadata, a working setup cannot be reproduced months later. The environment.json takes 10 lines to generate and saves hours of debugging.

### 9. Checkpointing: save every 10 heads

**Chosen:** After every 10 heads, append to `head_scores.csv`. On restart, detect existing checkpoint and skip completed heads.

**Rationale:** Losing 6 hours of computation to an OOM on head 143 is unacceptable. A CSV checkpoint costs ~1KB per 10 heads and enables both crash recovery and incremental analysis.

### 10. Cache clean forward pass

**Chosen:** Before any patching, run all images through the model once and cache the clean logits (and optionally the hidden states at the patching layer). Reuse cached values for all 144 heads.

**Rationale:** Each head's patching currently requires 3 forward passes (clean, corrupted, patched). Clean is identical across all heads. Caching it saves 144 - 1 = 143 forward passes — a ~33% runtime reduction. The cache is a simple dict keyed by (image_index, layer_index).

### 11. Single entry point: scripts/run_poc.py

**Chosen:** A single Python script that runs all 5 PoC questions and prints a pass/fail table.

```
$ python scripts/run_poc.py --device cuda --seed 42

Results:
  Q1 (nnsight hook):       ✓ PASS (intervention successful)
  Q2a (1 head effect):     ✓ PASS (Δ logit = 0.42)
  Q2b (10 head stability): ✓ PASS (no leak detected)
  Q3 (144 head stability): ✓ PASS (Kendall τ = 0.82)
  Q4 (runtime):            ✓ PASS (linear estimate: 8.2h [7.1h, 9.5h])
  Q5 (memory):             ✓ PASS (peak = 4.7 GB)
```

**Rationale:** A single script that produces a structured report is more useful than 5 separate scripts. Each question can be run independently via `--skip-*` flags for debugging. The output format is deliberately machine-parseable (tab-separated values for each question result).

## Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    run_poc.py                                     │
│                                                                   │
│  1. Load DINOv3 via timm                                         │
│  2. Write environment.json to output_dir                          │
│  3. Wrap with nnsight (ndiff)                                     │
│  4. Build head_specs list (12 layers × 12 heads = 144 entries)   │
│                                                                   │
│  5. Load CIFAR-100 → paired_dataset (clean_img, corrupted_img)   │
│                                                                   │
│  ---- Gate 1: validate ONE head ----                             │
│  6. Score head 0: forward + patched → Δ logit                     │
│  7. If Δ logit < 0.001 → FAIL with failure_report.md             │
│                                                                   │
│  ---- Gate 2: validate TEN heads ----                             │
│  8. Score heads 1-9                                               │
│  9. If monotonic memory growth → FAIL with memory leak warning    │
│                                                                   │
│  ---- Full sweep (with checkpointing) ----                       │
│  10. For each head (10..143):                                     │
│      ├─ Reuse cached clean logits                                 │
│      ├─ Forward pass with intervention at head                    │
│      ├─ Compute Δ logit = |logit_clean - logit_patched|           │
│      ├─ Record score, peak memory, time                           │
│      ├─ torch.cuda.empty_cache()                                  │
│      └─ Every 10 heads: append to head_scores.csv                 │
│                                                                   │
│  11. Run 1-2 more times with different seeds/image subsets        │
│                                                                   │
│  12. Compute:                                                     │
│      ├─ Kendall τ between runs (report target + minimum)          │
│      ├─ Linear model for runtime (skip warmup heads, 95% CI)     │
│      ├─ Peak memory across all heads                              │
│      └─ Print pass/fail table                                     │
└──────────────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| nnsight doesn't support DINOv3 hook points | Medium | Critical (Q1 fail) | Fallback to DINOv2 via same timm API. If both fail, do manual hooks via PyTorch forward hooks. Generate failure_report.md with full diagnostics. |
| Memory grows across sequential heads (leak) | Medium | Critical (Q5 fail) | Subprocess isolation: fork per batch of 10 heads, collect scores, kill process, release all GPU memory. |
| Rankings are unstable (τ < 0.7) | Medium | High (Q3 fail) | Use minimum bar (τ ≥ 0.6) for binary gate. Investigate larger sample, different corruption, or different metric before declaring failure. |
| 144 heads × 5 min = 12h boundary case | Medium | High (Q4 fail) | Reduce image count per head (100 instead of 512). Report time-image tradeoff curve. Linear model with 95% CI gives earlier, more accurate estimate. |
| DINOv3 checkpoint download fails | Low | Medium | Use timm's built-in download with `check_hash=True`. Fallback: manually download and point `TIMM_CACHE_DIR`. |
| CIFAR-100 download fails | Low | Low | torchvision handles download. Fallback: 10 random images as minimal test. |
| Over-invest in PoC infrastructure (scope creep) | High | Medium | Strict 300-line target for src/keystone/. If exceeded, refactor before proceeding. |
| Head 143 OOM loses 6 hours of work | Medium | High | Checkpoint every 10 heads. On restart, resume from last checkpoint. |

## Open Questions

- Does `timm.models.vit_base_patch16_reg8_dino` expose attention heads as named modules for nnsight hooking? Need to inspect `model.named_modules()` to discover hook names. PoC will log all discovered hook points on start.
- What is the optimal batch size for 12GB VRAM with nnsight overhead? PoC will binary-search batch_size = [2, 4, 8, 16] during Q5.
- Does nnsight's `ndiff` context manager work with `torch.no_grad()` for inference-only patching? If not, PoC will use `ndiff` in eval mode with gradient computation disabled.
- DINOv3 `vit_base_patch16_reg8_dino` may not exist in the installed timm version. The PoC tries it first (via timm.list_models or try/except) and falls back to `vit_base_patch14_dinov2` if unavailable.
