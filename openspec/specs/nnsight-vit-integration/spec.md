# NNsight ViT Integration

## Purpose

Hook and intervene on DINOv3 ViT-B/16 attention heads via nnsight, with documented layer names and intervention points.

## Requirements

### Requirement: Hook and intervene on a single attention head

The system SHALL load a DINOv3 ViT-B/16 via timm, wrap it with nnsight, and register an intervention on a single attention head that replaces its output activation with a different value.

#### Scenario: Successful hook on DINOv3 head
- **WHEN** the system loads `vit_base_patch16_reg8_dino` via timm and wraps the model with nnsight's `ndiff` context
- **THEN** all 144 attention head modules are discoverable via `model.named_modules()`, and the system logs each hook point with its layer index and head index

#### Scenario: Activation replacement succeeds on one head
- **WHEN** the system performs a forward pass with an intervention that replaces the output of ONE attention head with a corrupted activation
- **THEN** the forward pass completes without error and produces different logits than the unperturbed forward pass

#### Scenario: DINOv2 fallback hook
- **WHEN** nnsight fails to hook DINOv3 (import error, module not found, or intervention crash)
- **THEN** the system falls back to `vit_base_patch14_dinov2` and retries the intervention

#### Scenario: Hook point documentation
- **WHEN** the system discovers hook points
- **THEN** it prints a table of (layer_name, layer_index, head_index, nnsight_accessor) for every discovered head to stdout

### Requirement: Fail on single head before scaling to all heads

The system SHALL validate that one head can be hooked and produce a measurable effect before attempting to score all 144 heads.

#### Scenario: One-head validation gate
- **WHEN** the system starts scoring
- **THEN** it first hooks and patches ONE head. If that fails, it generates a failure report and stops. If it succeeds, it hooks TEN heads. Only after 10 heads succeed does it proceed to all 144.

### Requirement: Fail gracefully on unsupported model

The system SHALL detect when a model cannot be hooked by nnsight and report the specific failure reason rather than crashing silently.

#### Scenario: Unsupported model architecture
- **WHEN** a model does not contain expected attention module patterns
- **THEN** the system prints the first 10 discovered module names to stdout and exits with a clear error message describing what pattern was expected vs found

### Requirement: Generate failure report on Q1 failure

When Q1 (nnsight hook) fails, the system SHALL generate a structured failure report instead of just printing an error.

#### Scenario: Failure report contains environment diagnostics
- **WHEN** Q1 fails
- **THEN** the system writes `failure_report.md` containing the traceback, model tree (first 20 module names), attempted fixes, environment metadata (python/torch/timm/nnsight versions, GPU info), and the exact error message
