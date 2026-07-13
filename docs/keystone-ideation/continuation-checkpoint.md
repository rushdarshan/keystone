---
date: 2026-07-13
status: partial-checkpoint
source-artifact: ../ideation/2026-07-12-research-project-ideation.md
run-id: da91d24b
---

# Keystone Neurons Ideation Continuation

## Scope

This continuation tested and refined the Keystone Neurons direction using the proposal, OpenSpec PoC, current implementation artifacts, CAP, Vi-CD, CC-Prune, and current external prior art.

The original ideation artifact remains unchanged because the divergent-generation and adversarial-ranking workflow was stopped before completion.

## Grounded Corrections

1. **The broad novelty claim no longer holds.** CAP already applies interventional head importance to LLM pruning, CC-Prune protects activation-patching-derived circuits during NLP pruning, and Vi-CD performs faithful circuit discovery in ViTs. The defensible novelty boundary is narrower: whether faithful ViT intervention scores predict safe, physically realized structured pruning and preserve representations across tasks.
2. **The PoC validates hooking, not pruning.** Current code scores and patches individual heads. It does not physically remove heads, rebuild QKV/output projections, evaluate pruned checkpoints, or establish measured acceleration.
3. **The stability claim is not yet supported.** Stored Q3 evidence is null in one result file, and the two 144-head seed CSVs contain identical scores rather than an independently demonstrated repeatability result.
4. **The hardware assumption is overstated.** Recorded hardware exposes 6.44 GB VRAM, below the proposal's 8-12 GB assumption. Any direction must fit and be measured on the actual RTX 4050.
5. **Importance is currently intervention-specific.** Cross-class activation replacement plus target-logit difference may measure corruption sensitivity rather than model-intrinsic pruning importance.
6. **Single-head scores ignore group effects.** Redundant or synergistic heads can make individually safe removals unsafe when combined.

## Strongest Current Direction

### Keystone Pruning Validity Study

**Research question:** Do intervention-derived attention-head scores predict safe, physically realized ViT head removal across task shift?

This reframing makes the project's primary contribution a falsifiable empirical protocol rather than a newness claim about activation patching.

The strongest combined study has four parts:

- **Surgery-calibrated score validity:** compare patching, magnitude, gradient, and random rankings by how well they predict held-out loss after physical head removal.
- **Intervention invariance:** test whether rankings survive changes in corruption construction and output metric instead of trusting one cross-class logit score.
- **Conditional keystone sets:** inspect pair or small-group interactions near pruning cutoffs and ranking-disagreement regions.
- **Hardware and transfer validation:** report rebuilt-model latency, throughput, VRAM, classification utility, anomaly detection, and representation geometry.

This direction is negative-result-friendly. If causal scores do not beat conventional scores, the study can still establish when activation-patching ranks fail to transfer to structured pruning.

## Unranked Shortlist

These candidates survived the three completed generation frames but have not passed final adversarial critique:

1. **Surgery-Calibrated Causal Ranking** - validate scores against actual post-surgery damage.
2. **Intervention-Invariant CausalHeadRank** - require agreement across corruption and metric choices.
3. **Conditional Keystone Sets** - replace independent importance with targeted pair/group effects.
4. **Redundancy-Triggered Re-Ranking** - re-score only the uncertainty band after each safe pruning tranche.
5. **Hardware-Realizable Causal Pruning** - constrain selections to executable projection shapes and measured latency.
6. **The Patching-to-Surgery Gap** - directly compare activation replacement, zero masking, and physical deletion.
7. **Task-Conditional Keystone Rankings** - distinguish classification-specific, anomaly-specific, and shared representation heads.

## Mandatory Baselines and Threats

- CAP: https://arxiv.org/abs/2606.19350
- Vi-CD: https://arxiv.org/abs/2604.14477
- CAAP: https://arxiv.org/abs/2603.13652
- CC-Prune: https://github.com/ikari12/Causal_Pruning
- SnapViT, LPViT, Isomorphic Pruning
- Magnitude, gradient/Taylor, random, and equal-per-layer head selection

## Integrity Notes

- Some local files claim 2026-07-15 timestamps even though this run's current date is 2026-07-13. Those timestamps were not treated as evidence.
- CAP and Vi-CD were text-extracted with page-level evidence dossiers.
- First pages rendered successfully with PyMuPDF, but visual inspection was blocked by the local Windows sandbox wrapper.
- Three divergent frames completed. Two were interrupted. No final deduplication, adversarial filtering, basis verification, or final ranking was completed.
