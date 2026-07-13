# Raw Frame: Pain and Friction

Agent: Aquinas
Status: completed before the ideation run was stopped

### 1. Surgery-Calibrated Causal Ranking
- **Summary:** Redefine score validity around prediction: a causal ranking is useful only if it predicts the performance loss from *physical* head removal on held-out data. Compare activation-patching, magnitude, and gradient rankings by their ability to order observed post-surgery degradation, rather than treating Kendall stability as validation. This makes a negative result meaningful: stable patching scores may still be invalid pruning proxies.
- **Axis:** Causal-score validity
- **Basis:** `direct:` “Activation patching provides an approximation of causal contribution, not ground-truth causal effect.” — [C:\Users\rushd\Downloads\prj-res\docs\brainstorms\keystone-neurons-requirements.md:172](/C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md#L172)
- **Why it matters:** It changes the central claim from “we can rank heads” to “this intervention predicts the consequence that compression actually cares about.”
- **Meeting test:** Held-out correlation between predicted importance and post-surgery loss exceeds magnitude and gradient at multiple pruning ratios.

### 2. Conditional Keystone Sets
- **Summary:** Replace independent head scores with conditional contribution: ask whether a head remains important after other candidate heads are retained or removed. The output is a compact set of mutually complementary heads, separating uniquely necessary heads from redundant heads that only appear important in isolation. This directly targets interaction bias without attempting infeasible exhaustive subset search over 144 heads.
- **Axis:** Interaction-aware importance
- **Basis:** `direct:` “Standard ablation can't disentangle coupled components — removing one changes the function of others.” — [C:\Users\rushd\Downloads\prj-res\docs\ideation\2026-07-12-research-project-ideation.md:69](/C:/Users/rushd/Downloads/prj-res/docs/ideation/2026-07-12-research-project-ideation.md#L69)
- **Why it matters:** A single-head ranking can preserve redundant heads while pruning a jointly necessary set, which is exactly the failure mode structured pruning cannot absorb.
- **Meeting test:** Conditional sets retain more frozen-model utility than equally sized independent-score selections at the same structural budget.

### 3. Hardware-Realizable Causal Pruning
- **Summary:** Make the pruning decision aware of the architecture that can actually be rebuilt and accelerated: select head-retention counts and layer allocations that produce valid reduced QKV/output dimensions, then evaluate measured latency and memory. The contribution is not a FLOPs estimate but a causal ranking constrained by executable ViT shapes and real RTX 4050 behavior.
- **Axis:** Structured pruning and real hardware effects
- **Basis:** `direct:` “Inference latency: unpruned vs. pruned at each ratio” — [C:\Users\rushd\Downloads\prj-res\docs\brainstorms\keystone-neurons-requirements.md:185](/C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md#L185); `direct:` “The PoC only implements activation patching” — [C:\Users\rushd\Downloads\prj-res\openspec\changes\causal-headrank-poc\design.md:65](/C:/Users/rushd/Downloads/prj-res/openspec/changes/causal-headrank-poc/design.md#L65)
- **Why it matters:** It closes the current masking-versus-compression gap and prevents a paper from claiming efficiency based on non-accelerating activation masks.
- **Meeting test:** At least one physically rebuilt causal-pruned model improves median latency on the RTX 4050 while matching its claimed utility budget.

### 4. Task-Conditional Keystone Rankings
- **Summary:** Test whether heads important for CIFAR target logits are also important for DINO’s downstream representation geometry and anomaly detection. Compare classification-derived rankings with representation-preserving rankings, then use a distribution-shift anomaly benchmark such as MVTec AD 2 when feasible. The contribution is a falsifiable account of when “importance” transfers across uses of a pretrained ViT.
- **Axis:** Cross-task representation preservation
- **Basis:** `direct:` “AUROC measures detection separability but may not capture fine-grained representation quality. Metrics like effective rank or intrinsic dimension may provide complementary signal.” — [C:\Users\rushd\Downloads\prj-res\docs\brainstorms\keystone-neurons-requirements.md:174](/C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md#L174)
- **Why it matters:** The current logit score is aligned to CIFAR classification, while the proposed application is frozen DINO features for anomaly detection.
- **Meeting test:** Classification-derived and representation-derived rankings either agree and preserve both tasks, or their divergence reliably predicts the task-specific failure.

### 5. Corruption-Invariant Causal Importance
- **Summary:** Treat corruption construction as a source of estimator uncertainty, not a fixed implementation detail. A head is a keystone only when its low-importance status persists across semantically distinct but controlled replacement distributions, with uncertainty reported alongside rank. This turns the arbitrary cross-class swap into an empirical robustness question.
- **Axis:** Causal-score validity
- **Basis:** `direct:` “Scores depend on the choice of patching distribution (replacement with mean vs. Gaussian vs. swapped example).” — [C:\Users\rushd\Downloads\prj-res\docs\brainstorms\keystone-neurons-requirements.md:172](/C:/Users/rushd/Downloads/prj-res/docs/brainstorms/keystone-neurons-requirements.md#L172)
- **Why it matters:** A ranking driven by a particular corruption artifact cannot defensibly claim to identify model-intrinsic importance.
- **Meeting test:** Consensus-ranked low-importance heads yield lower variance and no worse post-pruning utility than rankings from cross-class swapping alone.

### 6. Redundancy Gap Maps
- **Summary:** Quantify, per layer, the gap between independent causal importance and group-removal importance. The result is a redundancy map that identifies where head effects substitute for one another and where a nominally low-score group is jointly indispensable. This can explain when causal ranking should beat gradients and when neither independent criterion is trustworthy.
- **Axis:** Interaction-aware importance
- **Basis:** `direct:` The current pipeline computes “the per-head score” as a mean difference after “a single head is patched.” — [C:\Users\rushd\Downloads\prj-res\openspec\changes\causal-headrank-poc\specs\causal-head-scoring\spec.md:7](/C:/Users/rushd/Downloads/prj-res/openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md#L7), [C:\Users\rushd\Downloads\prj-res\openspec\changes\causal-headrank-poc\specs\causal-head-scoring\spec.md:19](/C:/Users/rushd/Downloads/prj-res/openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md#L19)
- **Why it matters:** It makes redundancy a measured explanation of pruning outcomes rather than post-hoc speculation.
- **Meeting test:** Layers with larger redundancy gaps show larger divergence between independent-score pruning predictions and observed group-pruning loss.

### 7. The Patching-to-Surgery Gap
- **Summary:** Directly characterize the mismatch among corrupt-activation replacement, zero masking, and physical head deletion. Report which intervention gives rankings that transfer to rebuilt models, and where the answer changes by layer or pruning ratio. A negative result would sharply constrain claims that activation-patching importance is suitable for structured compression.
- **Axis:** Structured pruning and real hardware effects
- **Basis:** `direct:` The current intervention is “Replace one clean attention-head output with the paired corrupt output.” — [C:\Users\rushd\Downloads\prj-res\src\keystone\patching.py:18](/C:/Users/rushd/Downloads/prj-res/src/keystone/patching.py#L18); meanwhile, “Structured pruning implementation” was explicitly deferred. — [C:\Users\rushd\Downloads\prj-res\openspec\changes\causal-headrank-poc\design.md:17](/C:/Users/rushd/Downloads/prj-res/openspec/changes/causal-headrank-poc/design.md#L17)
- **Why it matters:** Replacement can introduce information from a different image, whereas deletion removes capacity; treating them as equivalent is the project’s largest construct-validity risk.
- **Meeting test:** One intervention’s ranking consistently has the strongest agreement with accuracy, representation, and latency outcomes after physical surgery.
