# Evidence dossier: Vi-CD / Keystone Neurons relevance

Source: *Seeing Through Circuits: Faithful Mechanistic Interpretability for Vision Transformers*, arXiv:2604.14477v1.
Evidence entries: 30. Page numbers are PDF pages.

## Faithfulness problem
1. [Paraphrase; p. 2, Sec. 1] The paper defines a circuit as faithful when restricting computation to it preserves task performance; faithfulness is intended to distinguish mechanisms from correlates.
2. [Quote; p. 2, Sec. 1] “A key requirement for such circuits is faithfulness.”
3. [Paraphrase; p. 5, Def. 3.2] Formal criterion: `M_T(E) - M_T(E_C) <= epsilon`, where `M_T` is the task-fidelity metric.
4. [Paraphrase; pp. 2, 4, Secs. 1, 3] Existing vision work is described as neuron-, channel-, or feature-level; the claimed gap is explicit modeling of information flow between components.

## Method
5. [Paraphrase; pp. 4-6, Fig. 2, Secs. 3-3.2] Vi-CD represents a ViT as a directed residual-stream graph, selects edges by sequential activation patching, and prunes an edge when its removal causes a sufficiently small target-logit change.
6. [Paraphrase; p. 6, Sec. 3.2, Fig. 3] An attention-input receiver node aggregates attention-block residual input, reducing candidate edges by approximately a factor of the number of heads without changing stated functionality.
7. [Paraphrase; pp. 6-7, Eqs. 1-3] Candidate-circuit edges receive clean-run contributions while non-circuit edges receive corrupted-run contributions; the patched model is then scored.
8. [Paraphrase; p. 3, Sec. 2] The paper positions Vi-CD as a vision transfer of edge-centric circuit discovery, contrasting it with EAP/EAP-IG approximations developed for language models.

## Intervention design
9. [Paraphrase; pp. 8-9, Sec. 3.3] For attack circuits, the method estimates a corruption-aligned direction from paired clean/corrupted activations and applies patchwise directional ablation only on circuit edges.
10. [Paraphrase; p. 8, Sec. 3.3, Alg. 1] The intervention subtracts `alpha ReLU(c_p) v_j,p`; ReLU removes positively aligned projections and avoids amplifying anti-correlated features.
11. [Paraphrase; pp. 20-23, Secs. C.2-C.5, Fig. 7, Table 6] Typographic evaluation uses clean images and controlled text-overlay corruptions; steering was evaluated with pre/post normalization and mean/medoid aggregation, with subsequent experiments using pre-normed mean.
12. [Paraphrase; pp. 12, 35-37, Table 1, Fig. 17, Sec. G] Matched-size random-edge and random-non-circuit controls are used to test whether effects are specific to discovered edges rather than generic ablation.

## Circuit/objective definition
13. [Paraphrase; p. 5, Def. 3.1] A circuit is an edge subset `E_C` of the model graph; edges are additive residual-stream contributions between model components.
14. [Paraphrase; p. 8, Def. 3.3] A class circuit is `(D_A, M, E_C)`: correctly classified target-class examples, a scalar metric such as accuracy, and a faithful edge circuit evaluated by activation patching.
15. [Paraphrase; pp. 7, 18, Sec. 3.3, App. A] Target logit difference is the pruning objective because it is aligned with the classification decision boundary; thresholds are selected for over 80% performance retention and maximal sparsity.
16. [Paraphrase; pp. 9, 19, Sec. 4.1, App. B] Reported quality axes are restricted-circuit classification accuracy (faithfulness) and retained-edge fraction (sparsity); Jaccard similarity is used for circuit overlap.

## Datasets and models
17. [Paraphrase; pp. 7, 18, Sec. 3.3, App. A, Table 3] Class circuits use ForAug-processed ImageNet images: foreground segmentation and inpainting remove class evidence while preserving background statistics and low-level structure; `N=128` correctly classified images per class are used.
18. [Paraphrase; pp. 9, 19, Sec. 4.1, App. B] Main models are supervised ViT-B trained on ImageNet and OpenCLIP ViT-B/32; OpenCLIP classification uses a zero-shot ImageNet text-embedding classifier matrix.
19. [Paraphrase; pp. 9, 20-21, Sec. 4.1, Sec. C.2, Table 5] Typographic circuits use 13 effective attack words and three regimes: big text, multiple small texts, and bezel overlays; the big-text setup avoids fully occluding the main object.
20. [Paraphrase; pp. 12-13, Sec. 4.5, Table 2, App. C.6, Table 9] RoCOCO evaluates image-to-text retrieval on MS-COCO with danger words inserted into captions; safety is RSMS and utility is R@1/R@5/R@10/Rmean.

## Results
21. [Paraphrase; p. 10, Fig. 4, Sec. 4.2] Vi-CD is reported to achieve near-perfect ViT-B classification while retaining fewer than 10% of edges; comparable EAP-IG circuits require substantially more edges, summarized as approximately 10x sparsity advantage.
22. [Paraphrase; p. 12, Table 1, Sec. 4.4] Average Top-1 ASR falls from 39.1% to 2.8% for big text, 39.4% to 1.6% for small text, and 39.5% to 3.1% for bezel; clean Top-1 accuracy changes from 57.0% to 55.8%, 57.1% to 55.7%, and 57.1% to 49.9% respectively.
23. [Paraphrase; p. 13, Table 2, Sec. 4.5] At `alpha=0.4`, RSMS changes from 11.68% baseline to 5.15%, 5.69%, and 4.86% for Assault Rifle, Revolver, and Rifle circuits; Rifle Rmean rises from 62.74% to 64.37%.

## Ablations and stability
24. [Paraphrase; pp. 34-35, App. F, Fig. 16] The paper sweeps KL divergence and target-logit-difference selection criteria over thresholds; figures report accuracy and sparsity for CLIP and ViT-B.
25. [Paraphrase; pp. 35-37, App. G, Fig. 17] Circuit-edge steering uniquely combines ASR suppression with performance retention; random matched-size edges suppress ASR less consistently, while non-circuit edges can increase ASR at strong steering through middle layers.
26. [Paraphrase; pp. 11, 30-32, Fig. 5, Figs. 10-13, Sec. D] Same-class circuits share a core but are not identical; the discussion reports Jaccard similarities of 0.6-0.8, 34.5% of edges appearing in 90-100% of repeated runs, and increasing stability with larger mining batches.
27. [Paraphrase; p. 32, Fig. 12, Sec. D] Edges originating from attention heads, especially `attn->attn_input` and `attn->mlp`, are disproportionately unstable across runs in both ViT-B and CLIP.
28. [Paraphrase; pp. 33-34, Figs. 14-15, Sec. E] Unions of class circuits support zero-shot binary classification, and explicitly mined binary circuits overlap strongly with per-class circuit unions; this is evidence for reuse/compositionality, not a head-pruning result.

## Limitations and relevance to head-level pruning
29. [Paraphrase; p. 14, Sec. 5] The authors state that Vi-CD costs at least one patching intervention per edge and is more expensive than EAP/EAP-IG; scaling to the largest transformers remains open.
30. [Paraphrase; p. 14, Sec. 5] The paper explicitly leaves neuron-within-edge semantics, non-classification tasks, training-time circuit evolution, and robustness under distribution shift unexplored.
31. [Paraphrase; pp. 2, 5-8, Secs. 1, 3] Faithfulness is defined for an edge-restricted graph under activation patching, whereas head-level pruning removes whole components; therefore the paper does not establish that an edge circuit maps to a minimal or safe set of removable attention heads.
32. [Paraphrase; pp. 6-7, Fig. 3, Sec. 3.2] The attention-input graph reduction preserves stated functional dependencies for discovery, but it does not itself provide a hardware/pruning transformation or head-retention criterion.
33. [Paraphrase; pp. 11, 14, Secs. 4.3, 5] Imperfect same-class overlap and the authors' interpretation as a distribution of plausible circuits indicate that circuit membership is not a unique ground-truth importance ranking for heads.

## Novelty overlap and discovery/pruning gap
34. [Paraphrase; pp. 2-4, Secs. 1-2] Novelty claimed by the paper: first edge-based circuit discovery for vision transformers, extending language-model circuit methods; prior vision approaches cited here are node/neuron/feature/path based.
35. [Paraphrase; pp. 2-3, Sec. 2; p. 14, Sec. 5] The novelty overlaps causal-importance-guided pruning at the level of importance estimation and intervention, but Vi-CD's unit is an edge and its endpoint is faithful explanation/steering, not a head-pruned model.
36. [Paraphrase; pp. 8, 12-14, Secs. 3.3-5] Discovery-to-pruning gap: the demonstrated causal intervention is directional activation ablation on selected edge hooks, while reported sparsity is graph-edge retention; no experiment reports accuracy, latency, parameter count, or retraining after physically deleting attention heads.
