# Hardware Validation

## Purpose

Profile GPU memory and runtime for activation patching on a consumer GPU, producing a pass/fail report against Go/No-Go thresholds.

## Requirements

### Requirement: Measure peak GPU memory during patching

The system SHALL track and report peak CUDA memory allocation at each stage of the activation patching pipeline.

#### Scenario: Memory profiled per head
- **WHEN** each head is scored
- **THEN** the system records `torch.cuda.max_memory_allocated()` before and after the patching forward pass, and logs the difference

#### Scenario: Memory budget validation
- **WHEN** scoring completes for all heads
- **THEN** the system reports peak memory across all heads and produces PASS if peak < 11 GB, FAIL otherwise

#### Scenario: Memory trend detection
- **WHEN** peak memory increases monotonically across sequential heads (no decrease after cache clearing)
- **THEN** the system warns of a potential memory leak and stops further head scoring

### Requirement: Measure runtime per head and estimate total with 95% CI

The system SHALL measure and report the time required to score each individual head, and estimate the total time to score all 144 heads using a linear model with 95% confidence interval.

#### Scenario: Per-head timing
- **WHEN** each head is scored
- **THEN** the system records wall-clock time for that head's patching forward pass, excluding any cache clearing or logging overhead

#### Scenario: Runtime estimation with warmup
- **WHEN** at least 10 heads (after a warmup budget of 5 heads) have been scored
- **THEN** the system fits a linear model: time_per_head = β₀ + β₁ × head_idx, and reports predicted total = ∑(β₀ + β₁ × i) for i = 6..143, with 95% confidence interval

#### Scenario: Runtime budget validation
- **WHEN** the estimated total runtime is computed
- **THEN** the system produces PASS if estimated total ≤ 12 hours, FAIL otherwise

### Requirement: Profile at multiple batch sizes

The system SHALL test patching at batch sizes [2, 4, 8, 16] to find the optimal memory-throughput tradeoff.

#### Scenario: Batch size sweep
- **WHEN** the user passes `--sweep-batch-size`
- **THEN** the system scores a single head at each batch size and reports (batch_size, time, peak_memory, throughput_heads_per_hour)

#### Scenario: Recommended batch size
- **WHEN** the batch size sweep completes
- **THEN** the system recommends the batch size that maximizes throughput while keeping peak memory < 10 GB

### Requirement: Log environment automatically

The system SHALL write environment metadata alongside experiment results.

#### Scenario: environment.json written at start
- **WHEN** any scoring run begins
- **THEN** the system writes `environment.json` to the output directory containing:
  - `python_version`, `torch_version`, `cuda_available`, `cuda_version`, `cudnn_version`
  - `timm_version`, `nnsight_version`, `gpu_name`, `gpu_memory_gb`, `gpu_driver_version`
