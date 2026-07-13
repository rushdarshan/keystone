# Leverage and Compounding - Bohr

### 1. Predictive Causal-Score Calibration
- **summary:** Treat a head score as credible only if it predicts the downstream damage caused by its eventual structural removal, rather than merely producing a large patched-logit change. Compare logit-difference, KL, and loss-based scores by their held-out ability to predict accuracy and representation loss across pruning levels. This turns CausalHeadRank from an attribution method into a falsifiable pruning-signal study.
- **axis:** Causal-score validity
- **basis:** direct: "Measure the change in the target class logit between clean and patched forward passes." [openspec/changes/causal-headrank-poc/design.md:40] The PoC explicitly excluded "Any baseline comparisons (SparseViT, DepGraph, magnitude, gradient)" [openspec/changes/causal-headrank-poc/design.md:18], so predictive validity against pruning outcomes is still untested.
- **why_it_matters:** A shared score-validity table makes every later pruning result interpretable: causal scores either predict structural damage better than conventional signals, or they do not. Either result is publishable and directly addresses CAP's non-transferability to ViTs.
- **meeting_test:** Can a held-out score metric predict which head-removal sets cause the least structural-model degradation better than magnitude and gradient rankings?

### 2. Cutoff-Aware Interaction Certificates
- **summary:** Estimate joint removal effects only for heads near each pruning cutoff and for heads whose causal and conventional rankings disagree. Use these targeted group interventions to identify redundant pairs, synergistic pairs, and individually harmless heads that become harmful together. The output is an interaction certificate attached to each pruning decision, not an infeasible all-pairs analysis of 144 heads.
- **axis:** Interaction-aware importance
- **basis:** direct: "Standard ablation can't disentangle coupled components - removing one changes the function of others." [docs/ideation/2026-07-12-research-project-ideation.md:69] Current scoring is explicitly single-head: "WHEN a single head is patched with a corrupted activation on 100 CIFAR-100 images" [openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:7-9].
- **why_it_matters:** It concentrates expensive causal interventions exactly where pruning decisions are unstable, producing a reusable explanation for rank failures and a defensible answer to interaction-bias concerns.
- **meeting_test:** Do targeted pair or small-group effects materially reorder the heads selected at 25%, 50%, and 75% pruning cutoffs?

### 3. Hardware-Realizable Head Surgery Frontier
- **summary:** Define the pruning unit as a physically removable attention-head bundle: its Q/K/V slices and corresponding output-projection inputs, subject to layerwise configurations that execute efficiently on the RTX 4050. Compare masked, structurally rebuilt, and dense models to separate functional sparsity from actual parameter, latency, throughput, and VRAM gains. The contribution is a causal-guided Pareto frontier constrained by real executable architectures, not nominal FLOPs.
- **axis:** Structured pruning and real hardware effects
- **basis:** direct: "The PoC only implements activation patching" [openspec/changes/causal-headrank-poc/design.md:65]. The intended evaluation already specifies "Inference latency: unpruned vs. pruned at each ratio" [docs/brainstorms/keystone-neurons-requirements.md:180-187], while the recorded hardware has only `"gpu_memory_gb": 6.44` [experiments/pretrained_smoke_v2/environment.json:10].
- **why_it_matters:** This prevents claiming compression from activation masking and makes the work comparable to structured ViT pruning baselines, whose practical advantage depends on measured acceleration.
- **meeting_test:** At equal retained-head budgets, does causal selection yield a better measured latency-performance frontier after physical surgery than magnitude, gradient, and random selection?

### 4. Representation-Preservation Transfer Matrix
- **summary:** Evaluate whether a ranking calibrated on CIFAR-100 classification preserves frozen DINO representations under a distinctly different task and shift regime, using anomaly detection plus representation geometry. Report linear-probe accuracy, AUROC, effective rank or intrinsic dimension, and clean-to-shift degradation for the same pruned checkpoints. This tests whether causal importance is task-general representation protection or merely classifier-specific head protection.
- **axis:** Cross-task representation preservation
- **basis:** direct: "AUROC measures detection separability but may not capture fine-grained representation quality." [docs/brainstorms/keystone-neurons-requirements.md:174] The planned research question is already explicit: "How does causal-guided pruning affect downstream classification and anomaly detection performance?" [docs/brainstorms/keystone-neurons-requirements.md:76].
- **why_it_matters:** It establishes a stronger endpoint than CIFAR accuracy and uses the same pruned models to answer several transfer questions. A negative result, where classification-preserving pruning damages anomaly features, is scientifically useful.
- **meeting_test:** Do causal-pruned models preserve anomaly separability and feature geometry better than matched baselines at equal measured latency?

### 5. Intervention-Invariant Causal Ranking
- **summary:** Build a consensus rank only from heads whose importance remains stable across intervention semantics and output objectives: cross-class replacement, mean activation replacement, and a feasible image-corruption control; logit difference, KL, and loss change. Heads with high score variance become an explicit uncertainty set rather than being silently forced into a precise global ordering. Test whether consensus-only protection improves pruning reliability per scored head-hour.
- **axis:** Causal-score validity
- **basis:** direct: the current method uses "Cross-class swapping" [openspec/changes/causal-headrank-poc/design.md:27] and chooses logit difference while acknowledging "KL divergence" and "Cross-entropy loss change" as alternatives [openspec/changes/causal-headrank-poc/design.md:42-45]. The project already identifies "Different causal scoring metrics (logit diff, KL div, loss change)" as a robustness variable [docs/brainstorms/keystone-neurons-requirements.md:160].
- **why_it_matters:** It makes the causal claim robust to a known attribution failure mode: rankings induced by a particular corruption distribution rather than stable functional importance.
- **meeting_test:** Does an intervention-invariant consensus ranking outperform any single intervention/metric ranking in predicting safe structural removal?

### 6. Disagreement-Directed Redundancy Map
- **summary:** Use causal-versus-magnitude/gradient disagreement as the sampling policy for interaction experiments. For each disagreement region, test whether causal-low but magnitude-high heads are redundant capacity, and whether causal-high but magnitude-low heads are hidden dependencies; then determine whether these patterns are layer- or task-specific. This yields an empirical explanation of when causal ranking is useful rather than only reporting correlation coefficients.
- **axis:** Interaction-aware importance
- **basis:** direct: the proposal calls for "An investigation of the relationship between causal importance and conventional pruning metrics, including correlation structure and divergence patterns." [docs/brainstorms/keystone-neurons-requirements.md:62] CC-Prune has "No comparison between causal importance and magnitude/gradient correlation" [papers/CC-Prune_GitHub_README.md:29].
- **why_it_matters:** It converts baseline disagreement into a compact experimental design and provides a mechanism-level result even if causal pruning does not win on every aggregate metric.
- **meeting_test:** Are rank-disagreement heads enriched for redundant or synergistic group behavior relative to matched rank-agreement heads?

### 7. Task-Conditional Keystone Profiles
- **summary:** Mine separate head rankings for classification, normal-image representation preservation, and anomaly or distribution-shift sensitivity, then compare their overlap and the cost of transferring one task's protected set to another. Distinguish universally protected heads from task-specific heads and test whether a small shared core plus task-specific supplements dominates a single global ranking. Keep the study focused on one ViT family if cross-model transfer becomes too expensive.
- **axis:** Cross-task representation preservation
- **basis:** direct: "Vi-CD explicitly leaves ... non-classification tasks ... unexplored." [tmp/compound-engineering/ce-ideate/da91d24b/evidence-cross-task-representation.md:52] CAP has no ViT evidence because "ViTs have patch tokens, class/task-specific visual losses, different attention/head roles" [tmp/compound-engineering/ce-ideate/da91d24b/evidence-user-research-cap.md:51].
- **why_it_matters:** It narrows novelty to a question neither prior line establishes: whether causal head importance is a portable property of a visual representation or an objective-dependent property of a task.
- **meeting_test:** Is there a stable shared keystone set whose protection preserves both classification and anomaly performance better than task-specific or random sets at the same structural budget?
