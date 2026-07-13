# Interaction-aware importance evidence

Extraction scope: single-head assumptions, redundancy, coupled heads, circuit/group effects, and marginal versus joint removal. CAP and Vi-CD PDFs were not re-extracted.

## Pain points

- “standard ablation cannot reveal due to component coupling.” (`docs/ideation/2026-07-12-research-project-ideation.md:68`)
- “Standard ablation can't disentangle coupled components — removing one changes the function of others.” (`docs/ideation/2026-07-12-research-project-ideation.md:69`)
- “Every paper claims each component is essential, but standard ablation is biased.” (`docs/ideation/2026-07-12-research-project-ideation.md:70`)
- “The full research project requires scoring 144 attention heads by causal importance using activation patching.” (`openspec/changes/causal-headrank-poc/design.md:3`)
- “Structured pruning implementation (deferred to later milestone)” (`openspec/changes/causal-headrank-poc/design.md:17`)
- “Neuron-level hierarchical analysis deferred to Phase B / Future Work.” (`docs/brainstorms/keystone-neurons-requirements.md:103`)
- “Head-level pruning only. Neuron-level analysis deferred.” (`docs/brainstorms/keystone-neurons-requirements.md:216`)

## Single-head assumptions

- “Implement ACDC-style algorithm ported from LLMs to ViTs: patch each head, measure metric drop.” (`docs/brainstorms/keystone-neurons-requirements.md:99`)
- “WHEN a single head is patched with a corrupted activation on 100 CIFAR-100 images” (`openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:7-9`)
- “Replace one clean attention-head output with the paired corrupt output.” (`src/keystone/patching.py:18-25`)
- `head_idx = int(head_spec["head_in_layer"])` (`src/keystone/patching.py:26-27`)
- “the per-head score is the mean absolute logit difference across all N images” (`openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:19-21`)
- “the score for a head is mean |logit_clean - logit_patched| across all images” (`openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:27-29`)
- `patched_outputs = patch_head(model, spec, clean_batch, corrupt_batch, cfg.device)` (`src/keystone/scoring.py:47-53`)
- `"causal_score": float(scores.mean().item()),` (`src/keystone/scoring.py:63-73`)

## Coupled/group effects

- “start from a trivial baseline (single linear layer) and add components one at a time.” (`docs/ideation/2026-07-12-research-project-ideation.md:68`)
- “Measure each addition's marginal benefit across multiple tasks.” (`docs/ideation/2026-07-12-research-project-ideation.md:68`)
- “Reverse ablation reveals true marginal contribution.” (`docs/ideation/2026-07-12-research-project-ideation.md:69`)
- “Structured pruning with dependency awareness (heads + associated MLP neurons).” (`docs/brainstorms/keystone-neurons-requirements.md:103`)
- “Neuron-level hierarchical analysis (head → MLP neurons).” (`docs/brainstorms/keystone-neurons-requirements.md:222`)
- “No hierarchical analysis (head → neuron levels)” (`papers/CC-Prune_GitHub_README.md:28`)

## Marginal versus joint removal

- `for i, name in enumerate(component_names):` (`reverse_ablation/experiment.py:53-60`)
- `print(f"Step {i+1}/{len(component_names)}: Adding component '{name}'")` (`reverse_ablation/experiment.py:53-56`)
- `"marginal_acc_gain": acc_gain,` (`reverse_ablation/analysis/pareto.py:23-38`)
- `acc_gain = row["best_acc"] - prev_acc` (`reverse_ablation/analysis/pareto.py:27-30`)
- `def run_all_independent(self, component_names: List[str], tag: str = "independent"):` (`reverse_ablation/experiment.py:93-99`)
- `print(f"Independent run: '{name}'")` (`reverse_ablation/experiment.py:97-105`)
- `def marginal_benefit_plot(results_df, save_path="experiments/marginal_benefit.png"):` followed by `pass` (`reverse_ablation/analysis/pareto.py:104-106`)

## Contradictions and boundaries

- “Score all attention heads by causal importance ... Prune lowest-scoring heads at multiple ratios (25%, 50%, 75%, 90%).” (`docs/brainstorms/keystone-neurons-requirements.md:101-103`)
- “Non-Goals: - Structured pruning implementation (deferred to later milestone)” (`openspec/changes/causal-headrank-poc/design.md:16-18`)
- “No comparison against structured pruning baselines (only Wanda for unstructured)” (`papers/CC-Prune_GitHub_README.md:21-25`)
- “No comparison between causal importance and magnitude/gradient correlation” (`papers/CC-Prune_GitHub_README.md:26-29`)

## Workarounds and controls

- “Process heads one at a time.” (`openspec/changes/causal-headrank-poc/design.md:74-77`)
- “Explicit `torch.cuda.empty_cache()` after each head bounds memory to the worst single head, not 144× the average head.” (`openspec/changes/causal-headrank-poc/design.md:77`)
- “Before any patching, run all images through the model once and cache the clean logits.” (`openspec/changes/causal-headrank-poc/design.md:103-106`)
- “the clean forward pass is executed only once per image” (`openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:49-53`)
- “Run scoring twice with different random image subsets (100 vs 200 images).” (`openspec/changes/causal-headrank-poc/design.md:81`)

## Surprising patterns in artifacts

- `head_idx 3: causal_score 7.776096820831299; head_idx 5: causal_score 0.0; head_idx 7: causal_score 0.0` (`experiments/stability_smoke_v2/q2_head_scores.csv:5-9`)
- `head_idx 9: causal_score 1.3170095682144165; score_std 1.65790855884552` (`experiments/stability_smoke_v2/q2_head_scores.csv:10-11`)
- `"target_tau": 0.7` and `"taus_vs_baseline": [0.7230769230769232, 0.7230769230769232]` (`experiments/stability_smoke_v2/results.json:368-371`)
- `"top_k_overlap_vs_baseline": [1.0, 1.0]` (`experiments/stability_smoke_v2/results.json:373-376`)
- `"overlap_with_baseline": 0` (`experiments/stability_smoke_v2/results.json:364`)

## TODO/FIXME markers

- “Status: Unexplored” (`docs/ideation/2026-07-12-research-project-ideation.md:74`)
- “Neuron-level analysis deferred.” (`docs/brainstorms/keystone-neurons-requirements.md:216`)
- `def marginal_benefit_plot(...): pass` (`reverse_ablation/analysis/pareto.py:104-106`)

## Leverage points recorded in workspace

- “Importance ranking → structured pruning” (`docs/brainstorms/keystone-neurons-requirements.md:35`)
- “An investigation of the relationship between causal importance and conventional pruning metrics, including correlation structure and divergence patterns.” (`docs/brainstorms/keystone-neurons-requirements.md:62`)
- “Overlap analysis (top-k Jaccard, Kendall τ, Spearman ρ)” (`docs/brainstorms/keystone-neurons-requirements.md:164`)

