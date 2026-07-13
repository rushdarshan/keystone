# Evidence Dossier: CAP and ViT Transfer

Source: `CAP_2606.19350.pdf`, arXiv:2606.19350v1 (27 Apr 2026). This dossier extracts evidence only; it does not evaluate or propose a method.

## Problem
- **E01 [Paraphrase].** The paper frames pruning as a way to reduce model size/inference cost, but says existing magnitude or local-gradient signals can damage multi-step reasoning and cause “layer collapse.” (p. 1, §1)
- **E02 [Paraphrase].** Its target is preserving chain-of-thought/task reasoning under pruning, not generic language modeling; calibration is therefore reasoning-focused. (p. 2, “Why focus on chain-of-thought reasoning?”; p. 3, §3.1)

## Method
- **E03 [Paraphrase].** Causal Attribution Pruning (CAP) is training-free and has three stages: mask each attention head and measure loss change; convert head scores to weight scores; globally threshold weights to the requested sparsity. (p. 3, Fig. 1; pp. 5–6, Algorithm 1)
- **E04 [Paraphrase].** The claimed distinction from magnitude/activation criteria is interventional measurement of functional contribution, followed by unstructured weight pruning. (pp. 1–3, Abstract, §2–§3)

## Causal Attribution Definition
- **E05 [Formula/paraphrase].** For head h in layer l, Δ(h_l) is the expected increase in token-level cross-entropy under temporary head masking: E[(L(f_mask(h_l)(x),y) − L(f(x),y))]. Higher Δ means larger measured task degradation and greater causal importance. (p. 3, Eq. 1; p. 4, §3.2)
- **E06 [Paraphrase].** Masking is applied by a forward hook after head aggregation and before output projection, zeroing the selected head’s attention-output contribution while leaving W_o intact; the stated purpose is to avoid changing internal Q/K/V attention computations. (p. 4, §3.2)
- **E07 [Paraphrase].** The score uses K=3 or 5 disjoint calibration subsets: median masked-loss estimates minus a mean intact-model baseline. The authors report median aggregation as more robust to ablation-induced loss spikes. (p. 4, Eq. 2, §3.2; p. 8, §6)
- **E08 [Scope boundary].** “CAP’s causal scoring operates at the attention head level”; MLP importance is only an approximate layer value derived from co-located heads, and the paper explicitly does not claim causal attribution for individual MLP neurons. (p. 2, “Scope of causal attribution”; pp. 5, 9–10, §§3.3, 7)

## Pruning Procedure
- **E09 [Paraphrase].** Head scores are linearly shifted/scaled to I(h_l) in [1,10], with identical scores mapped to 1.0. Each mapped weight receives S_ij=|W_ij|·I(h_region(i,j)); weights are globally sorted and values at/below a binary-searched threshold are set to zero. (pp. 4–6, Eqs. 3–4, Algorithm 1)
- **E10 [Paraphrase].** Q/K/V rows and O columns are assigned to head regions; MLP weights receive the layer-average head importance. The paper identifies this MLP mapping as an approximation that assumes within-layer covariance between MLP and head importance. (p. 5, §3.3)
- **E11 [Paraphrase].** The implementation uses 128–256 examples/task, fixed seed 0, greedy decoding, exact zeroing, ±0.01% sparsity targeting, and cached head scores; reported sparsities are 10%, 20%, and 50%. (pp. 3, 5–6, §§3.1, 3.4, 4)

## Baselines
- **E12 [Paraphrase].** The main comparison is dense vs. Wanda, selected as the like-for-like training-free, one-shot, no-weight-update baseline using the same calibration data. SparseGPT and simple magnitude pruning are not included in the main comparison. (p. 6, “Baseline selection”; p. 9, §7)
- **E13 [Limitation].** The authors state that broader baseline coverage, especially SparseGPT and a magnitude lower bound at high sparsity, would strengthen the empirical picture. (pp. 9–10, §§7–8)

## Datasets and Evaluation
- **E14 [Paraphrase].** Calibration/evaluation reasoning sources are GSM8K (grade-school math), StrategyQA (multi-hop commonsense), and ARC-Challenge (science/world knowledge); WikiText-2 supplies perplexity evaluation. Calibration examples are disjoint from evaluation examples. (pp. 3, 5–6, §§3.1, 3.4, 4)
- **E15 [Paraphrase].** Models are Llama-3-8B-Instruct and Mistral-7B-Instruct-v0.2, both using grouped-query attention; a mixture-of-experts model is only exploratory. (p. 6, §4)
- **E16 [Limitation].** Reasoning is evaluated only by final-answer accuracy after chain-of-thought generation; the paper says this does not measure intermediate completeness, coherence, error type, or step count. (pp. 6, 9, §§4, 6.1)

## Results
- **E17 [Table evidence].** Table 1 uses n=128 samples/task, K=3 calibration subsets, and median aggregation. At Llama-3 10% sparsity, CAP/Wanda are GSM8K 71.5/59.5, StrategyQA 65.5/65.0, ARC-C 74.2/68.7; at 20%, ARC-C is 70.8/43.9, while GSM8K is 65.4/72.1. (p. 8, Table 1; p. 7, §5.1)
- **E18 [Table evidence].** On Mistral, 10% differences are within 1.5 points; at 20%, CAP is slightly ahead on GSM8K and StrategyQA but behind Wanda on ARC-C. (pp. 7–8, §5.1, Table 1)
- **E19 [Paraphrase].** At 50% Llama-3 sparsity, CAP has ARC-C 30.1 vs. Wanda 8.5 but GSM8K 0.5 vs. 1.7, StrategyQA 6.9 vs. 51.7, and perplexity 428.2 vs. 55.6; the paper attributes this failure primarily to coarse MLP treatment. (pp. 7–8, §5.2, Table 1)
- **E20 [Paraphrase].** At 10–20%, the paper reports better reasoning accuracy often coexisting with slightly worse perplexity, e.g. Llama-3 at 20%: CAP/Wanda perplexity 9.57/8.70 and StrategyQA 63.1/60.5. (p. 8, §5.3, Table 1)

## Ablations and Analyses
- **E21 [Paraphrase].** WikiText-2 calibration gives similar perplexity but tends to underperform reasoning calibration on GSM8K and ARC-C, especially at 20%; mean aggregation is reported less stable than median; K=3 stabilizes rankings vs. K=1, with smaller gains from K=5. (pp. 8–9, §6)
- **E22 [Paraphrase].** Whole-head structural pruning is described as brittle when a high-importance head is mistakenly removed; weight-level pruning retains some capacity in low-importance regions and removes small weights within critical heads. (p. 9, §6)
- **E23 [Figure evidence].** Figure 2 shows Llama-3 importance concentrated in layers 11–14 and boundary layers with redundancy in 15–27, while Mistral is more diffuse with critical heads in layers 0–5; the caption says fewer than 20% of heads have high scores. (p. 12, Fig. 2, Appendix A)

## Limitations
- **E24 [Paraphrase].** CAP is reported as most suitable for moderate sparsity (10–30%); above about 40%, global thresholding can prune weights inside critical heads, while coarse MLP attribution exacerbates collapse. (p. 10, §7)
- **E25 [Paraphrase].** Preliminary MoE tests qualitatively underperformed Wanda, without reported model-specific numbers; dynamic routing makes a single averaged head score potentially non-stationary. (p. 8, §5.4; p. 10, §7)
- **E26 [Paraphrase].** Unstructured sparsity may not produce practical latency gains because hardware/software support remains immature. (p. 10, §7)

## Novelty Overlap and Transfer Risks to ViTs
- **E27 [Overlap evidence].** The paper itself places CAP alongside prior attribution-guided compression in computer vision, including Layer-wise Relevance Propagation/Integrated Gradients for CNNs and vision Transformers, and cites X-Pruner for explainable ViT pruning. It claims its positioning as head-level intervention plus budget-aware weight pruning, not a first attribution-based pruning result in vision. (p. 2, §2; p. 12, references)
- **E28 [Non-transfer assumption].** The causal unit is an LLM attention head with token-level cross-entropy and CoT reasoning calibration. ViTs have patch tokens, class/task-specific visual losses, different attention/head roles, and often token/patch/channel pruning; the paper provides no ViT experiments or visual-task evidence. (pp. 3–6, §§3–4; pp. 7–10, §§5–8)
- **E29 [Non-transfer assumption].** The Q/K/V/O region mapping and layer-average MLP proxy assume LLM projection layouts and head-to-MLP importance covariance; ViT architectures vary in patch embedding, class token, attention layouts, MLP blocks, and task heads. (p. 5, §3.3; p. 10, §7)
- **E30 [Transfer risk].** The reported gains are benchmark-, model-, calibration-, and sparsity-specific: CAP loses to Wanda on Llama-3 GSM8K at 20%, on Mistral ARC-C at 20%, and catastrophically degrades some Llama-3 metrics at 50%. These results do not establish analogous gains for ViT accuracy, robustness, calibration, or efficiency. (pp. 7–10, §§5–8; Table 1)
