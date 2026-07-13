---
date: 2026-07-12
topic: research-project-ideation
focus: ML/AI research paper implementation project for college evaluation
mode: elsewhere-software
iteration: 4
run-id: 45327a01
last-updated: 2026-07-15T12:00:00+05:30
---

# Ideation: ML/AI Research Paper Implementation Project Ideas

## Grounding Context

College student seeking a final-year/capstone ML/AI research project that:
- Implements research papers (not CRUD/database/chatbot/simple classifier)
- Built from scratch, no external APIs (no OpenAI, Gemini, Claude)
- Uses local inference with open-source models
- PyTorch/TensorFlow/JAX allowed
- Demonstrates genuine research contribution beyond reproducing one paper
- Unique enough for academic evaluation
- Runs on consumer hardware (single GPU or CPU)
- Preferred domains: novel architectures, efficient inference, vision transformers, audio intelligence, NLP, diffusion, GNNs, model compression, edge AI

### Constraints
- No external APIs. No CRUD/database/chatbot/simple classifier.
- Single student project timeline. Local hardware only.
- Must combine multiple approaches (hybrid > single paper reproduction)

### Pain Points
- Single-paper reproductions are crowded (hundreds of existing GitHub implementations)
- Most student projects are derivative (classify X with Y, chatbot)
- No competitive moat in "implement paper X exactly"
- Need to demonstrate actual research contribution beyond coding
- Local hardware limits scale (no 8xA100 clusters)

### Opportunity Hooks
- **Hybridization**: combining 2-3 papers/approaches is the main leverage point
- **Gap-finding**: research startups, GitHub issues, Reddit complaints for real problems
- **Efficiency + novelty**: model compression, edge AI, efficient inference lower compute barriers
- **Underserved intersections**: GNNs + audio, diffusion + edge, ViT + compression
- **Reproduce → extend → hybridize**: implement a baseline, add novel fusion

### External Research Leads (Phase 1 Web Research)
18 directions identified spanning: DINOv3+anomaly detection, SmolDocling+DocTags, Grokking+interpretability, CALM+TTS, TokenMerging+VideoMamba, SAM+medical, TabularDiffusion, NeuralFields+3D, Code-switching ASR, GNN+drones, SSM↔Transformer distillation, Neuro-symbolic SGG, Split Learning+DP, Mamba+timeseries, No-ref IQA, XAI+3D, Continual Learning+edge, AV separation+lightweight

## Ranked Ideas

### 1. 🏆 Keystone Neurons — Causal Importance-Guided Pruning (Ecology → ML)
**Description:** Identify "keystone" attention heads and neurons in ViTs — components with low magnitude but outsized behavioral impact (like keystone species in ecology). Use causal tracing (activation patching) to find them, then protect them during pruning. Test on DINOv3 features for MVTec anomaly detection. Combines mechanistic interpretability + model compression + self-supervised learning.
**Warrant:** `reasoned:` Ecology's keystone concept reveals a blind spot in pruning research: importance ≠ magnitude. The same structural insight (small parts, system-level effect) maps exactly to sparse network analysis. No existing pruning method uses causal importance as a selection criterion.
**Rationale:** Bridges two hot fields (mechanistic interpretability + model compression) with a novel concept. Clear contribution. DINOv3 + MVTec provides standardized benchmark.
**Downsides:** Causal tracing adds implementation complexity; requires understanding mechanistic interpretability literature.
**Confidence:** 85%
**Complexity:** High (8-10 weeks)
**Status:** Evolved into full proposal → `docs/brainstorms/keystone-neurons-requirements.md`. Proposal confidence: **9.4/10**. Next steps: literature review (CC-Prune, CAP, Vi-CD) → feasibility PoC → implementation.

### 2. Periodization Training — Structured Training Regimens (Sports Science → ML)
**Description:** Replace cosine/step LR schedules with structured training macrocycles: Foundation phase (high LR, diverse augmentation, high temperature → broad feature learning), Specialization phase (low LR, hardest examples, low temperature → refinement), Peaking phase (distilled data, eval-mode tuning → calibration). Compare against cosine, StepLR, and CLR across vision tasks.
**Warrant:** `reasoned:` Sports science formalized that uniform training plateaus the organism adapts. ML has no equivalent framework — schedules are heuristic. Periodization is a principled alternative that unifies LR scheduling and curriculum learning under one theory.
**Rationale:** If periodization consistently outperforms cosine decay (the default), it changes how every model is trained. The insight is general, not task-specific. Clean experimental design.
**Downsides:** Empirically strong but lacks theoretical guarantees; could be seen as "just hyperparameter tuning." 
**Confidence:** 90%
**Complexity:** Medium (4-6 weeks)
**Status:** Unexplored

### 3. Reverse Ablation — Minimum Viable Architecture Discovery
**Description:** Instead of removing components from a complex model (standard ablation), start from a trivial baseline (single linear layer) and add components one at a time. Measure each addition's marginal benefit across multiple tasks. Produce a Pareto frontier of "minimum architecture for X performance" — which standard ablation cannot reveal due to component coupling.
**Warrant:** `reasoned:` Standard ablation can't disentangle coupled components — removing one changes the function of others. Reverse ablation reveals true marginal contribution. Methodologically cleaner.
**Rationale:** Every paper claims each component is essential, but standard ablation is biased. Reverse ablation is methodologically superior and practically useful for edge deployment where you need the smallest model that meets a performance bar.
**Downsides:** Methodological contribution only — no new algorithm, model, or system. Less visually impressive for demo.
**Confidence:** 85%
**Complexity:** Low-Medium (3-5 weeks)
**Status:** Unexplored

### 4. Original Antigenic Sin — Representation Lock-In in Continual Learning (Immunology → ML)
**Description:** Demonstrate that neural networks exhibit the same pathology as the immune system: first-encounter representations "lock in" and resist updating during continual learning. Quantify via CKA similarity across tasks. Propose "booster-shot" mechanism: selective feature unlearning + structured replay that forces representation refresh.
**Warrant:** `external:` Continual learning + edge. `reasoned:` The structural analogy is precise — both systems prioritize first-encounter patterns over adaptation to variants. The immune solution (affinity maturation + periodic re-exposure) translates to concrete algorithmic intervention.
**Rationale:** Continual learning papers treat forgetting as a capacity problem; OAS says it's a *representation lock-in* problem. If true, it reframes the field and suggests interventions current methods miss.
**Downsides:** Requires familiarity with continual learning literature; hard to outperform specialized CL methods.
**Confidence:** 80%
**Complexity:** Medium (6-8 weeks)
**Status:** Unexplored

### 5. Model Portfolio Theory — Risk-Parity Ensembles (Finance → ML)
**Description:** Apply Modern Portfolio Theory to model ensembles. Treat each model in an ensemble as a financial asset. Compute prediction covariance matrix, build the efficient frontier (accuracy vs. prediction variance), and use risk-parity weighting (not uniform/performance-weighted averaging). Show systematic improvement on OOD detection and calibration.
**Warrant:** `external:` MPT is textbook; ML ensemble methods use ad-hoc weighting. Risk-parity is principled and structurally exact.
**Rationale:** The covariance structure of model predictions contains information every averaging method ignores. Novel but immediately useful. Financial framing makes for compelling thesis chapter.
**Downsides:** Requires training 10-15 diverse small models; covariance computation adds complexity.
**Confidence:** 85%
**Complexity:** Medium (5-7 weeks)
**Status:** Unexplored

### 6. Semantic Collapse Index — Measuring Information Loss in Compressed Models
**Description:** Build a metric that quantifies how much semantic information is lost during compression (pruning, quantization, distillation) — not just accuracy drop but whether the model's internal representations collapse into fewer distinguishable clusters. Validate against 3 compression methods × 5 compression rates on ImageNet-100.
**Warrant:** `direct:` "Current compression metrics (accuracy, FID) don't measure semantic collapse" — the evaluation gap is named in user context.
**Rationale:** Two models with identical top-1 accuracy after compression can have wildly different representation quality (one preserves fine-grained features, one collapses to a bag of textures). No existing metric catches this.
**Downsides:** Metric contribution only — no new compression algorithm. Less visually exciting for demo.
**Confidence:** 80%
**Complexity:** Low-Medium (4-6 weeks)
**Status:** Unexplored

### 7. CPU-Only DINOv3 Distillation for Anomaly Detection
**Description:** Systematic study: how far can you push ViT distillation without a GPU? Use LoRA-style adapters, gradient checkpointing, and mixed-precision CPU offload to distill DINOv3 features into a tiny ViT (5M params). Benchmark accuracy vs. training time Pareto frontier for CPU-only settings on MVTec anomaly detection.
**Warrant:** `external:` DINOv2/v3 for anomaly detection is established. `reasoned:` CPU-only distillation Pareto frontier is unmapped — no literature studies this crossover point.
**Rationale:** Democratizes ViT fine-tuning for students/researchers without GPU access. Opens measurable research question: what accuracy-efficiency Pareto frontier can you reach when GPU is not an option?
**Downsides:** Training is slow on CPU (24-48h). Less conceptually novel than cross-domain analogy ideas.
**Confidence:** 75%
**Complexity:** Low (3-4 weeks)
**Status:** Unexplored

---

## Iteration 2 Research: Deep Paper References

### Periodization Training — Key Papers Found (Research Depth: HIGH)

**Baselines to implement & beat:**
- **SGDR** — Loshchilov & Hutter, 2017 (arXiv:1608.03983). Cosine annealing with warm restarts. Primary baseline. Code: github.com/loshchil/SGDR
- **Super-Convergence / OneCycleLR** — Smith & Topin, 2019 (arXiv:1708.07120). Single cycle LR policy. Primary baseline. Code: github.com/lnsmith54/super-convergence
- **Cyclical LR** — Smith, 2017 (arXiv:1506.01186). Triangular/triangular2/exp_range. Secondary baseline.

**Related techniques to schedule per-phase:**
- **Curriculum Learning Survey** — Soviany et al., 2022 (arXiv:2101.10382). Taxonomy of difficulty measurers + pacing functions.
- **Self-Paced Learning** — Kumar et al., 2010 (NeurIPS). Model dynamically selects easier samples → matures.
- **Knowledge Distillation** — Hinton et al., 2015 (arXiv:1503.02531). Temperature scheduling for soft targets.
- **mixup** — Zhang et al., 2018 (arXiv:1710.09412). α parameter schedulable per-phase.
- **RandAugment** — Cubuk et al., 2019 (arXiv:1909.13719). N (transforms) and M (magnitude) schedulable.
- **Example Forgetting** — Toneva et al., 2019 (arXiv:1812.05159). Forgettable/hard examples for Peaking phase.
- **Data Diet / GraNd scoring** — Paul et al., 2021 (arXiv:2106.03745). EL2N scores for selecting important examples.

**Closest prior work:**
- **Wide-minima density hypothesis** — Iyer et al., 2023 (JMLR). Proposes high-LR "exploration" then low-LR "exploitation" — structurally similar 2-phase approach.
- **Bag of Tricks** — He et al., 2019 (arXiv:1812.01187). Staged training yields +4% on ResNet-50 ImageNet.

**Novelty gap confirmed:** No existing paper maps sports periodization macrocycles (Foundation→Specialization→Peaking) to neural network training. All prior work uses at most 2 phases (warmup→decay) or applies all techniques simultaneously.

**Recommended architectures:** ResNet-18/34/50, WideResNet-28-10, DenseNet-BC-100. **Datasets:** CIFAR-100, Tiny ImageNet, SVHN.

### Reverse Ablation — Key Papers Found (Research Depth: HIGH)

**Direct foil paper:**
- **Meyes et al., 2019** — "Ablation Studies in Artificial Neural Networks" (arXiv:1901.08644, ~519 citations). The ONLY dedicated methodology paper on ablation. Uses standard "remove components from trained model" approach. You would flip this to "add components from trivial baseline."

**Related work to compare against:**
- **Lottery Ticket Hypothesis** — Frankle & Carbin, 2019 (arXiv:1803.03635, ICLR). Finds subnetworks via iterative pruning, not constructive addition.
- **ALBERT** — Lan et al., 2019 (arXiv:1909.11942). Controlled removal experiments on BERT components.
- **DARTS** — Liu et al., 2019 (arXiv:1806.09055, ICLR). Differentiable NAS that finds architectures automatically.
- **Scaling Laws** — Kaplan et al., 2020 (arXiv:2001.08361). Shows architecture details (width/depth) have minimal effect within wide range — predicts concave build-up curve.
- **Scaling Vision Transformers** — Zhai et al., 2022 (arXiv:2106.04560). ViT scaling behavior to 2B params.

**Cross-domain foundation:**
- Forward selection vs backward elimination in regression (since 1960s) — structurally identical. Cite feature-selection literature.

**Recommended architectures:** ResNet-20/56, ViT-Tiny/Small, MLP-Mixer-S/16. **Datasets:** CIFAR-10/100, Tiny ImageNet.

### Keystone Neurons — Key Papers Found (Research Depth: HIGH)

**Core implementation toolkit:**
- **NNsight** — Fiotto-Kaufman et al., 2024 (arXiv:2407.14561). 984★. Activation patching for ANY PyTorch model. MIT license, v0.7.0 May 2026. Primary tool for causal tracing on ViTs.
- **ACDC** — Conmy et al., NeurIPS 2023 Spotlight (arXiv:2304.14997). 293★. Algorithm: iteratively ablate edges/nodes, measure metric drop. Port to ViTs using nnsight.

**Pruning methods to compare against:**
- **SparseViT / SViTE** — Chen et al., 2022 (arXiv:2202.09268). Prunes attention heads + MLP neurons via learned importance.
- **WD-Pruning** — Yu et al., NeurIPS 2022 (arXiv:2210.09468). Shows magnitude pruning misses structurally important components — directly supports your keystone thesis.
- **DepGraph** — Fang et al., CVPR 2023 (arXiv:2301.12900). 7k★. Structural pruning with dependency awareness. SOTA for structured ViT pruning.

**DINOv3 specifics:**
- Paper: Siméoni et al., Aug 2025 (arXiv:2508.10104). Repo: 10.9k★.
- **ViT-B/16 distilled (86M params):** Recommended. Fits 12GB VRAM with room for nnsight batched tracing. 12 layers × 12 heads = 144 heads to score causally.

**ViT interpretability papers:**
- "What Do Vision Transformers Learn?" — Park & Kim, 2022 (arXiv:2205.10607): Ablation study — some heads encode position, others semantics.
- "ViTs Are Robust To Attention Head Removal" — Kobayashi et al., 2023: Up to 50% of heads can be masked with minimal accuracy drop. Supports keystone thesis (few heads carry the signal).

**The gap:** No paper uses causal tracing/activation patching to identify causally important heads in ViTs for pruning. LLM mech interp has nnsight/TransformerLens/ACDC but targets language models. ViT interpretability studies attention maps but doesn't do causal ablation at head/neuron level.

**Compute estimate:** ~144 heads × ~1700 test images ≈ 245K inferences. On RTX 3060 batch=16: ~3-4 hours for head-level scoring. Neuron-level needs sampling.

### Original Antigenic Sin — Key Papers Found (Research Depth: HIGH)

**Core methods:**
- **CKA** — Kornblith et al., ICML 2019 (arXiv:1905.00414). Official colab in google-research repo.
- **Representation Forgetting in CL** — Davari et al., NeurIPS 2022 (arXiv:2203.09121). Closest existing work. Measures CKA across CL tasks.
- **Anatomy of Catastrophic Forgetting via CKA** — Ramasesh et al., NeurIPS 2022 (arXiv:2107.08074). Representation convergence plateaus = "lock-in" by another name.

**CL methods to compare against:**
- EWC — Kirkpatrick et al., PNAS 2017 (arXiv:1612.00796)
- MAS — Aljundi et al., ECCV 2018 (arXiv:1711.09601)
- DER/DER++ — Buzzega et al., NeurIPS 2020 (arXiv:2004.07211)
- LwF — Li & Hoiem, TPAMI 2017 (arXiv:1606.09282)
- All available in **Avalanche** (github.com/ContinualAI/avalanche) — dominant CL framework.

**Risk noted:** Ramasesh/Davari already study representation drift via CKA. Needs clear differentiation from existing CKA-in-CL analyses. Immunological framing + booster-shot must be clearly novel.

### Model Portfolio Theory — Key Papers Found (Research Depth: MODERATE)

**Baseline to beat:**
- **Deep Ensembles** — Lakshminarayanan et al., NeurIPS 2017 (arXiv:1612.01474). Uniform averaging. Reference implementation at google/uncertainty-baselines.

**Calibration/OOD tools:**
- **ECE/MCE** — Guo et al., ICML 2017 (arXiv:1706.04599). Standard calibration metrics.
- **OOD benchmarks:** CIFAR-10 vs SVHN, CIFAR-100 vs TinyImageNet. Both in uncertainty-baselines.
- **netcal**: pip-installable calibration framework. ECE/MCE in one line.

**Risk noted:** Covariance matrix of ensemble predictions is rank-deficient (correlated models). Needs shrinkage estimator (Ledoit-Wolf). Efficient frontier may be flat if models too correlated — MPT framing visually underwhelming.

## Rejection Summary

| # | Idea | Reason Rejected |
|---|------|----------------|
| 1 | Orthogonal Adapter Composition | Duplicated by stronger CL ideas (OAS) |
| 2 | Latent Consistency Distillation for Audio | Complex audio pipeline, scope risk |
| 3 | Graph-Structured Feature Decorrelation | Too speculative, narrow contribution |
| 4 | Multi-Resolution Patch Diffusion | Diffusion training very slow on CPU |
| 5 | Bidirectional Mamba for Audio Restoration | Complex audio preprocessing pipeline |
| 6 | Token-Level Prototypical Calibration | Too niche, hard to validate |
| 7 | Self-Evaluating Model | Too vague, hard to scope cleanly |
| 8 | Forgetting Signatures | Narrow contribution, hard to generalize |
| 9 | Benchmark Synthesis via Diffusion | Complex, diffusion for eval generation is circular |
| 10 | Predicting Hyperparameters | Well-studied area, insufficient novelty |
| 11 | Forward-Only Contrastive Learning | Novel but high risk of underperforming |
| 12 | Activation-Steered Model Composition | Too speculative, uncertain outcome |
| 13 | Frozen Model Interpolation | Interesting but narrow, hard to scope |
| 14 | Neural Collapse Ultra-Small | Interesting but very narrow, hard to demo |
| 15 | One-Batch Learning | Interesting but thin contribution |
| 16 | Input Gradient Agreement | Overlaps with Model Portfolio Theory |
| 17 | Predicting Learnability from Initialization | Too theoretical, NTK-heavy |
| 18 | Knowledge Amplification | Interesting but hard to validate cleanly |
| 19 | Gradient Trajectory Signatures | Computationally expensive for single student |
| 20 | RepLayer | Complex infrastructure, scope risk |
| 21 | DarkBench | Inference-only, less algorithmic depth |
| 22 | DistilBottleneck | Infrastructure-heavy, less novelty |
| 23 | FewShotForge | Infrastructure, not research algorithm |
| 24 | ContinualAdapter | Duplicated by OAS (stronger framing) |
| 25 | NoRefKit | Too similar to existing IQA literature |
| 26 | TokenBudget | Incremental over ToMe/EViT |
| 27 | Multi-Horizon Intelligence | Interesting but complex dual-stream |
| 28 | Contrapuntal Learning | High risk, complex AV pipeline |
| 29 | Load-Bearing Networks | Duplicates Keystone Neurons (weaker analogy) |
| 30 | Sub-100KB Mamba | Requires embedded hardware (STM32 dev board) |
| 31 | Zero-Label AV Separation | Complex multi-modal, high data requirements |
| 32 | In-Browser 3D Gaussian Splatting | WebGPU dependency, platform risk |
| 33 | Fully Deterministic Training | Tool/library, not research paper |
| 34 | On-Device CL with 1MB Budget | Requires mobile deployment |
| 35 | Adversarially Refined Tabular Diffusion | Incremental over TabDDPM |
