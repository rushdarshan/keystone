# Keystone Improvement Plans

**Generated:** 2026-07-13 | **Planned at commit:** `a377c37`

## Execution Order

| # | Plan | Status | Priority | Effort | Depends on |
|---|------|--------|----------|--------|------------|
| 001 | [Update README with benchmark results and paper link](001-update-readme-results.md) | pending | P1 | S | none |

## Dependency Graph

```
001 (README update) — no dependencies
```

## Considered and Rejected

- **Add pyproject.toml** — deferred. Requires pinning exact versions against tested environment. Low urgency for a research repo.
- **Fix _find_corrupt_idx same-class fallback** — accepted but not planned. Only affects edge case where batch is too small. Mitigated by using batch_size >= 4.
- **Monkey-patch version guard** — accepted but not planned. Would require timm version detection. EVA attention is stable in timm 1.0.x.
- **Checkpoint atomicity** — accepted but not planned. Crash window is milliseconds between two atomic replaces. Low probability.
