from dataclasses import dataclass
from typing import Literal


@dataclass
class PocConfig:
    seed: int = 42
    device: str = "cuda"
    batch_size: int = 4
    n_images: int = 100
    corruption_strategy: Literal["cross_class"] = "cross_class"
    metric: Literal["logit_diff", "kl_div", "feature_diff"] = "logit_diff"
    model_name: str = "vit_base_patch16_dinov3"
    fallback_model: str = "vit_base_patch14_dinov2"
    pretrained: bool = True
    output_dir: str = "experiments/causal_headrank_poc"
    num_workers: int = 2
    checkpoint_every: int = 10
    sample_composition_seed: int = 0
    probe_train_images: int = 5000
    probe_val_images: int = 1000
    probe_batch_size: int = 32
    probe_epochs: int = 100
    probe_learning_rate: float = 0.05
    probe_weight_decay: float = 1e-4
    probe_min_accuracy: float = 0.10
    stability_repeats: int = 3
    stability_top_k: int = 20
    pruning_ratios: tuple[float, ...] = (0.25, 0.50, 0.75, 0.90)
    pruning_seeds: tuple[int, ...] = (42, 43, 44)
    n_eval_images: int = 500
