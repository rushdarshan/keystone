---
title: feat: Implement Full Keystone Structured Pruning Pipeline
type: feat
status: active
date: 2026-07-13
origin: docs/brainstorms/keystone-neurons-requirements.md
---

# Implement Full Keystone Structured Pruning Pipeline

## Overview

Build the complete structured pruning pipeline on top of the existing CausalHeadRank PoC. This adds physical head removal surgery, three baseline pruning methods (magnitude, gradient, random), post-prune accuracy evaluation on CIFAR-100, Pareto analysis, and statistical comparison between causal and conventional importance metrics.

The PoC already scores all 144 heads by causal importance and validates ranking stability (Kendall τ ≥ 0.7). This plan extends that to: physically prune heads at 4 ratios (25%, 50%, 75%, 90%), compare against magnitude/gradient/random baselines, and produce the evidence needed to answer RQ1-RQ3 from the origin requirements doc.

---

## Problem Frame

The PoC proved activation patching can produce stable, measurable causal importance scores for ViT attention heads within 6GB VRAM. Now we need to determine whether those scores translate to effective structured pruning — i.e., does pruning low-causal-importance heads preserve accuracy better than pruning low-magnitude or low-gradient heads?

The origin doc frames this as H1-H3: causal importance is distinct from magnitude (τ < 0.3), and causal-guided pruning preserves output competitively at ≥50% sparsity.

---

## Requirements Trace

From `docs/brainstorms/keystone-neurons-requirements.md`:

- R7. Score all 144 attention heads by causal importance → prune lowest-scoring heads at 25%, 50%, 75%, 90% ratios
- R8. Structured pruning with dependency awareness (heads only; neurons deferred)
- R10. Random pruning baseline (lower bound)
- R11. Magnitude pruning baseline (weight-magnitude-based)
- R12. Gradient/Taylor pruning baseline (gradient-based importance)
- R16. Stage 1 (primary): Post-hoc prune, freeze weights, measure accuracy on CIFAR-100 validation
- R19. Pruning ratio vs accuracy Pareto curve (4+ ratios)
- R20. FLOPs reduction, parameter count, throughput (inferences/sec), peak VRAM
- R21. Kendall rank correlation between causal importance and weight magnitude
- R22. Distribution of keystone heads across layers
- R24. Fixed seeds (3 minimum). Report mean ± std.

**Origin acceptance examples:** H1 — heads with low magnitude but high causal importance exist. H2 — τ < 0.3 between causal and magnitude. H3 — causal-guided ≥ magnitude-guided at ≥50% sparsity across 3 seeds.

---

## Scope Boundaries

### In Scope
- Structured attention-head removal + QKV/output projection rebuild
- Magnitude, gradient, and random baseline scoring
- Physical pruning at 25%, 50%, 75%, 90% ratios
- Post-prune CIFAR-100 accuracy evaluation (frozen weights, no fine-tuning)
- Pareto curves: sparsity vs accuracy
- FLOPs, parameter count, throughput, VRAM measurement
- Kendall τ between causal and magnitude/gradient rankings
- Keystone head distribution per layer
- 3-seed reproducibility

### Deferred to Follow-Up Work
- MVTec AD anomaly detection evaluation
- Cross-model transfer (DINOv2)
- SparseViT and DepGraph external baselines
- Training-time (fine-tuning after pruning) evaluation
- Neuron-level hierarchical pruning

---

## Context & Research

### Relevant Code and Patterns

- `src/keystone/scoring.py:score_all_heads()` — produces head scores DataFrame; pruning module consumes this
- `src/keystone/patching.py:patch_head()` — monkey-patches attention forward; pruning module mirrors the attention surgery pattern
- `src/keystone/vit_adapters.py:discover_head_specs()` — maps head_idx → (layer, head_in_layer, module); pruning depends on this mapping
- `src/keystone/config.py:PocConfig` — extend with pruning ratios, baseline config, eval config
- `scripts/run_poc.py` — single-entry-point pattern; new script follows same conventions
- `src/keystone/utils.py:set_seed()`, `timer()` — reuse for reproducibility and timing

### Institutional Learnings

- `docs/keystone-ideation/continuation-checkpoint.md` — note: 6.44GB VRAM (not 12GB), novelty is narrower than originally claimed (CAP, Vi-CD exist), single-head scores miss group effects
- Previous smoke runs: 0.43 GB peak memory with 10 heads / 25 images on DINOv3

### External References

- CAP (arXiv:2606.19350) — LLM unstructured weight pruning via causal attribution
- Vi-CD (arXiv:2604.14477) — ViT circuit discovery via activation patching
- SparseViT (arXiv:2202.09268) — learned importance structured ViT pruning
- DepGraph (arXiv:2301.12900) — dependency-aware structured pruning

---

## Key Technical Decisions

- **Head removal surgery:** Modify ViT block's attention module in-place — slice QKV weight, output projection, and reduce `num_heads`. This mirrors `patch_head()`'s attention-forward replacement pattern but makes it permanent
- **Pruning ratios:** 25%, 50%, 75%, 90% of heads removed (keeps 108, 72, 36, 14 heads from 144)
- **Baseline scoring:** Magnitude = L2 norm of QKV+output weights per head. Gradient = L2 norm of weight × gradient product (Taylor first-order). Random = uniform shuffle of head indices
- **Evaluation:** Frozen post-prune forward pass on CIFAR-100 test set. No fine-tuning in this plan — isolates the pruning signal quality
- **Single script:** New `scripts/run_pruning.py` as the entry point, following `run_poc.py` conventions

---

## Implementation Units

### Phase A: Pruning Infrastructure

- U1. **Structured head removal surgery**

**Goal:** Physically remove attention heads from a ViT block, reducing `num_heads`, slicing QKV and output projection weights, and rebuilding the attention module.

**Requirements:** R7, R8

**Dependencies:** None (uses existing `discover_head_specs()` from `vit_adapters.py`)

**Files:**
- Create: `src/keystone/pruning.py`
- Test: `tests/test_pruning.py`

**Approach:**
- For each ViT block, locate the attention module (`blocks.N.attn`, EvaAttention)
- Given a list of head indices to keep, compute the keep mask for QKV channels
- Slice `qkv.weight`, `qkv.bias`, `proj.weight`, `proj.bias` along head-dimension axes
- Rebuild the EvaAttention module with updated `num_heads` and sliced weights
- Verify forward pass produces same shape output (batch, seq, embed_dim) with reduced head count
- Measure FLOPs reduction for verification

**Patterns to follow:**
- `src/keystone/patching.py:_attention_forward()` — already rewrites attention forward; surgery is the permanent version of the same pattern
- `src/keystone/vit_adapters.py:discover_head_specs()` — already maps heads to modules

**Test scenarios:**
- Happy path: prune 12 heads from a 12-head block → attention output shape unchanged, fewer FLOPs
- Edge case: prune 0 heads → module unchanged, no-op
- Edge case: prune all but 1 head from a layer (per-layer floor enforced by U3 orchestrator)
- Error path: invalid head indices → ValueError

**Verification:**
- Pruned model forward pass completes without error
- `num_heads` updated correctly
- QKV/proj weight shapes reflect new head count
- FLOPs decrease proportional to head removal ratio

- U2. **Baseline importance scoring**

**Goal:** Compute head importance scores via magnitude norm, gradient norm (Taylor first-order), and random shuffle.

**Requirements:** R10, R11, R12

**Dependencies:** None (uses existing `discover_head_specs()` from `vit_adapters.py` and ViT weight access patterns; no dependency on U1's pruning module)

**Files:**
- Create: `src/keystone/baselines.py`
- Test: `tests/test_baselines.py`

**Approach:**
- `score_magnitude(model, head_specs)`: For each head, compute L2 norm of QKV slice + output projection slice
- `score_gradient(model, head_specs, images, labels)`: Run one backward pass, compute L2 norm of weight × grad product per head (Taylor first-order)
- `score_random(n_heads, seed)`: Return shuffle of range(n_heads)
- All return same DataFrame format as `score_all_heads()`: [head_idx, layer, head_in_layer, score]

**Patterns to follow:**
- `src/keystone/scoring.py:score_all_heads()` — output DataFrame format
- `src/keystone/vit_adapters.py:discover_head_specs()` — head-to-module mapping

**Test scenarios:**
- Happy path: magnitude scores computed for all 144 heads, non-negative values
- Happy path: gradient scores differ from magnitude scores
- Happy path: random scores are a permutation of 0..143
- Edge case: zero-weight head → magnitude score = 0
- Error path: no_grad context during gradient scoring → grad is None, handled gracefully

**Verification:**
- All three scoring functions return DataFrames matching `score_all_heads()` schema
- Magnitude scores are deterministic (same weights = same scores)
- Random scores change with different seed

- U3. **Pruning orchestrator script**

**Goal:** Single entry point that scores heads (causal + baselines), prunes at 4 ratios, evaluates accuracy, and produces comparison artifacts.

**Requirements:** R7, R16, R19, R20, R24

**Dependencies:** U1, U2, U4, U5, U7 (and existing `score_all_heads()` in `scoring.py`)

**Files:**
- Create: `scripts/run_pruning.py`
- Modify: `src/keystone/config.py` (add pruning config)

**Approach:**
- CLI: `--seed`, `--n-images`, `--batch-size`, `--ratios "0.25,0.50,0.75,0.90"`, `--seeds "42,43,44"`, `--output-dir`
- Flow for each seed:
  1. Score heads via CausalHeadRank (reuse `score_all_heads()`)
  2. Score heads via magnitude, gradient, random baselines
   3. For each pruning ratio and each scoring method:
      a. Reload base model from checkpoint (pruning is destructive — never prune an already-pruned model)
      b. Select heads to keep using U7's `compare_rankings()` logic; enforce per-layer floor of ≥1 head
      c. Physically prune model using U1
      d. Evaluate accuracy via U4 on CIFAR-100 test set (frozen weights)
      e. Measure FLOPs, params, throughput, VRAM via U5
      f. Call `torch.cuda.empty_cache()` between prune/eval cycles to prevent fragmentation
      g. Record in results DataFrame
   4. Compute Kendall τ between rankings via U7's `compare_rankings()`
  5. Generate Pareto plots (sparsity vs accuracy)
  6. Print comparison table

**Patterns to follow:**
- `scripts/run_poc.py` — CLI conventions, gate structure, Pass/Fail table output

**Test scenarios:**
- Happy path: full 3-seed run produces results.csv with accuracy per ratio per method
- Edge case: ratio=0 (keep all heads) → accuracy matches unpruned baseline
- Integration: score → prune → evaluate pipeline completes without OOM on 6GB VRAM

**Verification:**
- Script runs end-to-end with `--n-images 25 --ratios 0.25,0.50`
- Produces `results.csv`, `rankings.csv`, `pareto_curve.png`
- 3-seed run reports mean ± std for each ratio/method

### Phase B: Evaluation and Analysis

- U4. **Post-prune accuracy evaluation**

**Goal:** Evaluate pruned model accuracy on CIFAR-100 test set without fine-tuning.

**Requirements:** R16, R19

**Dependencies:** None (takes a pruned model + dataloader; called by U3 orchestrator)

**Files:**
- Create: `src/keystone/evaluation.py`
- Test: `tests/test_evaluation.py`

**Approach:**
- `evaluate_accuracy(model, dataloader, device)`: Run forward passes, compute top-1 and top-5 accuracy
- Handles pruned model with potentially different head counts per layer
- Reports per-class accuracy for analysis

**Patterns to follow:**
- `src/keystone/probe.py:extract_features()` — batched inference pattern

**Test scenarios:**
- Happy path: unpruned DINOv3 on 100 CIFAR-100 test images → top-1 accuracy > 70%
- Happy path: pruned model at 50% ratio → accuracy lower than unpruned but > random (1%)
- Edge case: model with 0 heads in a layer → still runs, accuracy degraded

**Verification:**
- Evaluation runs without OOM
- Returns accuracy dict with top-1, top-5, per-class scores

- U5. **FLOPs, throughput, and memory measurement**

**Goal:** Measure computational efficiency of pruned models.

**Requirements:** R20

**Dependencies:** None (called by U3 orchestrator)

**Files:**
- Modify: `src/keystone/evaluation.py` (add `measure_efficiency()`) 
- Test: `tests/test_evaluation.py` (add efficiency tests)

**Approach:**
- FLOPs: Use `torch.profiler` with `profile_memory=True` on a single forward pass. Count FLOPs from profiler events for attention and MLP modules. Report total FLOPs and reduction vs unpruned.
- Throughput: Measure inferences/sec on batch=32, warmup=10, measured=100
- VRAM: `torch.cuda.max_memory_allocated()` before/after forward pass

**Test scenarios:**
- Happy path: FLOPs decrease monotonically with pruning ratio
- Edge case: VRAM at 90% pruning is less than at 0% pruning

**Verification:**
- FLOPs, throughput, and VRAM measurements are numeric and sensible

- U6. **Analysis and visualization**

**Goal:** Generate Pareto curves, Kendall τ correlation matrices, keystone head distribution plots.

**Requirements:** R19, R21, R22

**Dependencies:** U3, U4, U5

**Files:**
- Create: `src/keystone/visualization.py`
- Test: `tests/test_visualization.py`

**Approach:**
- `plot_pareto_curve(results_df)`: Accuracy vs sparsity for each method (4 curves)
- `plot_rank_correlation(causal_scores, magnitude_scores, gradient_scores)`: Scatter + τ annotation
- `plot_keystone_distribution(head_scores)`: Bar chart of keystone head count per layer
- All plots saved to output dir

**Patterns to follow:**
- `reverse_ablation/analysis/pareto.py` — existing Pareto plotting

**Test scenarios:**
- Happy path: Pareto plot shows monotonic accuracy degradation with sparsity
- Happy path: Kendall τ scatter shows correlation structure

**Verification:**
- All plots generated as PNG files in output directory
- Pareto plot legend distinguishes causal, magnitude, gradient, random

### Phase C: Statistical Comparison

- U7. **Kendall τ between importance rankings**

**Goal:** Quantify correlation between causal importance and magnitude/gradient importance.

**Requirements:** R21, H2

**Dependencies:** U2, U3

**Files:**
- Modify: `src/keystone/analysis.py` (add `compare_rankings()`)
- Test: `tests/test_analysis.py` (add ranking comparison tests)

**Approach:**
- `compare_rankings(causal_df, magnitude_df, gradient_df)`: Compute pairwise Kendall τ and Spearman ρ
- Report τ per-layer and overall
- Flag heads where causal score is high but magnitude is low (keystone candidates)

**Patterns to follow:**
- `src/keystone/analysis.py:kendall_tau()` — existing τ implementation

**Test scenarios:**
- Happy path: τ between causal and magnitude < 0.3 (supports H2)
- Happy path: τ between magnitude and gradient > 0.5 (both weight-based)
- Edge case: identical rankings → τ = 1.0

**Verification:**
- Pairwise τ matrix computed and saved
- Keystone head candidates identified (high causal, low magnitude)

---

## System-Wide Impact

- **Interaction graph:** `scoring.py` output → `pruning.py` input → `evaluation.py` measurement → `visualization.py` display. Each module consumes the previous module's output format.
- **Unchanged invariants:** Existing `src/keystone/` modules unchanged except `config.py` (add pruning fields) and `analysis.py` (add `compare_rankings()`). PoC pipeline (`scripts/run_poc.py`) continues to work independently.
- **VRAM budget:** All operations must stay within 6.44 GB. Pruning at 90% ratio reduces model size, which helps. Gradient scoring may spike VRAM (backward pass); use batch_size=1 if needed.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Attention surgery breaks forward pass | Verify pruned model output shape and values before evaluation |
| Gradient scoring OOMs on 6GB VRAM | Use batch_size=1, accumulate gradients across images |
| 90% pruning degrades accuracy to near-random | This is a valid result — report it, don't treat as failure |
| Baseline rankings are too correlated with causal (τ > 0.5) | Report honestly; this would falsify H2 but the framework contribution stands |
| SparseViT/DepGraph integration too complex for this phase | Deferred to separate milestone; manual comparison in this plan |

---

## Sources & References

- **Origin document:** [docs/brainstorms/keystone-neurons-requirements.md](../brainstorms/keystone-neurons-requirements.md)
- Related code: `src/keystone/scoring.py`, `src/keystone/patching.py`, `src/keystone/vit_adapters.py`
- Related plan: `docs/plans/2026-07-13-001-feat-validate-poc-plan.md` (PoC validation, completed)
- External: CAP (arXiv:2606.19350), Vi-CD (arXiv:2604.14477)
