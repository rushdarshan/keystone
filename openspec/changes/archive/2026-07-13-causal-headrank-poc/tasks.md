## 1. Project Scaffolding

- [x] 1.1 Create `src/keystone/__init__.py` with package docstring
- [x] 1.2 Install deps (nnsight, timm, torchvision, scipy, pandas)
- [x] 1.3 Create `scripts/run_poc.py` entry point
- [x] 1.4 Verify first script run succeeds (imports + CLI help)

## 2. Core Modules

- [x] 2.1 Implement `src/keystone/config.py`: dataclass with seed, device, batch_size, n_images, corruption_strategy, metric, output_dir
- [x] 2.2 Implement `src/keystone/utils.py`: set_seed(), log_memory(), format_time(), Timer context manager

## 3. Model Loading and Head Discovery

- [x] 3.1 Implement `src/keystone/models.py`: DINOv3 loader via timm with DINOv2 fallback
- [x] 3.2 Implement `src/keystone/vit_adapters.py`: discover all 144 head hook points, print hook table
- [x] 3.3 Verify head discovery works (fix DINOv3 model name, timm attention interface)

## 4. Patching and Scoring

- [x] 4.1 Implement `src/keystone/patching.py`: activation patching with clean-logit cache
- [x] 4.2 Implement `src/keystone/scoring.py`: incremental scoring (1→10→144) with checkpointing every 10 heads
- [x] 4.3 Implement cross-class corruption pairing for CIFAR-100

## 5. Analysis and Reporting

- [x] 5.1 Implement `src/keystone/analysis.py`: kendall_tau() between two rankings
- [x] 5.2 Fix runtime estimation: linear model with warmup (skip first 5), 95% CI
- [x] 5.3 Add failure_report.md generation on Q1 fail
- [x] 5.4 Add environment.json logging

## 6. Orchestration and Verification

- [x] 6.1 Wire incremental gates (1 head → 10 heads → 144 heads) into run_poc.py
- [x] 6.2 Print pass/fail table with binary PASS/FAIL results
- [x] 6.3 Run full PoC end-to-end and verify all questions pass
  - Full run with pretrained DINOv3, CIFAR-100, 50 images, 144 heads: Q1-Q5 all PASS. Verdict: GO.
