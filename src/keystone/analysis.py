import pandas as pd
from scipy.stats import kendalltau, spearmanr
from scipy import stats
import numpy as np


RESEARCH_GATES = ("Q1", "Q0_probe", "Q2", "Q3", "Q4", "Q5")


def determine_verdict(results: dict[str, bool | None], *, research_mode: bool) -> str:
    if any(value is False for value in results.values()):
        return "NO-GO"
    if not research_mode:
        return "WIRING-ONLY"
    if all(results.get(gate) is True for gate in RESEARCH_GATES):
        return "GO"
    return "PARTIAL"


def kendall_tau(rank_a: pd.DataFrame, rank_b: pd.DataFrame) -> float:
    merged = rank_a.merge(rank_b, on="head_idx", suffixes=("_a", "_b"))
    tau, _ = kendalltau(merged["causal_score_a"], merged["causal_score_b"])
    return 0.0 if np.isnan(tau) else float(tau)


def top_k_overlap(rank_a: pd.DataFrame, rank_b: pd.DataFrame, k: int = 20) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    available = min(k, len(rank_a), len(rank_b))
    if available == 0:
        return 0.0
    top_a = set(rank_a.nlargest(available, "causal_score")["head_idx"])
    top_b = set(rank_b.nlargest(available, "causal_score")["head_idx"])
    return len(top_a & top_b) / available


def estimate_total_runtime(scored: pd.DataFrame, total_heads: int = 144, warmup: int = 5) -> dict:
    usable = scored[scored["head_idx"] >= warmup]
    if len(usable) < 2:
        mean_time = float(scored["time_seconds"].mean())
        total = mean_time * total_heads
        return {"estimate_seconds": total, "low_seconds": total, "high_seconds": total, "method": "mean"}

    x = usable["head_idx"].to_numpy(dtype=float)
    y = usable["time_seconds"].to_numpy(dtype=float)
    slope, intercept, _, _, _ = stats.linregress(x, y)
    all_x = np.arange(warmup, total_heads, dtype=float)
    pred = intercept + slope * all_x
    estimate = float(np.maximum(pred, 0).sum() + scored[scored["head_idx"] < warmup]["time_seconds"].sum())

    residuals = y - (intercept + slope * x)
    stderr = float(residuals.std(ddof=1) if len(residuals) > 1 else 0.0)
    margin = 1.96 * stderr * (total_heads ** 0.5)
    return {
        "estimate_seconds": estimate,
        "low_seconds": max(0.0, estimate - margin),
        "high_seconds": estimate + margin,
        "method": "linear",
    }


def compare_rankings(
    causal_df: pd.DataFrame,
    magnitude_df: pd.DataFrame,
    gradient_df: pd.DataFrame,
) -> dict:
    """Compute pairwise Kendall tau and Spearman rho between rankings.

    Args:
        causal_df: From score_all_heads(), columns [head_idx, layer, head_in_layer, causal_score]
        magnitude_df: From score_magnitude(), columns [head_idx, layer, head_in_layer, score]
        gradient_df: From score_gradient(), columns [head_idx, layer, head_in_layer, score]

    Returns:
        Dict with keys:
            tau_causal_magnitude, tau_causal_gradient, tau_magnitude_gradient
            rho_causal_magnitude, rho_causal_gradient, rho_magnitude_gradient
            keystone_candidates: list of head_idx where causal score > 75th percentile
                                 AND magnitude score < 50th percentile
    """
    merged = causal_df[["head_idx", "causal_score"]].merge(
        magnitude_df[["head_idx", "score"]].rename(columns={"score": "magnitude_score"}),
        on="head_idx",
    ).merge(
        gradient_df[["head_idx", "score"]].rename(columns={"score": "gradient_score"}),
        on="head_idx",
    )

    causal = merged["causal_score"].values
    magnitude = merged["magnitude_score"].values
    gradient = merged["gradient_score"].values

    tau_cm, _ = kendalltau(causal, magnitude)
    tau_cg, _ = kendalltau(causal, gradient)
    tau_mg, _ = kendalltau(magnitude, gradient)

    rho_cm, _ = spearmanr(causal, magnitude)
    rho_cg, _ = spearmanr(causal, gradient)
    rho_mg, _ = spearmanr(magnitude, gradient)

    causal_p75 = np.percentile(causal, 75)
    magnitude_p50 = np.percentile(magnitude, 50)
    keystone_mask = (causal > causal_p75) & (magnitude < magnitude_p50)
    keystone_indices = merged.loc[keystone_mask, "head_idx"].tolist()

    return {
        "tau_causal_magnitude": round(float(tau_cm), 4),
        "tau_causal_gradient": round(float(tau_cg), 4),
        "tau_magnitude_gradient": round(float(tau_mg), 4),
        "rho_causal_magnitude": round(float(rho_cm), 4),
        "rho_causal_gradient": round(float(rho_cg), 4),
        "rho_magnitude_gradient": round(float(rho_mg), 4),
        "keystone_candidates": keystone_indices,
        "n_keystone": len(keystone_indices),
        "keystone_pct": round(len(keystone_indices) / len(merged) * 100, 1),
        "total_heads": len(merged),
    }
