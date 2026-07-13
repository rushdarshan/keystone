---
date: 2026-07-12
topic: interpretability-guided-compression
status: draft
iteration: 8
---

# Interpretability-Guided Structured Model Compression

**Framework:** Keystone Evaluation (protocol for causally-guided pruning)
**Algorithm:** CausalHeadRank — scores attention heads by activation-patching-derived causal importance for structured pruning decisions.
**Target:** College capstone / potential publication. Consumer GPU (12GB VRAM). Single student, 10-12 weeks.

## Problem Frame

Mechanistic interpretability has shown that individual components (neurons, attention heads) in neural networks carry outsized causal importance. Meanwhile, model compression (pruning) relies on weight magnitude or gradient-based importance — metrics that can miss structurally important but numerically small components and, as recent work shows (Gradient-Causal Gap, 2026), can systematically invert true importance.

Recent work has explored causal-guided pruning in language models (CC-Prune, CAP) and causal circuit discovery in Vision Transformers (Vi-CD). However, whether activation-patching-derived causal importance can serve as an effective structured pruning signal for Vision Transformers — with their different attention mechanisms, inductive biases, and downstream tasks — has received limited direct investigation.

This project investigates that question through a systematic empirical evaluation.

**Research question:** Does activation-patching-derived causal importance provide a complementary pruning signal — distinct from magnitude and gradient-based importance — for structured compression of Vision Transformers?

**Proposed contribution:** A systematic empirical evaluation of whether activation-patching-derived causal importance provides a complementary structured pruning signal for Vision Transformers — a question distinct from causal-guided LLM weight pruning (CAP, CC-Prune) and visual circuit discovery (Vi-CD).

### Building on Vi-CD's Methodology

Vi-CD (Żukowska et al., 2026) already solved key engineering challenges for activation patching in ViTs. Rather than reinventing these, we adopt their established pipeline:

| Vi-CD Component | How We Reuse | What We Add |
|-----------------|--------------|-------------|
| Clean/corrupted image construction (segmentation + inpainting) | Directly adopt | — |
| Activation patching on ViT components | Directly adopt | — |
| Graph simplification (attention-input nodes) | Directly adopt | — |
| Edge/head importance scoring | Adopt as input to our pipeline | **Importance ranking → structured pruning** |
| Faithfulness evaluation | Adopt for validation | **Pareto curves across pruning ratios** |
| Computational scaling | Use as baseline timing | **Pruning-specific metrics (FLOPs, params, throughput)** |

**Separation of concerns:** Vi-CD's pipeline ends where ours begins. They use activation patching to *discover circuits for interpretability*; we use the same importance signal to *make pruning decisions*. Our contribution starts after head importance is obtained.

### Comparison with Closest Prior Work

| Feature | CC-Prune | CAP | Vi-CD | Ours |
|---------|----------|-----|-------|------|
| Vision Transformer | ✗ (LLM) | ✗ (LLM) | ✓ (circuit disc.) | **✓ (pruning)** |
| Activation patching | ✓ | ✓ | ✓ | ✓ |
| Structured pruning | unclear | ✗ (unstructured) | ✗ | **✓** |
| Anomaly detection | ✗ | ✗ | ✗ | **✓** |
| Cross-task evaluation | ✗ | ✗ | ✗ | **✓** |
| Cross-model transfer (ViT families) | ✗ | ✗ | ✗ | **✓** |
| Causal vs magnitude/gradient | ✗ | ✗ | ✗ | **✓** |
| Systematic empirical comparison | ✗ | ✗ | ✗ | **✓** |

---

## Expected Contributions

1. **Framework** — A reproducible pipeline for evaluating causal-guided structured pruning in Vision Transformers, building on Vi-CD's activation patching methodology and extending it to compression.

2. **Empirical Study** — A comparison of causal, magnitude, gradient, and structure-based pruning signals for ViT attention heads, across pruning ratios from 25% to 90%.

3. **Analysis** — An investigation of the relationship between causal importance and conventional pruning metrics, including correlation structure and divergence patterns.

4. **Cross-model validation** — Testing whether causal-guided pruning transfers across ViT families (DINOv3, DINOv2 or ViT-B/16).

5. **Benchmark** — Evaluation on structured pruning quality (primary), classification (secondary), and anomaly detection (tertiary).

---

## Research Questions

- **RQ1 (Primary).** Does causal importance provide a structured pruning signal distinct from magnitude and gradient-based importance for ViT attention heads?
- **RQ2 (Primary).** How correlated is causal importance with weight magnitude across attention heads and layers (Kendall τ)?
- **RQ3 (Primary).** Does the relative advantage of causal-guided pruning (vs. magnitude) change across pruning ratios (25% → 90%)?
- **RQ4 (Cross-model).** Does causal importance transfer across ViT families (DINOv3 → DINOv2 / vanilla ViT-B/16)?
- **RQ5 (Task generalization).** How does causal-guided pruning affect downstream classification and anomaly detection performance?

---

## Hypotheses

- **H0 (null).** Causal importance offers no statistically significant improvement or complementary information over conventional pruning metrics.
- **H1.** Causal importance provides information not captured by weight magnitude: attention heads with low magnitude but high causal importance exist and are distributed across layers.
- **H2.** Kendall rank correlation between causal importance and weight magnitude is low (τ < 0.3), confirming the signals are complementary.
- **H3.** Causal-guided pruning preserves structured output quality at least competitively with magnitude-guided pruning at ≥50% sparsity across 3 seeds.

---

## Requirements

### Dataset & Task Setup
- R1. Use **CIFAR-100** for development and fast iteration (classification accuracy, ablation studies).
- R2. Use **MVTec AD** for the primary anomaly detection benchmark (AUROC, pixel AUROC).
- R3. Optionally use **ImageNet-100** for scalability if time permits.

### Model & Framework
- R4. Target model: **DINOv3 ViT-B/16 distilled** (86M params, 12 layers × 12 heads = 144 heads). Fallback: **DINOv2 ViT-B/14** if nnsight tracing is unstable on DINOv3.
- R5. Causal tracing via **nnsight** for activation patching on ViT components.
- R6. Implement ACDC-style algorithm ported from LLMs to ViTs: patch each head, measure metric drop.

### Pruning Method
- R7. Score all attention heads by causal importance via activation patching. Prune lowest-scoring heads at multiple ratios (25%, 50%, 75%, 90%).
- R8. Structured pruning with dependency awareness (heads + associated MLP neurons). Neuron-level hierarchical analysis deferred to Phase B / Future Work.
- R9. Repeat on a second ViT family (DINOv2 or vanilla ViT-B/16) for cross-model transfer.

### Baselines (Complete Taxonomy)
- R10. **Random pruning** — lower bound.
- R11. **Magnitude pruning** — weight-magnitude-based.
- R12. **Gradient/Taylor pruning** — gradient-based importance.
- R13. **SparseViT** — learned importance + structured ViT pruning SOTA.
- R14. **DepGraph** — dependency-aware structured pruning.
- R15. Extended (if time): WD-Pruning (shows magnitude ≠ importance).

### Evaluation Protocol (3 Stages)
- R16. **Stage 1 (Primary — structured pruning quality):** Post-hoc prune, freeze weights. Measure accuracy/quality on validation set directly. Pareto curve: sparsity vs. performance.
- R17. **Stage 2 (Classification generalization):** Linear probe on frozen pruned features → classification accuracy.
- R18. **Stage 3 (Anomaly detection):** Extract features from pruned model → kNN/Mahalanobis AD on MVTec. AD is supporting evidence, not primary eval.

### Metrics
- R19. Pruning ratio vs. accuracy/AUROC Pareto curve (5+ ratios).
- R20. FLOPs reduction, parameter count, throughput (inferences/sec), peak VRAM.
- R21. Kendall rank correlation between causal importance and weight magnitude.
- R22. Distribution of keystone heads across layers.
- R23. Paired t-test or Wilcoxon signed-rank between magnitude vs. keystone at each ratio.

### Reproducibility
- R24. Fixed seeds (3 minimum). Report mean ± std.
- R25. All code, configs, and results tracked in project repo.

---

## Success Criteria

- **Primary (falsifiable, H3):** At ≥50% sparsity, causal-guided pruning preserves structured output competitively with magnitude-guided pruning across 3 seeds.
- **Primary (H1, H2):** Causal importance has low rank correlation with magnitude (Kendall τ < 0.3). Heads with low magnitude but high causal importance exist and are identifiable.
- **Cross-model (RQ4):** Causal importance rankings show non-trivial overlap across ViT families (Jaccard > 0.3 for top-k heads), or divergence is explainable.
- **Framework contribution (fallback):** Even if causal-guided pruning does not beat magnitude, contributions hold: (1) framework for applying activation patching to ViT compression, (2) empirical comparison of causal vs. traditional importance, (3) cross-model transfer analysis.
- **Handoff:** Another researcher can reproduce all experiments from repo and configs.

---

## Go / No-Go Criteria (Feasibility PoC)

Run 2-3 day PoC before committing to full project. Pass all four criteria for Go:

| # | Criterion | Measurement | Fallback if Fails |
|---|-----------|-------------|-------------------|
| 1 | nnsight hooks DINOv3 correctly | Forward pass succeeds with intervention on ≥1 head | Switch to DINOv2 (more mature ecosystem) |
| 2 | Head importance rankings are stable across seeds | Kendall τ > 0.7 between two runs with different image subsets | Increase image count or switch to Integrated Gradients |
| 3 | Runtime is practical | ≤5 min per head for scoring (144 heads ≈ 12 hours) | Reduce batch size, use smaller image subset |
| 4 | Memory fits in VRAM | Peak < 11 GB on target GPU | Reduce batch size or image resolution |

---

## Ablation Plan

| Experiment | Purpose | What Varies |
|------------|---------|-------------|
| Different pruning ratios (0%–90%) | Sensitivity to sparsity | Ratio |
| Different causal scoring metrics (logit diff, KL div, loss change) | Robustness of importance signal | Scoring formula |
| Random image subsets for patching | Stability of causal scores | Image seed |
| Per-layer analysis | Layer dependence of keystone distribution | Layer index |
| Cross-model transfer (DINOv3 → DINOv2 / ViT-B/16) | Generality of pruning signal | Model family |
| Overlap analysis (top-k Jaccard, Kendall τ, Spearman ρ) | Whether causal importance is truly distinct from magnitude/gradient | k threshold |
| 3 random seeds | Reproducibility | Training seed |
| kNN vs. Mahalanobis AD | Task generalization | AD method |

---

## Threats to Validity

- **Internal validity:** Activation patching provides an approximation of causal contribution, not ground-truth causal effect. Scores depend on the choice of patching distribution (replacement with mean vs. Gaussian vs. swapped example).
- **External validity:** Results are limited to DINOv3, DINOv2, and ViT-B on vision tasks. Cross-model transfer experiment (RQ4) partially addresses this. Generalization to CNNs, ViT-L, and language models is untested.
- **Construct validity:** AUROC measures detection separability but may not capture fine-grained representation quality. Metrics like effective rank or intrinsic dimension may provide complementary signal.
- **Statistical conclusion validity:** 3 seeds provides minimum statistical power. Paired comparisons reduce variance but effect size may still have wide confidence intervals.
- **Compute validity:** Consumer GPU (12GB) limits maximum batch size, number of patching images, and model scale. Results may not replicate at production scale.

---

## Compute Analysis (to report)

- Total GPU hours per experiment
- Peak VRAM during activation patching
- Time per head for causal scoring (with batch size)
- Inference latency: unpruned vs. pruned at each ratio
- FLOPs per forward pass at each sparsity level
- Energy estimate (extrapolate from GPU TDP × runtime)

---

## Paper Outline

```
1. Introduction
2. Related Work (pruning, mechanistic interpretability, ViT circuit discovery)
3. CausalHeadRank (framework: activation patching → importance ranking → structured pruning)
4. Experimental Setup (models, datasets, baselines, metrics)
5. Results
   5.1 RQ1: Causal vs. magnitude/gradient importance
   5.2 RQ2: Correlation between importance signals
   5.3 RQ3: Pruning ratio Pareto curves
   5.4 RQ4: Cross-model transfer
   5.5 RQ5: Classification and AD downstream
6. Ablation Studies (scoring metric, layer analysis, AD method)
7. Threats to Validity
8. Discussion
9. Conclusion
```

---

## Scope Boundaries

### In Scope (V1)
- DINOv3 ViT-B/16 (DINOv2 or vanilla ViT-B/16 as secondary for cross-model transfer).
- Head-level pruning only. Neuron-level analysis deferred.
- CIFAR-100 (classification) + MVTec AD (anomaly detection). ImageNet-100 optional.
- Structured pruning only (no unstructured sparsity).
- Post-hoc evaluation (no training-time pruning).

### Deferred to Phase B / Future Work
- Neuron-level hierarchical analysis (head → MLP neurons).
- ImageNet-100 at scale.
- WD-Pruning baseline.
- Quantization-aware pruning.
- Pruning + distillation combined.

### Outside Scope
- No new model architecture.
- No LLM experiments.
- No edge deployment.
- No real-time optimization beyond FLOPs/throughput.

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Project name | Interpretability-Guided Structured Model Compression | Framework name, not algorithm nickname |
| CausalHeadRank naming | Algorithm: activation-patching-based head importance scoring | Describes what it does |
| Research narrative | "Causal importance provides a complementary pruning signal" | Peer-review safe framing |
| Hypothesis framing | H1-H3 with falsifiable predictions | Follows ML paper structure |
| Dataset strategy | CIFAR-100 (dev) + MVTec AD (primary) | Fast iteration + respected benchmark |
| Evaluation protocol | 3-stage (pruning quality → classification → AD) | Compression is primary contribution |
| Pruning granularity | Heads only (V1). Neurons deferred | Keeps V1 focused and publishable |
| Causal tracing tool | nnsight (DINOv2 fallback) | Mature tool + safer backup |
| Statistical testing | Paired t-test / Wilcoxon | Stronger conclusions |
| Baseline taxonomy | Magnitude, gradient, structural, causal | Complete comparison spectrum |

---

## Dependencies / Assumptions

- **nnsight** works with DINOv3 ViT-B/16 (to be verified in PoC). DINOv2 available as verified fallback.
- DINOv3/DINOv2 ViT-B fits in 12GB VRAM with nnsight overhead (~86M / 86M params).
- MVTec AD license (CC BY-NC-SA 4.0) compatible with publication.
- User has or can access a CUDA GPU with ≥8GB VRAM.

---

## Outstanding Questions

### Resolve Before Planning

- **Feasibility:** Does nnsight activation patching work stably on DINOv3 ViT-B/16? (See Go/No-Go criteria above.)
- **Literature gap (status: partially filled):** CAP (2606.19350) — LLM unstructured weight pruning. Vi-CD (2604.14477) — ViT circuit discovery, not pruning. CC-Prune (ikari12) — GitHub-only, LLM-targeted, no peer review. Gap stands: no published work evaluates activation-patching-guided structured pruning in ViTs.

### Deferred to Planning

- [R5] Exact batch size for nnsight activation patching (depends on GPU VRAM).
- [R13-R14] SparseViT and DepGraph integration strategy (existing repos vs reimplement).
- [R16] kNN vs Mahalanobis for AD evaluation.
- [R7] Causal importance scoring formula (logit diff, KL divergence, or loss change).

---

## Next Steps

1. **Literature gap audit** (1-2 days): Targeted search for activation patching + ViT pruning.
2. **Feasibility PoC** (2-3 days): Verify nnsight + DINOv3 against Go/No-Go criteria.
3. If both pass → `-> /ce-plan` for structured implementation planning.
