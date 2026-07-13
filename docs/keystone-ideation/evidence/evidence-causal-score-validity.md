# Evidence Dossier: Causal-Score Validity

Extraction scope: continuing Keystone Neurons / causal-importance-guided structured pruning for Vision Transformers.

## Corruption construction

1. "For each CIFAR-100 image, pair it with a random image from a different class." — `openspec/changes/causal-headrank-poc/design.md:29`
2. "Cross-class swapping is the standard approach from ACDC and similar circuit discovery work." — `openspec/changes/causal-headrank-poc/design.md:36`
3. `def build_corrupt_indices(clean_labels: torch.Tensor) -> torch.Tensor:` — `src/keystone/patching.py:8`
4. `candidate = (current_idx + offset) % n` — `src/keystone/patching.py:83`
5. `if labels[candidate].item() != current_class: return candidate` — `src/keystone/patching.py:84-85`
6. `corrupt_indices = build_corrupt_indices(labels)` — `src/keystone/scoring.py:32`
7. `corrupt_batch = images[corrupt_indices[start_idx:end_idx]]` — `src/keystone/scoring.py:50`
8. "Vi-CD segmentation + inpainting: production-quality but requires an external segmentation model" — `openspec/changes/causal-headrank-poc/design.md:32`
9. "Gaussian noise corruption: simpler but provides a weaker causal signal" — `openspec/changes/causal-headrank-poc/design.md:33`
10. "Mean ablation (replace with mean activation across dataset)" — `openspec/changes/causal-headrank-poc/design.md:34`

## Target metric

11. "Measure the change in the target class logit between clean and patched forward passes." — `openspec/changes/causal-headrank-poc/design.md:40`
12. "a large drop = high causal importance for that head." — `openspec/changes/causal-headrank-poc/design.md:40`
13. `target_labels = labels[start_idx:end_idx] if cfg.metric == "logit_diff" else None` — `src/keystone/scoring.py:55`
14. `target = target_labels.to(device=clean_output.device, dtype=torch.long)` — `src/keystone/patching.py:54`
15. `return (clean_output[row, target] - patched_output[row, target]).abs()` — `src/keystone/patching.py:58`
16. `if metric == "kl_div":` — `src/keystone/patching.py:39`
17. `return F.kl_div(patched_log_probs, clean_log_probs.exp(), reduction="none").sum(dim=-1)` — `src/keystone/patching.py:42`
18. `target = clean_output.detach().abs().argmax(dim=-1)` — `src/keystone/patching.py:46`
19. "Attention output norm: correlates with magnitude, not causal importance — defeats the purpose." — `openspec/changes/causal-headrank-poc/design.md:45`
20. `"metric": "logit_diff"` — `experiments/pretrained_smoke_v2/results.json:60`
21. `"mean_score": 0.10699008777737617` — `experiments/pretrained_smoke_v2/results.json:31`
22. `"clean_vs_corrupt_head_max_abs": 2.8665771484375` — `experiments/pretrained_smoke_v2/results.json:17`

## Intervention semantics

23. "Replace one clean attention-head output with the paired corrupt output." — `src/keystone/patching.py:18`
24. `model(corrupt_input.to(device))` — `src/keystone/patching.py:35`
25. `capture["head"] = head_outputs[:, head_idx].detach()` — `src/keystone/patching.py:127`
26. `head_outputs[:, head_idx] = replacement.to(device=head_outputs.device, dtype=head_outputs.dtype)` — `src/keystone/patching.py:129`
27. `return model(clean_input.to(device))` — `src/keystone/patching.py:42`
28. `"direct_vs_nnsight_max_abs": 0.0` — `experiments/pretrained_smoke_v2/results.json:18`
29. `"baseline_vs_traced_max_abs": 0.0` — `experiments/pretrained_smoke_v2/results.json:15`
30. "Only after 10 heads succeed, proceed to all 144." — `openspec/changes/causal-headrank-poc/specs/nnsight-vit-integration/spec.md:29`
31. "Structured pruning implementation (deferred to later milestone)" — `openspec/changes/causal-headrank-poc/design.md:17`
32. "Any baseline comparisons (SparseViT, DepGraph, magnitude, gradient)" — `openspec/changes/causal-headrank-poc/design.md:18`

## Rank stability

33. "Run scoring twice with different random image subsets (100 vs 200 images)." — `openspec/changes/causal-headrank-poc/design.md:81`
34. `repeat_cfg = replace(cfg, seed=cfg.seed + repeat)` — `scripts/run_poc.py:214`
35. `raise RuntimeError("stability subsets are identical; refusing to compute a tautological tau")` — `scripts/run_poc.py:221`
36. `raise RuntimeError("stability subsets do not preserve class composition")` — `scripts/run_poc.py:223`
37. `taus = [kendall_tau(rankings[0], ranking) for ranking in rankings[1:]]` — `scripts/run_poc.py:236`
38. `passed = report["mean_tau"] >= 0.7 and report["min_tau"] >= 0.6` — `scripts/run_poc.py:250`
39. `"Q3": null` — `experiments/pretrained_smoke_v2/results.json:66`
40. `"verdict": "GO"` — `experiments/pretrained_smoke_v2/results.json:70`
41. `"record_count": 12` — `experiments/stability_smoke_v2/q3_seed_42_scores.meta.json:3`
42. `"record_count": 12` — `experiments/stability_smoke_v2/q3_seed_43_scores.meta.json:3`
43. `0.0021357345394790173` — `experiments/causal_headrank_poc/q3_seed_a_scores.csv:2`
44. `0.0021357345394790173` — `experiments/causal_headrank_poc/q3_seed_b_scores.csv:2`
45. `0.10090450942516327` — `experiments/causal_headrank_poc/q3_seed_a_scores.csv:5`
46. `0.10090450942516327` — `experiments/causal_headrank_poc/q3_seed_b_scores.csv:5`

## Repeatability artifacts

47. "Every experiment output directory contains `environment.json` with python/torch/timm/nnsight/CUDA/GPU versions." — `openspec/changes/causal-headrank-poc/design.md:93`
48. `"gpu_memory_gb": 6.44` — `experiments/pretrained_smoke_v2/environment.json:10`
49. `"python_version": "3.13.7"` — `experiments/pretrained_smoke_v2/environment.json:2`
50. `"nnsight_version": "0.7.0"` — `experiments/pretrained_smoke_v2/environment.json:7`
51. `"fingerprint_config = {` — `src/keystone/scoring.py:102`
52. `"batch_size": cfg.batch_size,` — `src/keystone/scoring.py:103`
53. `"metric": cfg.metric,` — `src/keystone/scoring.py:105`
54. `"model_name": cfg.model_name,` — `src/keystone/scoring.py:106`
55. `"pretrained": cfg.pretrained,` — `src/keystone/scoring.py:107`
56. `sample_composition_seed: int = 0` — `src/keystone/config.py:19`
57. `seed: int = 42` — `src/keystone/config.py:7`
58. `print(f"  [scoring] ignoring legacy checkpoint without metadata: {checkpoint_path}")` — `src/keystone/scoring.py:135`
59. `PermissionError: [WinError 32]` — `experiments/smoke_v2/failure_report.md:7`
60. "Full run with pretrained DINOv3, CIFAR-100, 50 images, 144 heads: Q1-Q5 all PASS. Verdict: GO." — `openspec/changes/causal-headrank-poc/tasks.md:33`

## Related pruning footprint

61. "Pipeline: Scoring (activation patching on JSTS) → Pruning (magnitude pruning of non-circuit components)" — `papers/CC-Prune_GitHub_README.md:18`
62. "No comparison against structured pruning baselines (only Wanda for unstructured)" — `papers/CC-Prune_GitHub_README.md:24`
63. "No comparison between causal importance and magnitude/gradient correlation" — `papers/CC-Prune_GitHub_README.md:29`
64. "Does activation-patching-derived causal importance provide a complementary pruning signal" — `docs/brainstorms/keystone-neurons-requirements.md:22`
65. "Score all attention heads by causal importance via activation patching. Prune lowest-scoring heads at multiple ratios (25%, 50%, 75%, 90%)." — `docs/brainstorms/keystone-neurons-requirements.md:102`
66. "At ≥50% sparsity, causal-guided pruning preserves structured output competitively with magnitude-guided pruning across 3 seeds." — `docs/brainstorms/keystone-neurons-requirements.md:134`
