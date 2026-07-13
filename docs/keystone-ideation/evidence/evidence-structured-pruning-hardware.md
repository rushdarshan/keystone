# Evidence Dossier: Structured Pruning and Real Hardware Effects
Scope: continuing Keystone Neurons / causal importance-guided structured pruning for Vision Transformers.

## Planned structured pruning

1. “Prune lowest-scoring heads at multiple ratios (25%, 50%, 75%, 90%).”
   `docs/brainstorms/keystone-neurons-requirements.md:102`

2. “Structured pruning with dependency awareness (heads + associated MLP neurons). Neuron-level hierarchical analysis deferred to Phase B / Future Work.”
   `docs/brainstorms/keystone-neurons-requirements.md:103`

3. “Structured pruning implementation (deferred to later milestone)”
   `openspec/changes/causal-headrank-poc/design.md:17`

4. “Head-level pruning only. Neuron-level analysis deferred.”
   `docs/brainstorms/keystone-neurons-requirements.md:216`

5. “Structured pruning only (no unstructured sparsity).”
   `docs/brainstorms/keystone-neurons-requirements.md:218`

6. “No real-time optimization beyond FLOPs/throughput.”
   `docs/brainstorms/keystone-neurons-requirements.md:232`

7. “SparseViT — learned importance + structured ViT pruning SOTA.”
   `docs/brainstorms/keystone-neurons-requirements.md:110`

8. “DepGraph — dependency-aware structured pruning.”
   `docs/brainstorms/keystone-neurons-requirements.md:111`

9. “SparseViT and DepGraph integration strategy (existing repos vs reimplement).”
   `docs/brainstorms/keystone-neurons-requirements.md:272`

## Masking, head representation, and projection structure

10. “The PoC only implements activation patching”
    `openspec/changes/causal-headrank-poc/design.md:65`

11. `head_outputs[:, head_idx] = replacement.to(device=head_outputs.device, dtype=head_outputs.dtype)`
    `src/keystone/patching.py:134-138`

12. `qkv = qkv.reshape(batch, tokens, 3, module.num_heads, -1).permute(2, 0, 3, 1, 4)`
    `src/keystone/patching.py:111-114`

13. `q = module.q_proj(x).reshape(batch, tokens, module.num_heads, -1).transpose(1, 2)`
    `src/keystone/patching.py:115-118`

14. `x = head_outputs.transpose(1, 2).reshape(batch, tokens, attn_dim)`
    `src/keystone/patching.py:140-145`

15. `x = module.proj(x)`
    `src/keystone/patching.py:140-146`

16. `if hasattr(module, "num_heads") and (hasattr(module, "qkv") or hasattr(module, "q_proj")):`
    `src/keystone/vit_adapters.py:36-41`

17. `self.qkv = nn.Linear(embed_dim, embed_dim * 3)` and `self.proj = nn.Linear(embed_dim, embed_dim)`
    `reverse_ablation/components/attention.py:8-16`

18. `qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)`
    `reverse_ablation/components/attention.py:18-25`

19. “No changes to existing `reverse_ablation/` package or `run_experiment.py`”
    `openspec/changes/causal-headrank-poc/proposal.md:26-32`

## Dependencies and implementation gaps

20. “Structured pruning implementation (deferred to later milestone)”
    `openspec/changes/causal-headrank-poc/design.md:16-18`

21. “The full research project requires scoring 144 attention heads by causal importance using activation patching.”
    `openspec/changes/causal-headrank-poc/design.md:1-5`

22. “The system SHALL score each of the 144 attention heads ... producing a ranked list”
    `openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:3-5`

23. “The system SHALL save intermediate results to disk every 10 heads.”
    `openspec/changes/causal-headrank-poc/specs/causal-head-scoring/spec.md:35-43`

24. “If memory grows monotonically across heads, we have a leak and fail the PoC.”
    `openspec/changes/causal-headrank-poc/design.md:73-77`

25. `temporary_metadata.replace(metadata_path)`
    `src/keystone/scoring.py:148-163`

26. `pass`
    `reverse_ablation/analysis/pareto.py:100-105`

## Hardware measurement requirements and workarounds

27. “FLOPs reduction, parameter count, throughput (inferences/sec), peak VRAM.”
    `docs/brainstorms/keystone-neurons-requirements.md:119-124`

28. “Inference latency: unpruned vs. pruned at each ratio” and “FLOPs per forward pass at each sparsity level”
    `docs/brainstorms/keystone-neurons-requirements.md:180-187`

29. “The system SHALL track and report peak CUDA memory allocation at each stage of the activation patching pipeline.”
    `openspec/changes/causal-headrank-poc/specs/hardware-validation/spec.md:3-9`

30. “The system SHALL measure and report the time required to score each individual head”
    `openspec/changes/causal-headrank-poc/specs/hardware-validation/spec.md:19-25`

31. “The system SHALL test patching at batch sizes [2, 4, 8, 16] to find the optimal memory-throughput tradeoff.”
    `openspec/changes/causal-headrank-poc/specs/hardware-validation/spec.md:35-45`

32. `torch.cuda.empty_cache()` and `torch.cuda.reset_peak_memory_stats()` occur before each head.
    `src/keystone/scoring.py:35-43`

33. `except torch.cuda.OutOfMemoryError:` followed by halving `batch_size` and calling `torch.cuda.empty_cache()`.
    `scripts/run_poc.py:146-163`

34. “If this strategy fails ... we switch to subprocess isolation”
    `openspec/changes/causal-headrank-poc/design.md:75-77`

35. `throughput = 3600 / seconds if seconds > 0 else 0.0`
    `scripts/run_poc.py:173-191`

## Recorded results and contradictions

36. `"gpu_name": "NVIDIA GeForce RTX 4050 Laptop GPU", "gpu_memory_gb": 6.44`
    `experiments/smoke_v2/environment.json:1-11`

37. `"gpu_memory_gb": 6.44` versus the stated “within a 12GB VRAM budget”.
    `experiments/smoke_v2/failure_report.md:13-22`; `openspec/changes/causal-headrank-poc/proposal.md:3-5`

38. `"discovered_heads": 144`, `"captured_head_shape": [1, 201, 64]`, and `"passed": true`.
    `experiments/pretrained_smoke_v2/results.json:7-27`

39. `"estimate_seconds": 68.03264160006802`, `"method": "mean"`, and `"peak_memory_gb": 0.39003904`.
    `experiments/pretrained_smoke_v2/results.json:34-43`

40. `"Q3": null` while `"Q4": true` and `"Q5": true`.
    `experiments/pretrained_smoke_v2/results.json:62-70`

41. `head_idx,...,time_seconds,peak_memory_gb` and `0,...,0.203332699999919,0.364057088`.
    `experiments/smoke_v2/q2_head_scores.csv:1-2`

42. `"verdict": "NO-GO"` with `"Q2": false`, `"Q3": null`, `"Q4": null`, and `"Q5": null`.
    `experiments/smoke_v2/results.json:35-50`

43. `PermissionError: [WinError 32] ... 'q2_head_scores.meta.json.tmp' -> 'q2_head_scores.meta.json'`
    `experiments/smoke_v2/failure_report.md:3-7`

44. “No comparison against structured pruning baselines (only Wanda for unstructured)”
    `papers/CC-Prune_GitHub_README.md:21-27`

45. “Pruning (magnitude pruning of non-circuit components)”
    `papers/CC-Prune_GitHub_README.md:10-18`

46. “No activation patching framework like nnsight — appears to use custom patching”
    `papers/CC-Prune_GitHub_README.md:21-27`
