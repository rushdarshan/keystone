---
title: Validate and Finalize CausalHeadRank Feasibility PoC
type: feat
status: active
date: 2026-07-13
origin: docs/brainstorms/keystone-neurons-requirements.md
---

# Validate and Finalize CausalHeadRank Feasibility PoC

## Overview

The PoC code is already implemented (`src/keystone/` package, 11 modules). Previous runs produced GO verdicts. This plan covers: fixing one known Windows file-locking bug in checkpoint writes, running the 6 test files to confirm correctness, executing a fresh smoke test, and verifying all LFG acceptance criteria are met.

---

## Problem Frame

The CausalHeadRank PoC (feasibility gate for the Keystone Neurons research project) is implemented but needs a final validation pass. One known issue exists: checkpoint writes hit `PermissionError` on Windows due to `Path.replace()` failing when the target file handle is still held. All else is ready for verification.

---

## Requirements Trace

- R1. Fix Windows file-locking crash in `_write_checkpoint()` (observed in `experiments/smoke_v2/failure_report.md`)
- R2. All 6 test files in `tests/` pass
- R3. Fresh `run_poc.py` smoke test executes end-to-end producing all artifacts
- R4. `head_scores.csv`, `results.json`, runtime stats, memory stats, stability metrics produced
- R5. PASS/FAIL table for all feasibility gates printed
- R6. Failure report generated if any gate fails

---

## Scope Boundaries

- Fix known checkpoint write bug on Windows
- Verify tests pass
- Run smoke test and confirm gate outputs
- Structured pruning, baselines (SparseViT, DepGraph), anomaly detection, paper writing — all out of scope (deferred to full project milestones)

---

## Context & Research

### Relevant Code and Patterns

- `src/keystone/scoring.py:148-163` — `_write_checkpoint()` uses `Path.replace()` which fails on Windows when target file handle is still open
- `src/keystone/utils.py` — `set_seed()`, `log_memory()`, `write_failure_report()` utilities
- `scripts/run_poc.py` — orchestrator with `--skip-*` flags, 6-gate verdict table
- `tests/` — 6 test files covering data, patching, probe, scoring, vit_adapters, analysis

### Institutional Learnings

- `docs/keystone-ideation/continuation-checkpoint.md` — notes 6.44GB VRAM (not 12GB), narrower novelty boundary, single-head scoring misses group effects
- Previous `causal_headrank_poc_v2` run: all gates GO (probe 0.807, tau 0.849, 198s runtime, 0.61GB memory)

---

## Key Technical Decisions

- **Checkpoint fix:** Replace `Path.replace()` with an `os.replace()`-based or retry-based approach safe on Windows where concurrent file handles block rename
- **Smoke test scope:** Run a minimal full sweep (25 images, 10 heads) via `run_poc.py --n-images 25 --n-heads 10 --seed 42` to verify end-to-end quickly

---

## Implementation Units

- U1. **Fix Windows file-locking in checkpoint writes**

**Goal:** Prevent `PermissionError: [WinError 32]` when checkpoint `.tmp` file replaces existing file on Windows.

**Requirements:** R1

**Dependencies:** None

**Files:**
- Modify: `src/keystone/scoring.py`

**Approach:**
- In `_write_checkpoint()`, replace `temporary_path.replace(checkpoint_path)` / `temporary_metadata.replace(metadata_path)` with `os.replace()` wrapped in a retry loop (3 attempts, 0.1s delay) to handle transient Windows file handle conflicts
- `os.replace()` is atomic on Windows and handles cross-device rename; retry handles the case where antivirus/scanner briefly holds the target

**Patterns to follow:**
- Existing `Path.write_text()` / `Path.read_text()` usage in same file

**Test scenarios:**
- Happy path: write checkpoint with 10 records, verify CSV + meta.json exist and match
- Edge case: overwrite existing checkpoint, verify contents replaced without error
- Error path: simulated file handle conflict resolves with retry

**Verification:**
- No `PermissionError` on Windows when overwriting checkpoints

- U2. **Verify all tests pass and fix failures**

**Goal:** All 6 test files in `tests/` pass clean.

**Requirements:** R2

**Dependencies:** U1

**Files:**
- Test: `tests/test_analysis.py`, `tests/test_data.py`, `tests/test_patching.py`, `tests/test_probe.py`, `tests/test_scoring_checkpoint.py`, `tests/test_vit_adapters.py`

**Approach:**
- Run `pytest tests/ -v` and fix any failures
- Common issues: CPU-only machines, missing dependencies, stale test fixtures

**Test expectation:** Tests themselves are the verification surface — no new tests needed.

**Verification:**
- `pytest tests/` exits 0 with all green

- U3. **Run smoke test producing all artifacts**

**Goal:** Execute `run_poc.py` end-to-end and produce `head_scores.csv`, `results.json`, runtime/memory stats, stability metrics, PASS/FAIL table.

**Requirements:** R3, R4, R5

**Dependencies:** U1, U2

**Files:**
- Execute: `scripts/run_poc.py`

**Approach:**
- Run with minimal image count for speed: `--n-images 25 --n-heads 10 --seed 42`
- Script auto-adapts batch size and gates incrementally (1→10→144 heads, probe accuracy, stability)
- Verify `head_scores.csv`, `results.json`, `environment.json` written to output dir
- Verify PASS/FAIL table printed with all gate results

**Test expectation:** none — verification is the run output

**Verification:**
- Script exits 0
- Output directory contains `head_scores.csv`, `results.json`, `environment.json`
- Verdict is GO or a clearly-documented failed gate with failure report

- U4. **Confirm all LFG acceptance criteria**

**Goal:** Cross-check final state against every LFG acceptance criterion.

**Requirements:** R5, R6

**Dependencies:** U3

**Approach:**
- Review output artifacts from U3
- Confirm: all tests pass, PoC executes end-to-end, produces head_scores.csv + results.json + runtime/memory stats + stability metrics, reports PASS/FAIL per gate, generates failure report on any gate failure

**Test expectation:** none — manual checklist verification

**Verification:**
- All LFG acceptance criteria checked and confirmed

---

## System-Wide Impact

- **Interaction graph:** `scoring.py` → `patching.py` → `vit_adapters.py` → `models.py`. Checkpoint fix is isolated to `scoring.py:148-163`.
- **Unchanged invariants:** All other modules, scripts, and tests are unchanged. Checkpoint format (CSV + meta.json) preserved.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Windows retry may not cover all file lock scenarios | If retry fails, fall back to unique filenames (timestamp suffix) instead of overwrite |
| Smoke test may OOM on 6GB VRAM | `--batch-size 1` flag already exists; script auto-adapts |
| Test failures from stale fixtures | Fix fixtures rather than tests; tests reflect current code expectations |

---

## Sources & References

- **Origin document:** [docs/brainstorms/keystone-neurons-requirements.md](../brainstorms/keystone-neurons-requirements.md)
- Related code: `src/keystone/scoring.py:148-163`
- Related issues: `experiments/smoke_v2/failure_report.md`
