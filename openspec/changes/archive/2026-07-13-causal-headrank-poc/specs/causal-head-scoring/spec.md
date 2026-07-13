## ADDED Requirements

### Requirement: Score all attention heads by causal importance

The system SHALL score each of the 144 attention heads in DINOv3 ViT-B/16 by causal importance using activation patching, producing a ranked list where higher scores indicate greater causal importance for the model's classification output.

#### Scenario: Single head scoring produces a measurable Δ logit
- **WHEN** a single head is patched with a corrupted activation on 100 CIFAR-100 images
- **THEN** the system computes the mean absolute logit difference between clean and patched outputs, and the result is a non-negative float

#### Scenario: All 144 heads are scored
- **WHEN** the system iterates over all 144 head specifications
- **THEN** each head receives a score, and the output is a DataFrame with columns [head_idx, layer, head_in_layer, causal_score, time_seconds, peak_memory_gb]

#### Scenario: Scores are rank-stable across image subsets
- **WHEN** scoring is run twice with different random image subsets (e.g., 100 images vs 200 images, different seeds)
- **THEN** the Kendall τ rank correlation between the two score rankings is ≥ 0.7 (target) and ≥ 0.6 (minimum acceptable)

#### Scenario: Score aggregation supports multiple images
- **WHEN** scoring uses N > 1 images
- **THEN** the per-head score is the mean absolute logit difference across all N images, and the standard error is also reported

### Requirement: Support multiple patching metrics

The system SHALL support at least two patching metrics and make the metric configurable.

#### Scenario: Logit difference metric
- **WHEN** the metric is `logit_diff`
- **THEN** the score for a head is mean |logit_clean - logit_patched| across all images, where logit refers to the target class logit from clean forward pass

#### Scenario: KL divergence metric
- **WHEN** the metric is `kl_div`
- **THEN** the score for a head is mean KL(softmax(logits_clean) || softmax(logits_patched)) across all images

### Requirement: Checkpoint scores incrementally

The system SHALL save intermediate results to disk every 10 heads.

#### Scenario: Checkpoint prevents total loss on crash
- **WHEN** the system scores heads 0-9
- **THEN** it writes `head_scores.csv` with columns [head_idx, layer, head_in_layer, causal_score, score_std, time_seconds, peak_memory_gb]
- **WHEN** head 143 is reached and a checkpoint already exists
- **THEN** the system resumes from the last checkpoint rather than re-scoring completed heads

### Requirement: Cache clean forward pass per image

The system SHALL cache the clean (unperturbed) forward pass outputs once per image batch to avoid redundant computation.

#### Scenario: Clean logits cached
- **WHEN** the first head is scored
- **THEN** the system caches clean logits for each image and reuses them for subsequent heads
- **WHEN** the same image is used for head 0 and head 1
- **THEN** the clean forward pass is executed only once per image
