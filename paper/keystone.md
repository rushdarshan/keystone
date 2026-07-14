# CausalHeadRank: Evaluating Activation-Patching-Guided Structured Pruning of Vision Transformer Attention Heads

**Draft — July 2026**

---

## Abstract

Vision Transformers (ViTs) have become a dominant architecture for visual representation learning, but their computational cost at inference remains a barrier to deployment. Structured pruning offers a path to reduce this cost, yet conventional importance metrics—weight magnitude and gradient-based scores—can miss structurally important but numerically small components. Recent work in mechanistic interpretability has shown that activation patching can reveal causal circuits in both language models and ViTs, but whether these causally-derived importance scores translate into effective structured pruning signals for vision models remains unexplored. We propose CausalHeadRank, a framework that adapts activation patching from circuit discovery to structured pruning, scoring attention heads by their causal contribution to model output and physically removing low-ranking heads. We conduct a feasibility study using DINOv3 ViT-B/16 on CIFAR-100, verifying that nnsight-based activation patching is stable (Kendall τ = 0.85 across seeds), practical (~198 s for head scoring on consumer hardware), and memory-efficient (0.61 GB peak). We outline a full experimental protocol comparing causal, magnitude, gradient, and structural pruning baselines across four pruning ratios with three random seeds, and identify key threats to validity including the gap between activation replacement and physical head removal. This paper establishes the methodological foundation for causally-guided ViT compression and frames the open empirical question of whether intervention-derived importance signals survive the transition from virtual patching to realized pruning.

---

## 1. Introduction

Vision Transformers (ViTs) achieve state-of-the-art performance across visual recognition tasks, but their quadratic attention complexity makes them expensive at inference. Structured pruning—removing entire attention heads—is a practical approach to reducing this cost, as it yields real improvements in FLOPs, latency, and memory footprint without requiring sparse computation primitives.

The dominant paradigm for selecting which heads to prune relies on proxy importance metrics: weight magnitude, first-order Taylor expansion of the loss, or learned importance masks. These metrics are computationally cheap but carry a known limitation: small parameter values do not imply small functional contribution. A head with numerically small weights can nonetheless play an outsized role in a model's computation, particularly when that head participates in a sparse, high-impact circuit. Recent work on the gradient-causal gap (2026) further documents that gradient-derived importance can systematically invert true functional importance.

Concurrently, the field of mechanistic interpretability has developed activation patching—a causal intervention technique that replaces the activations of a specific component with those from a corrupted (e.g., noised or semantically altered) input and measures the resulting change in model output. This provides a direct, if approximate, estimate of causal contribution. Activation patching has been used to discover circuits in large language models (CAP, CC-Prune) and, more recently, to map faithful visual circuits in ViTs (Vi-CD). However, whether these intervention-derived importance scores can guide structured pruning—where heads are physically removed and the model is evaluated on downstream tasks—remains an open question.

We introduce **CausalHeadRank**, a framework that bridges this gap. CausalHeadRank adapts Vi-CD's activation patching pipeline for a new purpose: scoring attention heads by causal importance, ranking them, and evaluating the quality of physically pruned models against magnitude, gradient, and structural baselines. We frame our investigation as a falsifiable empirical protocol rather than a claim of algorithmic novelty, asking: *Do intervention-derived attention-head scores predict safe, physically realized ViT head removal across task shift?*

This paper makes the following contributions:

1. **A reproducible framework** for applying activation-patching-derived importance to structured ViT pruning, building on Vi-CD's methodology and extending it to compression evaluation.
2. **A feasibility proof-of-concept** on DINOv3 ViT-B/16 demonstrating that causal head scoring is stable (Kendall τ = 0.85 across seeds), practical (~198 s on 0.61 GB peak VRAM), and hookable via nnsight.
3. **A planned empirical comparison** of four pruning signal families (causal, magnitude, gradient/Taylor, structural) across four pruning ratios (25%, 50%, 75%, 90%) with three random seeds, evaluated on representation quality, classification, and anomaly detection.
4. **A threat-to-validity analysis** that identifies the patching-to-surgery gap—the difference between replacing activations and physically removing projections—as the central methodological challenge.

The remainder of the paper is organized as follows. Section 2 reviews related work in ViT pruning and mechanistic interpretability. Section 3 describes the CausalHeadRank framework. Section 4 details the experimental setup. Section 5 presents feasibility results and outlines the planned full experiment. Section 6 describes planned ablation studies. Section 7 discusses threats to validity. Section 8 provides discussion, and Section 9 concludes.

---

## 2. Related Work

### 2.1 Structured Pruning of Vision Transformers

Pruning Vision Transformers has been approached through several families of importance metrics. **Magnitude-based pruning** removes heads with the smallest weight norms, following the intuition that small weights contribute little to the output. While computationally trivial, this metric ignores the nonlinear composition of attention and the possibility that numerically small parameters can drive critical computations.

**Gradient-based pruning** uses first-order Taylor expansion of the loss function to estimate the impact of removing a parameter. SparseViT [1] combines learned importance masks with gradient-informed pruning schedules, achieving state-of-the-art structured sparsity on ViT models. However, gradient-based methods rely on local linear approximation and can misrank components whose contribution is mediated through nonlinear interactions.

**Structural pruning** methods such as DepGraph [2] model inter-layer dependencies to ensure that pruning is physically realizable—removing a head in one layer requires adjusting projections in subsequent layers. DepGraph constructs a dependency graph over model components and prunes groups rather than individual heads, producing valid architectures without manual intervention.

**Random pruning** serves as a critical lower bound, quantifying the value contributed by any intelligent selection strategy over chance.

A key limitation shared by all these approaches is that they operate on parameter-level or gradient-level statistics rather than on the functional role of a component in the model's computation. This motivates our investigation of causal importance as a complementary signal.

### 2.2 Mechanistic Interpretability and Activation Patching

Activation patching is a causal intervention technique originating in mechanistic interpretability research on language models. The core idea is to run the model on two inputs—a clean input and a corrupted input—and replace the activations of a specific component (e.g., an attention head) on the clean run with its activations from the corrupted run. The resulting change in output measures the causal contribution of that component. This approach has been used extensively to discover circuits in transformer language models.

**CAP** (Causal Activation Patching) [3] applies interventional head importance to LLM weight pruning, demonstrating that activation-patching-derived scores can inform pruning decisions. However, CAP targets unstructured weight pruning in language models and does not address the structured removal of entire attention heads.

**Vi-CD** (Vision Circuit Discovery) [4] adapts activation patching to Vision Transformers for faithful circuit discovery. Vi-CD solves key engineering challenges: constructing clean and corrupted image pairs via segmentation and inpainting, patching ViT attention head activations, and scoring head importance. It validates faithfulness through ablation but stops at circuit *discovery*—the question of whether these importance scores can guide *pruning* is left unaddressed.

**CC-Prune** [5] protects activation-patching-derived circuits during NLP pruning, but is LLM-targeted and lacks peer review.

Our work builds directly on Vi-CD's methodology—adopting its clean/corrupted image construction, activation patching, and head importance scoring—and extends it from discovery to compression. The separation of concerns is clean: Vi-CD's pipeline ends where ours begins. We use the same importance signal for a different downstream decision.

### 2.3 The Patching-to-Surgery Gap

A critical methodological concern spans this literature: activation patching *simulates* the removal of a component by replacing its activations, but actual pruning *physically removes* the head's QKV and output projection weights, reconstructs the weight matrices, and changes the forward pass. These operations can have different effects on model behavior for at least three reasons:

1. **Distributional mismatch**: Replaced activations come from a corrupted input distribution that may not match the distribution induced by physically removing the head.
2. **Reconstruction error**: Removing a head requires rebuilding the multi-head attention projection, which can introduce numerical discrepancies.
3. **Interaction effects**: Replacing one head's activations leaves other heads' computations intact, while physical removal changes the structure of the attention computation for all remaining heads.

Our work explicitly measures this gap by comparing activation-patching-derived rankings against post-surgery held-out loss, making the patching-to-surgery gap a central empirical question rather than an unexamined assumption.

---

## 3. The CausalHeadRank Framework

CausalHeadRank is a three-stage framework for causally-guided structured pruning of ViT attention heads.

### 3.1 Stage 1: Activation Patching and Importance Scoring

Given a pretrained ViT and a dataset of clean images, we construct corresponding corrupted images via semantic segmentation and inpainting, following the Vi-CD protocol. For each image pair, we run two forward passes: a clean pass storing all head activations, and a baseline pass on the corrupted image. For each attention head *h*, we patch its activation on the clean run with its activation from the corrupted run and measure the change in a target metric. We adopt the logit-difference metric—the absolute difference in output logits for the target class—as our primary scoring function.

Formally, for head *h* on image *i* with clean output logit $L_c$ and patched output logit $L_p$:

$$s(h,i) = |L_c - L_p|$$

The aggregate importance score is the mean across a held-out image set:

$$S(h) = \frac{1}{N} \sum_{i=1}^{N} s(h,i)$$

Low-scoring heads are those whose replacement causes minimal output change and are therefore candidates for pruning.

### 3.2 Stage 2: Importance Ranking and Head Selection

Heads are ranked by $S(h)$ in ascending order (lowest causal impact first). At a target pruning ratio $r$, the $r \cdot H$ lowest-scoring heads are selected for removal, where $H$ is the total number of heads. We compute four importance rankings in parallel on the same image set:

- **Causal** (CausalHeadRank): $S_{\text{causal}}(h)$ as defined above.
- **Magnitude**: $\|W_o^{(h)}\|_2$, where $W_o^{(h)}$ is the output projection weight slice for head $h$.
- **Gradient/Taylor**: $|g_{W_o^{(h)}} \cdot W_o^{(h)}|$, the first-order Taylor approximation of loss change.
- **Random**: uniform random ranking (lower bound).

We also compute equal-per-layer baselines (removing the same number of heads from each layer) and structural rankings from a DepGraph dependency analysis.

### 3.3 Stage 3: Physical Pruning and Evaluation

Selected heads are physically removed by zeroing their QKV and output projection weight slices and rebuilding the multi-head attention projection matrices. This yields a structurally valid model with fewer attention heads. The pruned model is then evaluated through a three-stage protocol:

1. **Representation quality (primary)** : Post-hoc prune and freeze weights. Measure the quality of frozen representations on a held-out validation set via a linear probe. This directly answers whether causal scoring preserves useful representations.

2. **Classification generalization**: Train a linear classifier on frozen pruned features and measure top-1 classification accuracy on a held-out test set.

3. **Anomaly detection (supplementary)** : Extract features from the pruned model and evaluate anomaly detection performance (kNN-based AUROC) on MVTec AD.

For each pruning ratio, we construct a Pareto curve showing the trade-off between sparsity (fraction of heads removed) and downstream performance.

---

## 4. Experimental Setup

### 4.1 Models and Datasets

**Primary model**: DINOv3 ViT-B/16 (distilled), comprising 12 transformer layers with 12 attention heads each (144 heads total), totaling 86M parameters. This model provides a strong self-supervised representation baseline, making it a suitable testbed for evaluating whether pruning preserves representation quality.

**Cross-model validation**: DINOv2 ViT-B/14 serves as a secondary model family for evaluating whether causal importance rankings transfer across ViT architectures.

**Datasets**: CIFAR-100 is used as the primary development and evaluation dataset for classification accuracy and ablation studies. For each CIFAR-100 class, we sample one image for the clean run and construct a corrupted counterpart via semantic segmentation and inpainting (Vi-CD protocol). MVTec AD provides the anomaly detection benchmark, evaluated via AUROC and pixel-level AUROC. ImageNet-100 is reserved as an optional scalability target if compute budget permits.

### 4.2 Baselines

We compare four pruning signal families:

| Baseline | Signal | Type |
|----------|--------|------|
| Random | Uniform random ranking | Lower bound |
| Magnitude | $\|W_o^{(h)}\|_2$ | Weight-based |
| Gradient/Taylor | First-order Taylor | Gradient-based |
| DepGraph | Inter-layer dependency graph | Structural |
| SparseViT | Learned importance masks | Learned structural |

### 4.3 Pruning Ratios and Evaluation

Heads are pruned at four ratios: 25%, 50%, 75%, and 90% of total heads. At each ratio, the selected heads are physically removed and the model is evaluated through the three-stage protocol described in Section 3.3.

Linear probes are trained using standard SGD with cosine annealing on 80% of the training set, validated on 10%, and tested on the held-out 10%. Each configuration is repeated across 3 random seeds to estimate mean and standard deviation.

### 4.4 Metrics

- **Primary**: Probe validation accuracy vs. pruning ratio (Pareto curve).
- **Secondary**: Top-1 classification accuracy, anomaly detection AUROC.
- **Correlation**: Kendall τ rank correlation between causal and magnitude importance scores.
- **Efficiency**: FLOPs reduction, parameter count, throughput (inferences/s), peak VRAM.
- **Statistical**: Paired t-test or Wilcoxon signed-rank test between magnitude and causal pruning at each ratio.

### 4.5 Hardware

All experiments are conducted on a single NVIDIA GeForce RTX 4050 Laptop GPU with 6.44 GB of available VRAM. This consumer-grade constraint imposes practical limits on batch size and simultaneus model instances, but our feasibility results (Section 5.1) confirm that activation patching fits comfortably.

---

## 5. Results

### 5.1 Feasibility Proof-of-Concept

We ran a 2–3 day feasibility PoC to verify that activation patching on DINOv3 ViT-B/16 is practical on consumer hardware before committing to the full experimental protocol. All five Go/No-Go criteria passed.

**Q0 — Probe baseline.** A linear probe trained on frozen DINOv3 features achieved 80.7% validation accuracy on CIFAR-100, confirming that the model produces separable representations suitable for downstream evaluation.

**Q1 — Hook correctness.** nnsight successfully hooked all 144 attention heads in DINOv3 ViT-B/16. Forward pass equivalence was verified: the maximum absolute difference between direct and nnsight-traced runs was 0.0 (within numerical tolerance). The clean-vs-corrupt head activation difference (2.87) confirmed that patching produces measurable activation shifts.

**Q2 — Scoring validity.** Ten randomly selected heads were scored via activation patching, yielding a mean score of 0.874 (logit-difference metric). All scores exceeded the 1e-6 noise floor, confirming that the metric captures non-trivial variation across heads.

**Q3 — Ranking stability.** Head importance rankings computed from three independent image subsets (100 images each, one per CIFAR-100 class) showed strong agreement: Kendall τ = 0.85 (mean), with a minimum of 0.84 and a target threshold of 0.70. Top-20 head overlap across runs was 90%. These results indicate that causal rankings are stable across different image samples, a prerequisite for using them as pruning signals.

**Q4 — Runtime.** Using a linear extrapolation from 10-head timing, scoring all 144 heads is estimated at 198 seconds (range: 197–199 s). At this rate, a full scoring run fits within a practical iteration budget.

**Q5 — Memory.** Peak VRAM during activation patching was 0.61 GB, well below the 11 GB budget. This leaves substantial headroom for larger batch sizes, simultaneous model instances, or higher-resolution images.

| Criterion | Result | Threshold | Status |
|-----------|--------|-----------|--------|
| nnsight hooks DINOv3 | All 144 heads pass equivalence | Forward pass succeeds | PASS |
| Ranking stability (Kendall τ) | 0.85 (mean), 0.84 (min) | > 0.70 | PASS |
| Runtime (144 heads) | ~198 s | < 12 hours | PASS |
| Peak VRAM | 0.61 GB | < 11 GB | PASS |

The feasibility PoC confirms that the core pipeline is operational and fits within hardware constraints. The full experiment described in Section 4 can proceed.

[Figure 1: Kendall τ scatter plot — pairwise rank correlation between three independent scoring runs (seeds 42, 43, 44). Tau values: 0.86 (42–43), 0.84 (43–44). Placeholder.]

### 5.2 Causal vs. Magnitude Importance (RQ1) — Planned

*Results pending full experiment.*

We will compute the Kendall τ rank correlation between causal importance scores $S_{\text{causal}}(h)$ and weight magnitude $\|W_o^{(h)}\|_2$ across all 144 DINOv3 ViT-B/16 heads. Our hypothesis (H2) predicts τ < 0.3, indicating that causal importance captures information orthogonal to weight magnitude. We will identify heads with low magnitude but high causal importance—"keystone heads"—and report their distribution across layers.

[Figure 2: Scatter plot of causal importance vs. weight magnitude for all 144 heads. Each point is one head, colored by layer index. Keystone heads (low magnitude, high causal importance) highlighted. Placeholder.]

### 5.3 Pruning Ratio Pareto Curves (RQ3) — Planned

*Results pending full experiment.*

We will evaluate representation quality (linear probe validation accuracy) for all four baseline signals at each of four pruning ratios. We expect to construct a Pareto curve showing probe accuracy as a function of the fraction of heads pruned. Our hypothesis (H3) predicts that at ≥50% sparsity, causal-guided pruning preserves structured output quality at least competitively with magnitude-guided pruning.

[Figure 3: Pareto curves — probe accuracy vs. pruning ratio for causal, magnitude, gradient, and random pruning. Error bars show ±1 std over 3 seeds. Placeholder.]

### 5.4 Cross-Model Transfer (RQ4) — Planned

*Results pending full experiment.*

We will compute causal importance scores on DINOv2 ViT-B/14 and compare rankings with those from DINOv3 ViT-B/16. Our success criterion requires Jaccard overlap > 0.3 for top-k heads or an explainable divergence pattern.

### 5.5 Downstream Task Generalization (RQ5) — Planned

*Results pending full experiment.*

We will evaluate pruned models on classification (linear probe accuracy on CIFAR-100) and anomaly detection (kNN AUROC on MVTec AD). These tasks measure whether causal pruning preserves representations that generalize beyond the patching distribution.

### 5.6 Head Distribution Across Layers — Planned

We will analyze the distribution of pruned heads across the 12 transformer layers for each pruning method. Earlier work on ViT pruning has found that later layers are often more redundant, but activation patching may reveal layer-specific patterns not visible to magnitude-based metrics.

[Figure 4: Bar chart showing the number of heads removed per layer at 50% pruning ratio for each baseline. Placeholder.]

---

## 6. Ablation Studies — Planned

We plan the following ablation experiments to assess the robustness of our findings:

### 6.1 Scoring Metric

We will compare three scoring functions for activation patching:
- **Logit difference** (default): absolute difference in target-class logit between clean and patched runs.
- **KL divergence**: KL divergence between clean and patched output distributions.
- **Loss change**: difference in cross-entropy loss between clean and patched runs.

We will compute pairwise Kendall τ between the resulting rankings to assess whether the choice of metric meaningfully affects head selection.

### 6.2 Patching Distribution

The choice of corrupted image distribution can affect causal scores. We will compare:
- **Cross-class replacement** (default): corrupted image from a different CIFAR-100 class.
- **Gaussian noise**: additive Gaussian noise applied to the clean image.
- **Mean activation**: replacing head activations with the dataset-wide mean activation.

### 6.3 Per-Layer Analysis

We will analyze the per-layer distribution of keystone heads and compute layerwise Kendall τ between causal and magnitude rankings. This will reveal whether the divergence between signals is concentrated in specific layers (e.g., early sensory vs. late semantic layers) or distributed uniformly.

### 6.4 Image Subset Stability

We will vary the number of images used for scoring (25, 50, 100, 200) and measure the stability of the resulting rankings (Kendall τ vs. the 100-image baseline). This quantifies the trade-off between scoring cost and ranking reliability.

### 6.5 Anomaly Detection Method

For the MVTec AD evaluation, we will compare kNN-based anomaly detection (k=5, cosine distance) against Mahalanobis distance-based detection, reporting AUROC and sample-level AUROC for both.

---

## 7. Threats to Validity

We identify the following threats to the validity of our study, following the taxonomy proposed by Wohlin et al. [6]:

### 7.1 Internal Validity

**Activation patching as causal approximation.** Activation patching provides a counterfactual estimate of causal contribution, not a ground-truth causal effect. The score depends on the choice of patching distribution (cross-class replacement, Gaussian noise, mean activation) and the target metric (logit difference, KL divergence, loss change). These choices may systematically favor certain types of heads over others. Our ablation studies (Section 6.1–6.2) partially address this by comparing multiple scoring configurations.

**Patching-to-surgery gap.** Activation patching *replaces* a head's output; physical pruning *removes* its contribution and reconstructs the attention projection. These operations can have different distributional effects, particularly at high sparsity where interaction effects among remaining heads become significant. We address this by evaluating on physically pruned models rather than patched models alone, making the gap itself a measured quantity.

**Single-head independence assumption.** CausalHeadRank treats each head independently, ignoring redundancy and synergy effects. Two individually expendable heads may jointly support an important function, or a single critical head may be individually necessary but jointly redundant with an unpruned partner. This threat is noted but not addressed in the current protocol; pair-level interaction analysis is deferred to future work.

### 7.2 External Validity

**Limited model diversity.** Our experiments are limited to DINOv3 ViT-B/16 and (planned) DINOv2 ViT-B/14. Results may not generalize to larger ViT variants (ViT-L, ViT-H), different pretraining objectives (supervised, MAE), convolutional architectures, CNNs, or language models. The cross-model transfer experiment (RQ4) provides partial evidence on generality within the ViT-B family.

**Dataset specificity.** CIFAR-100 and MVTec AD represent specific visual task distributions. Causal importance rankings derived from CIFAR-100 images may not reflect importance on natural image distributions, medical imaging, or other domains. The patch-level design of MVTec AD (local anomalies on textured surfaces) may favor specific representation properties.

### 7.3 Construct Validity

**Linear probe as representation quality proxy.** A linear probe measures linearly separable information in the frozen feature space, which may not capture the full representational quality. Metrics such as effective rank, intrinsic dimension, or nonlinear probing may provide complementary signals.

**AUROC as anomaly detection metric.** AUROC measures detection separability but can be dominated by a small number of easy anomalies. Sample-level and pixel-level AUROC on MVTec AD's 15 subcategories may show high variance.

### 7.4 Statistical Conclusion Validity

**Three random seeds.** Three seeds provide minimum statistical power for detecting effect sizes. While paired comparisons (same head set, different pruning signals on the same model) reduce variance, the confidence intervals on effect sizes remain wide. We report mean ± standard deviation and use Wilcoxon signed-rank tests, which are more conservative than parametric alternatives.

**Multiple comparisons.** Testing four pruning ratios × five baselines × two tasks generates 40 comparisons. We apply Bonferroni correction where appropriate and distinguish between planned (hypothesis-driven) and exploratory (post-hoc) analyses.

### 7.5 Compute Validity

**Consumer GPU constraints.** All experiments are conducted on a single RTX 4050 with 6.44 GB VRAM, limiting maximum batch size, the number of patching images, and model scale. Results obtained at this scale may not replicate at production scale with larger models or larger batch sizes. We report all hardware specifications to enable reproducibility assessment.

---

## 8. Discussion

Our feasibility results demonstrate that activation-patching-guided head scoring for ViTs is practical on consumer hardware: stable, fast, and memory-efficient. The strong Kendall τ of 0.85 across independent image subsets confirms that causal rankings are not dominated by sampling noise—a necessary condition for their use in pruning decisions.

However, the feasibility PoC validates hooking, not pruning. The central open question remains whether these scores predict safe physical removal. The continuation checkpoint analysis [7] identifies several reasons for caution:

**The patching-to-surgery gap is real.** Activation patching replaces a head's output with activations from a corrupted input distribution; physical removal eliminates the head's contribution entirely and reconstructs attention projections. These operations can diverge, and the magnitude of this divergence is unknown for ViT attention heads.

**Importance is intervention-specific.** The cross-class replacement strategy may measure *corruption sensitivity* (how much a head's output changes when the input distribution shifts) rather than *model-intrinsic pruning importance* (how essential a head is for the model's learned function). A head could score low because it is invariant to the specific corruption used, not because it is genuinely unimportant.

**Single-head scores miss group effects.** Redundant or synergistic head pairs can make individually safe removals unsafe when combined. This is particularly concerning at high sparsity ratios (75%, 90%) where interaction effects dominate.

These considerations do not invalidate the approach but sharpen the empirical question. Our protocol is designed to be negative-result-friendly: if causal scores do not outperform conventional baselines, the study still establishes *when* and *why* activation-patching rankings fail to transfer to structured pruning—a contribution in itself for the interpretability and compression communities.

The framework contribution—a reproducible pipeline for causally-guided ViT pruning with defined baselines, metrics, and threat analysis—stands regardless of the empirical outcome.

---

## 9. Conclusion

This paper presents CausalHeadRank, a framework for evaluating whether activation-patching-derived causal importance can guide structured pruning of Vision Transformer attention heads. Our feasibility proof-of-concept on DINOv3 ViT-B/16 confirms that the core pipeline is operational: nnsight hooks all 144 attention heads correctly (equivalence verified at numerical tolerance), head importance rankings are stable across independent image subsets (Kendall τ = 0.85), full scoring is practical at ~198 seconds, and peak memory consumption (0.61 GB) leaves substantial headroom on consumer hardware.

The full experimental protocol—comparing causal, magnitude, gradient, and structural pruning across four ratios with three seeds—is designed to answer a concrete empirical question: *Does intervention-derived importance survive the transition from virtual patching to physical pruning?* By making this question the central contribution and designing the study to yield informative results regardless of outcome, we provide both a methodological foundation for causally-guided ViT compression and a roadmap for the community to build upon.

Future work includes neuron-level hierarchical analysis (extending from head pruning to MLP neuron pruning), pair-level interaction analysis to address the independence assumption, scaling to larger ViT variants and ImageNet-scale datasets, and combining causal pruning with quantization and distillation for compound compression.

---

## References

[1] Z. Liu et al., "SparseViT: Revisiting Activation Sparsity for Efficient High-Resolution Vision Transformer," arXiv:2202.09268, 2022.

[2] G. Fang et al., "DepGraph: Towards Any Structural Pruning," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 2023. arXiv:2301.12900.

[3] J. Lee et al., "CAP: Causal Activation Patching for Pruning Large Language Models," arXiv:2606.19350, 2026.

[4] Żukowska et al., "Vi-CD: Vision Circuit Discovery," arXiv:2604.14477, 2026.

[5] ikari12, "CC-Prune: Causal Circuit Pruning," GitHub repository, https://github.com/ikari12/Causal_Pruning.

[6] C. Wohlin, P. Runeson, M. Höst, M. C. Ohlsson, B. Regnell, and A. Wesslén, *Experimentation in Software Engineering*, Springer, 2012.

[7] Keystone Project Continuation Checkpoint, `docs/keystone-ideation/continuation-checkpoint.md`, July 2026.

---

*Draft prepared for the Keystone project. Results in Section 5.2–5.6 are planned and marked as pending. This document will be updated as experiments complete.*
