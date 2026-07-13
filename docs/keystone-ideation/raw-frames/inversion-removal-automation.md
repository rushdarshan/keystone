# Raw Frame: Inversion, Removal, or Automation

Agent: Lovelace
Status: completed before the ideation run was stopped

### Intervention-Invariant CausalHeadRank
- **summary:** Replace the assumption that one cross-class replacement score is causal importance with an intervention-invariance criterion: retain only heads whose ranks persist across cross-class swaps, mean activation replacement, and a visually localized corruption. The contribution is a negative-result-friendly test of whether pruning-relevant importance survives changes in the counterfactual, rather than merely whether one hook produces a nonzero logit change.
- **axis:** Causal-score validity
- **basis:** **direct:** “Scores depend on the choice of patching distribution (replacement with mean vs. Gaussian vs. swapped example).” ([requirements](C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md):172)
- **why_it_matters:** It turns the weakest assumption in the PoC into the main scientific claim and distinguishes valid causal signals from corruption artifacts.
- **meeting_test:** A consensus rank predicts post-surgery retention better than every individual intervention rank, or the study establishes that no intervention-stable head ranking exists.

### Conditional Keystone Sets
- **summary:** Invert independent head ranking into conditional importance: after identifying candidate low-score heads, measure whether their effect changes when paired with a potentially redundant or complementary head. Use the resulting synergy and redundancy map to prune sets, not individually ranked heads, and report whether single-head CausalHeadRank systematically protects redundant heads or misses jointly essential pairs.
- **axis:** Interaction-aware importance
- **basis:** **direct:** “Standard ablation can't disentangle coupled components — removing one changes the function of others.” ([ideation](C:/Users/rushd/Downloads/prj-res/docs/ideation/2026-07-12-research-project-ideation.md):69)
- **why_it_matters:** This directly addresses interaction bias instead of treating a marginal score as a component’s intrinsic value.
- **meeting_test:** Conditional set selection preserves output quality at a fixed structural budget better than independent causal, magnitude, gradient, and random selections.

### Compiled-Shape Causal Pruning
- **summary:** Remove the assumption that a masked head equals compression. Restrict CausalHeadRank decisions to head sets that can be physically deleted from QKV and output projections while producing deployable attention shapes, then evaluate the accuracy-latency-VRAM frontier on the RTX 4050 rather than FLOPs alone.
- **axis:** Structured pruning and real hardware effects
- **basis:** **direct:** “The PoC only implements activation patching” ([structured-pruning dossier](C:/Users/rushd/Downloads/prj-res/tmp/compound-engineering/ce-ideate/da91d24b/evidence-structured-pruning-hardware.md):35) and “Inference latency: unpruned vs. pruned at each ratio” ([requirements](C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md):185).
- **why_it_matters:** It makes the contribution about usable structured compression, not a simulated ablation whose theoretical sparsity may yield no hardware gain.
- **meeting_test:** At least one structurally rebuilt causal model lies on the measured latency-quality Pareto frontier and improves end-to-end latency over an equally accurate baseline.

### Shift-Preserving Causal Compression
- **summary:** Reframe downstream anomaly detection as a representation stress test rather than a tertiary demonstration. Partition heads into classification-private, anomaly-private, and cross-task-preserving groups using frozen-feature degradation under classification and distribution-shift/anomaly objectives; prune only heads that are dispensable across the chosen representation contract.
- **axis:** Cross-task representation preservation
- **basis:** **direct:** “AUROC measures detection separability but may not capture fine-grained representation quality. Metrics like effective rank or intrinsic dimension may provide complementary signal.” ([requirements](C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md):174)
- **why_it_matters:** A head ranking that preserves CIFAR logits but destroys anomaly-relevant geometry is not a transferable compression signal.
- **meeting_test:** The selected compressed model preserves both probe performance and anomaly/shift representation metrics better than classification-only causal and magnitude rankings at the same latency.

### Prunability-Calibrated Causal Scores
- **summary:** Automate the costly choice of score formula by treating a causal score as useful only when it predicts the effect of physical removal. Compare logit difference, KL divergence, and loss change on a small calibration set, then select the metric by its ability to forecast held-out structural-pruning damage, not by rank stability alone.
- **axis:** Causal-score validity
- **basis:** **direct:** “Different causal scoring metrics (logit diff, KL div, loss change) | Robustness of importance signal | Scoring formula” ([requirements](C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md):160).
- **why_it_matters:** Stable rankings can still be stably wrong for compression; this defines validity against the actual decision the score is meant to make.
- **meeting_test:** The selected score has significantly higher held-out association with structural-removal damage than the current absolute ground-truth-logit score.

### Redundancy-Triggered Re-Ranking
- **summary:** Remove the one-shot ranking assumption. Begin with a causal rank, structurally remove a small safe tranche, re-score only the uncertainty band around the next pruning boundary, and test whether adaptive re-ranking avoids the abrupt failures caused by redundancy being exhausted during pruning.
- **axis:** Interaction-aware importance
- **basis:** **direct:** “the per-head score is the mean absolute logit difference across all N images” ([interaction dossier](C:/Users/rushd/Downloads/prj-res/tmp/compound-engineering/ce-ideate/da91d24b/evidence-interaction-aware-importance.md):21) and “Prune lowest-scoring heads at multiple ratios (25%, 50%, 75%, 90%).” ([requirements](C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md):102).
- **why_it_matters:** It tests whether importance is context-dependent while containing compute through targeted rescoring rather than exhaustive combinatorial attribution.
- **meeting_test:** Adaptive re-ranking delays the first statistically significant quality collapse relative to a one-shot causal ranking at the same cumulative head-removal budget.

### Causal Budget Allocation by Layer
- **summary:** Invert global head removal into a layer-budget allocation problem: use causal scores to decide how much attention capacity each layer must retain, then compare global ranking, equal-per-layer pruning, and learned causal retention quotas under the same compiled model size. The key result is whether causal attribution identifies where structural width can actually be removed, rather than merely which individual heads look unimportant.
- **axis:** Structured pruning and real hardware effects
- **basis:** **direct:** CAP reports importance concentrated in some layers while other layers show redundancy ([CAP dossier](C:/Users/rushd/Downloads/prj-res/tmp/compound-engineering/ce-ideate/da91d24b/evidence-user-research-cap.md):42), and the project requires analysis of “distribution of keystone heads across layers” ([requirements](C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md):123).
- **why_it_matters:** Layer-compatible head counts make physical projection surgery and real latency evaluation more defensible than arbitrary global masking.
- **meeting_test:** Causal layer quotas outperform global causal ranking and equal-per-layer removal on the measured quality-latency frontier.
