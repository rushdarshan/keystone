## Why

The research project "Interpretability-Guided Structured Model Compression" proposes using activation patching (via nnsight) to score attention heads by causal importance and guide structured pruning of Vision Transformers. This approach is novel, but its core technical assumption — that activation patching can produce stable, practical head importance scores for DINOv3 ViT-B/16 within a 12GB VRAM budget — has never been validated. Before investing 10-12 weeks in the full project, we need a 2-3 day feasibility proof of concept.

Failure scenarios that this PoC gates against: nnsight incompatibility with DINOv3, unstable rankings, memory overflow, impractical runtime.

## What Changes

- Create `src/keystone/` package with the minimal core pipeline
- Implement activation patching on a single DINOv3 ViT-B/16 attention head via nnsight
- Score all 144 heads on CIFAR-100 and measure ranking stability
- Profile memory and runtime to validate hardware feasibility
- Create `scripts/run_poc.py` as the single entry point
- Document hook locations, memory profiles, and timing results

## Capabilities

### New Capabilities
- `causal-head-scoring`: Score all attention heads in a ViT by causal importance using activation patching, producing a ranked list with stability metrics
- `nnsight-vit-integration`: Hook and intervene on DINOv3 ViT-B/16 attention heads via nnsight, with documented layer names and intervention points
- `hardware-validation`: Profile GPU memory and runtime for activation patching on a consumer GPU, producing a pass/fail report against Go/No-Go thresholds

### Modified Capabilities
No existing specs to modify.

## Impact

- **New code**: `src/keystone/` package (~300 lines), `scripts/run_poc.py` (~80 lines)
- **New dependencies**: nnsight, timm, torchvision
- **Data**: CIFAR-100 (auto-downloaded by torchvision)
- **No changes** to existing `reverse_ablation/` package or `run_experiment.py`
- **Hardware**: Requires CUDA GPU with ≥8GB VRAM
