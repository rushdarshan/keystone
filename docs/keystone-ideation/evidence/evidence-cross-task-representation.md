# Evidence Dossier: Cross-task representation preservation

Scope: continuing Keystone Neurons / causal-importance-guided structured pruning for ViTs.
Extraction only. Existing CAP and Vi-CD dossiers are used; their PDFs were not re-extracted.

## Project framing

- E01 [quote] "whether activation-patching-derived causal importance can serve as an effective structured pruning signal for Vision Transformers — with their different attention mechanisms, inductive biases, and downstream tasks — has received limited direct investigation." (docs/brainstorms/keystone-neurons-requirements.md:18)
- E02 [quote] "Anomaly detection | ✗ | ✗ | ✗ | **✓**" (docs/brainstorms/keystone-neurons-requirements.md:48)
- E03 [quote] "Cross-task evaluation | ✗ | ✗ | ✗ | **✓**" (docs/brainstorms/keystone-neurons-requirements.md:49)
- E04 [quote] "Cross-model transfer (ViT families) | ✗ | ✗ | ✗ | **✓**" (docs/brainstorms/keystone-neurons-requirements.md:50)
- E05 [quote] "Benchmark — Evaluation on structured pruning quality (primary), classification (secondary), and anomaly detection (tertiary)." (docs/brainstorms/keystone-neurons-requirements.md:66)
- E06 [quote] "RQ5 (Task generalization). How does causal-guided pruning affect downstream classification and anomaly detection performance?" (docs/brainstorms/keystone-neurons-requirements.md:76)

## Classification versus anomaly detection

- E07 [quote] "R1. Use **CIFAR-100** for development and fast iteration (classification accuracy, ablation studies)." (docs/brainstorms/keystone-neurons-requirements.md:92)
- E08 [quote] "R2. Use **MVTec AD** for the primary anomaly detection benchmark (AUROC, pixel AUROC)." (docs/brainstorms/keystone-neurons-requirements.md:93)
- E09 [quote] "R16. **Stage 1 (Primary — structured pruning quality):** Post-hoc prune, freeze weights. Measure accuracy/quality on validation set directly. Pareto curve: sparsity vs. performance." (docs/brainstorms/keystone-neurons-requirements.md:115)
- E10 [quote] "R17. **Stage 2 (Classification generalization):** Linear probe on frozen pruned features → classification accuracy." (docs/brainstorms/keystone-neurons-requirements.md:116)
- E11 [quote] "MVTec anomaly detection pipeline" (openspec/changes/causal-headrank-poc/design.md:19)
- E12 [quote] "Classification evaluation (linear probes, fine-tuning)" (openspec/changes/causal-headrank-poc/design.md:20)
- E13 [quote] "Cross-model transfer experiments" (openspec/changes/causal-headrank-poc/design.md:21)
- E14 [quote] "Paper figures or statistical analysis beyond Kendall τ" (openspec/changes/causal-headrank-poc/design.md:22)
- E15 [quote] "Structured pruning implementation (deferred to later milestone)" (openspec/changes/causal-headrank-poc/design.md:17)
- E16 [quote] "The system SHALL score each of the 144 attention heads in DINOv3 ViT-B/16 by causal importance using activation patching, producing a ranked list where higher scores indicate greater causal importance for the model's classification output." (openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:5)
- E17 [quote] "WHEN a single head is patched with a corrupted activation on 100 CIFAR-100 images" (openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:8)
- E18 [quote] "A large drop = high causal importance for that head." (openspec/changes/causal-headrank-poc/design.md:40)

## DINO representation and current workaround

- E19 [quote] "DINOv3 ViT-B/16 distilled (86M params, 12 layers × 12 heads = 144 heads). Fallback: **DINOv2 ViT-B/14** if nnsight tracing is unstable on DINOv3." (docs/brainstorms/keystone-neurons-requirements.md:97)
- E20 [quote] "Causal tracing via **nnsight** for activation patching on ViT components." (docs/brainstorms/keystone-neurons-requirements.md:98)
- E21 [quote] "DINOv3/DINOv2 ViT-B fits in 12GB VRAM with nnsight overhead (~86M / 86M params)." (docs/brainstorms/keystone-neurons-requirements.md:256)
- E22 [quote] "nnsight doesn't support DINOv3 hook points" and "Fallback to DINOv2 via same timm API." (openspec/changes/causal-headrank-poc/design.md:171)
- E23 [quote] "DINOv3 `vit_base_patch16_reg8_dino` may not exist in the installed timm version." (openspec/changes/causal-headrank-poc/design.md:185)
- E24 [code] `features = model(images.to(device))` and `if not isinstance(features, torch.Tensor) or features.ndim != 2: raise RuntimeError(...)` (src/keystone/probe.py:29-35)
- E25 [code] `classifier = torch.nn.Linear(train_features.shape[1], num_classes)` and `accuracy = float((predictions == val_labels).float().mean().item())` (src/keystone/probe.py:62-78)
- E26 [data] `validation_accuracy: 0.7420000433921814`, `train_images: 1000`, `validation_images: 500`, `train_test_overlap: 0` (experiments/stability_smoke_v2/probe_metrics.json:1-8)
- E27 [quote] "AUROC measures detection separability but may not capture fine-grained representation quality." (docs/brainstorms/keystone-neurons-requirements.md:174)
- E28 [quote] "Metrics like effective rank or intrinsic dimension may provide complementary signal." (docs/brainstorms/keystone-neurons-requirements.md:174)

## Transfer assumptions and contradictions

- E29 [quote] "Cross-model (RQ4): Causal importance rankings show non-trivial overlap across ViT families (Jaccard > 0.3 for top-k heads), or divergence is explainable." (docs/brainstorms/keystone-neurons-requirements.md:136)
- E30 [quote] "Results are limited to DINOv3, DINOv2, and ViT-B on vision tasks." (docs/brainstorms/keystone-neurons-requirements.md:173)
- E31 [quote] "Generalization to CNNs, ViT-L, and language models is untested." (docs/brainstorms/keystone-neurons-requirements.md:173)
- E32 [quote] "Cross-model transfer (DINOv3 → DINOv2 / ViT-B/16)" (docs/brainstorms/keystone-neurons-requirements.md:163)
- E33 [quote] "The PoC creates a separate `src/keystone/` package alongside the existing code, with no shared dependencies between the two." (openspec/changes/causal-headrank-poc/design.md:5)
- E34 [quote] "The PoC only implements activation patching (not attribution patching)" (openspec/changes/causal-headrank-poc/design.md:65)
- E35 [existing-dossier excerpt] "ViTs have patch tokens, class/task-specific visual losses, different attention/head roles, and often token/patch/channel pruning; the paper provides no ViT experiments or visual-task evidence." (tmp/compound-engineering/ce-ideate/da91d24b/evidence-user-research-cap.md:51)
- E36 [existing-dossier excerpt] "Vi-CD explicitly leaves ... non-classification tasks ... unexplored." (tmp/compound-engineering/ce-ideate/da91d24b/evidence-user-research-vi-cd.md:50)
- E37 [existing-dossier excerpt] "the paper does not establish that an edge circuit maps to a minimal or safe set of removable attention heads." (tmp/compound-engineering/ce-ideate/da91d24b/evidence-user-research-vi-cd.md:51)

## Benchmark and statistical design

- E38 [quote] "Different causal scoring metrics (logit diff, KL div, loss change) | Robustness of importance signal | Scoring formula" (docs/brainstorms/keystone-neurons-requirements.md:160)
- E39 [quote] "Random image subsets for patching | Stability of causal scores | Image seed" (docs/brainstorms/keystone-neurons-requirements.md:161)
- E40 [quote] "kNN vs. Mahalanobis AD | Task generalization | AD method" (docs/brainstorms/keystone-neurons-requirements.md:166)
- E41 [quote] "3 seeds provides minimum statistical power. Paired comparisons reduce variance but effect size may still have wide confidence intervals." (docs/brainstorms/keystone-neurons-requirements.md:175)
- E42 [quote] "R23. Paired t-test or Wilcoxon signed-rank between magnitude vs. keystone at each ratio." (docs/brainstorms/keystone-neurons-requirements.md:124)
- E43 [quote] "R24. Fixed seeds (3 minimum). Report mean ± std." (docs/brainstorms/keystone-neurons-requirements.md:127)
- E44 [code] `stability_repeats: int = 3` and `stability_top_k: int = 20` (src/keystone/config.py:27-28)
- E45 [code] The stability test refuses identical subsets and refuses changed class composition: `raise RuntimeError("stability subsets are identical; refusing to compute a tautological tau")`; `raise RuntimeError("stability subsets do not preserve class composition")` (scripts/run_poc.py:219-223)
- E46 [data] Both recorded score metadata files contain `record_count: 12` with different fingerprints: `430100...` and `e94553...` (experiments/stability_smoke_v2/q3_seed_42_scores.meta.json:1-4; experiments/stability_smoke_v2/q3_seed_43_scores.meta.json:1-4)
- E47 [data] First three causal scores differ between seed outputs: seed 42 `0.0850066, 0.0714121, 0.2256041`; seed 43 `0.0911201, 0.0591102, 0.2530968` (experiments/stability_smoke_v2/q3_seed_42_scores.csv:1-4; experiments/stability_smoke_v2/q3_seed_43_scores.csv:1-4)
- E48 [quote] "Kendall τ ≥ 0.7 (target) and ≥ 0.6 (minimum acceptable)" (openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:17)
- E49 [code] `kendall_tau()` merges by `head_idx` and computes correlation over `causal_score_a` and `causal_score_b` (src/keystone/analysis.py:20-23)
- E50 [quote] "At ≥50% sparsity, causal-guided pruning preserves structured output competitively with magnitude-guided pruning across 3 seeds." (docs/brainstorms/keystone-neurons-requirements.md:134)

## Recorded constraints and failure markers

- E51 [data] The recorded GPU is `NVIDIA GeForce RTX 4050 Laptop GPU` with `gpu_memory_gb: 6.44` (experiments/stability_smoke_v2/environment.json:1-10), versus the stated 12GB target (docs/brainstorms/keystone-neurons-requirements.md:12).
- E52 [quote] "Consumer GPU (12GB VRAM). Single student, 10-12 weeks." (docs/brainstorms/keystone-neurons-requirements.md:12)
- E53 [quote] "PermissionError: [WinError 32] ... q2_head_scores.meta.json.tmp ... is being used by another process" (experiments/smoke_v2/failure_report.md:3-7)
- E54 [quote] "Tried configured DINOv3 model." and "Tried configured DINOv2 fallback when model loading failed." (experiments/smoke_v2/failure_report.md:50-54)
- E55 [data] The equivalence record reports `passed: true`, `direct_vs_nnsight_max_abs: 0.0`, and `clean_vs_corrupt_head_max_abs: 2.8665771484375` (experiments/stability_smoke_v2/nnsight_equivalence.json:1-16).
- E56 [quote] "No comparison against structured pruning baselines (only Wanda for unstructured)" (papers/CC-Prune_GitHub_README.md:24-29)
- E57 [quote] "No cross-domain evaluation (single task/dataset)" (papers/CC-Prune_GitHub_README.md:24-29)
