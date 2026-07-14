# Plan 001: Update README with actual benchmark results and paper link

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.

> **Drift check (run first)**: `git diff --stat a377c37..HEAD -- README.md experiments/full_run_v2/results.json paper/keystone.md`
> If README.md changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, treat it as
> a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `a377c37`, 2026-07-13

## Why this matters

The current README shows only PoC feasibility results (Q1-Q5 gates). Readers and potential reviewers land on the repo to see the research outcomes — not infrastructure validation. The actual benchmark results (gradient beats causal, magnitude destroys the model) are the project's contribution. They must be front-and-center. Additionally, the paper draft (`paper/keystone.md`) exists but has no link from the README, so visitors never find it.

## Current state

**File: `README.md`** — The "Results" section (lines 52–64) contains only the PoC gate table:

```markdown
## Results

**Feasibility PoC** — DINOv3 ViT-B/16, CIFAR-100, RTX 4050 (6.44 GB VRAM):

| Gate | Threshold | Result |
|------|-----------|--------|
| Q0 — Linear probe accuracy | ≥ 10% | **80.7%** |
| Q1 — Head discovery | 144 heads | **144/144** |
...
```

The actual benchmark results are at `experiments/full_run_v2/results.json` with probe accuracy values for all 4 methods × 4 sparsity ratios. These are not mentioned anywhere in the README.

The "Citation" section (line 95–101) has an empty `author` field:
```bibtex
author = {},
```

There is no link to `paper/keystone.md`.

The "Quick Start" section lacks a GPU/VRAM requirement note.

## What changes

1. **Replace the Results section** with two tables: PoC validation (kept, condensed) and the main benchmark results.
2. **Add a "Key Findings" section** with 3 bullets summarizing the research outcomes.
3. **Add a link** to `paper/keystone.md` under a "Paper" heading after Results.
4. **Fill in the author field** in Citation as `rushdarshan`.
5. **Add a "Requirements" section** before Quick Start noting GPU, CUDA, and VRAM needs.

### Files in scope
- `README.md` — modify only

### Files explicitly out of scope
- Do NOT modify any file under `src/`, `scripts/`, `tests/`, `paper/`, `experiments/`, `docs/`
- Do NOT change the project structure tree, installation instructions, or How It Works section
- Do NOT add badges, change the license, or restructure sections beyond what's specified

## Steps

### Step 1: Read the benchmark results to extract accurate numbers

Run this and confirm it prints JSON with no errors:

```bash
python -c "import json; d=json.load(open('experiments/full_run_v2/results.json')); r=d['42']; print('causal:', {k: round(v.get('top1_accuracy',0),3) for k,v in r['causal'].items()}); print('magnitude:', {k: round(v.get('top1_accuracy',0),3) for k,v in r['magnitude'].items()}); print('gradient:', {k: round(v.get('top1_accuracy',0),3) for k,v in r['gradient'].items()}); print('random:', {k: round(v.get('top1_accuracy',0),3) for k,v in r['random'].items()})"
```

Expected output: four dicts showing accuracy at each ratio (0.25, 0.5, 0.75, 0.9).

### Step 2: Replace the Results section

In `README.md`, replace lines 52–64 (the entire `## Results` section through the Go/No-Go table) with:

```markdown
## Results

### Feasibility PoC

DINOv3 ViT-B/16 on CIFAR-100, RTX 4050 (6.44 GB VRAM):

| Gate | Result |
|------|--------|
| Head discovery | 144/144 |
| Ranking stability (Kendall τ) | 0.849 |
| Runtime (all 144 heads) | 198s |
| Peak VRAM | 0.61 GB |
| **Verdict** | **GO** |

### Pruning Benchmark

Post-prune linear probe accuracy at 4 sparsity ratios (1000 CIFAR-100 images, 25 probe epochs):

| Method | 25% sparsity | 50% sparsity | 75% sparsity | 90% sparsity |
|--------|-------------|-------------|-------------|-------------|
| **Gradient** | **49.0%** | 14.6% | 8.8% | 8.6% |
| Causal | 35.4% | 12.6% | 9.4% | 9.0% |
| Random | 35.0% | 8.8% | 7.8% | 7.4% |
| Magnitude | 6.0% | 6.0% | 6.0% | 6.6% |

### Key Findings

- **Causal importance and weight magnitude are complementary signals** — Kendall τ = -0.15, confirming the keystone hypothesis that magnitude misses causally important heads.
- **Gradient-based importance is the most effective pruning signal** — 49% accuracy at 25% sparsity vs. 35% for causal and 6% for magnitude.
- **Structured head removal is inherently destructive** without fine-tuning — even at 25% sparsity, accuracy drops from 80.7% (unpruned) to 35–49%.
```

### Step 3: Add Requirements section before Quick Start

Insert after the Installation section (after line 19) and before `## Quick Start`:

```markdown
## Requirements

- Python 3.13+
- CUDA-capable GPU with ≥6 GB VRAM (tested on RTX 4050 Laptop)
- PyTorch 2.x with CUDA support
```

### Step 4: Add Paper link after Results

Insert after the `## Results` section (after the Key Findings bullets, before `## Project Structure`):

```markdown
## Paper

A full paper draft is available at [`paper/keystone.md`](paper/keystone.md).
```

### Step 5: Fill in citation author

In the Citation section, change:
```bibtex
author = {},
```
to:
```bibtex
author = {rushdarshan},
```

### Step 6: Verify

Run these checks:

```bash
# README exists and is non-empty
python -c "content = open('README.md').read(); assert len(content) > 500, 'README too short'; assert '## Paper' in content, 'Paper link missing'; assert '49.0%' in content, 'Benchmark results missing'; assert 'rushdarshan' in content, 'Author missing'; print('OK')"
```

Expected output: `OK`

## STOP conditions

- If `results.json` is missing or malformed (Step 1 fails): STOP — the benchmark hasn't been run. Report "Need to run full_run_v2 benchmark first."
- If any required section heading (`## Paper`, `## Requirements`) already exists in the README: STOP — it may have already been added. Report the duplicate.
- If the README.txt format is significantly different from what's shown in "Current state": STOP — the file has drifted. Report the differences.

## Patterns to follow

The README uses standard GitHub-flavored markdown with pipe tables. Follow the existing style:
- H2 headings (`##`) for sections
- Pipe-delimited tables with bold header rows
- Bare URLs in code blocks (no angle brackets)
- Single blank line between sections

## Maintenance note

If benchmark results are regenerated with different probe data or seed values, update the numbers in the `### Pruning Benchmark` table. The paper at `paper/keystone.md` should also be updated to match. These two files should stay in sync.
