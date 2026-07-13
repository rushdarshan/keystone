import pandas as pd
import pytest

from src.keystone.analysis import compare_rankings, determine_verdict, top_k_overlap


def test_top_k_overlap_compares_highest_scoring_heads():
    first = pd.DataFrame({"head_idx": [0, 1, 2, 3], "causal_score": [4.0, 3.0, 2.0, 1.0]})
    second = pd.DataFrame({"head_idx": [0, 1, 2, 3], "causal_score": [1.0, 3.0, 4.0, 2.0]})

    assert top_k_overlap(first, second, k=2) == 0.5


def test_top_k_overlap_rejects_non_positive_k():
    frame = pd.DataFrame({"head_idx": [0], "causal_score": [1.0]})

    with pytest.raises(ValueError, match="positive"):
        top_k_overlap(frame, frame, k=0)


def test_research_verdict_is_partial_when_a_required_gate_is_skipped():
    results = {
        "Q1": True,
        "Q0_probe": True,
        "Q2": True,
        "Q3": None,
        "Q4": True,
        "Q5": True,
    }

    assert determine_verdict(results, research_mode=True) == "PARTIAL"


def test_research_verdict_requires_every_gate_to_pass():
    results = {name: True for name in ["Q1", "Q0_probe", "Q2", "Q3", "Q4", "Q5"]}

    assert determine_verdict(results, research_mode=True) == "GO"
    results["Q3"] = False
    assert determine_verdict(results, research_mode=True) == "NO-GO"


def test_compare_rankings_returns_all_correlation_metrics():
    """compare_rankings produces tau and rho for all three pairs."""
    n = 10
    causal = pd.DataFrame({
        "head_idx": range(n),
        "layer": [0] * n,
        "head_in_layer": range(n),
        "causal_score": list(range(n, 0, -1)),
    })
    magnitude = pd.DataFrame({
        "head_idx": range(n),
        "layer": [0] * n,
        "head_in_layer": range(n),
        "score": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    })
    gradient = pd.DataFrame({
        "head_idx": range(n),
        "layer": [0] * n,
        "head_in_layer": range(n),
        "score": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    })

    result = compare_rankings(causal, magnitude, gradient)

    assert "tau_causal_magnitude" in result
    assert "tau_causal_gradient" in result
    assert "tau_magnitude_gradient" in result
    assert "rho_causal_magnitude" in result
    assert "rho_causal_gradient" in result
    assert "rho_magnitude_gradient" in result
    assert "keystone_candidates" in result
    assert "n_keystone" in result
    assert "keystone_pct" in result
    assert "total_heads" in result
    assert result["total_heads"] == n


def test_keystone_candidates_identified():
    """Heads with high causal but low magnitude are flagged as keystone."""
    # causal: heads 0-3 high (9,8,7,6), heads 4-7 low (2,2,2,2)
    # magnitude: reverse (low for heads 0-3, high for heads 4-7)
    causal = pd.DataFrame({
        "head_idx": [0, 1, 2, 3, 4, 5, 6, 7],
        "layer": [0] * 8,
        "head_in_layer": [0, 1, 2, 3, 4, 5, 6, 7],
        "causal_score": [9.0, 8.0, 7.0, 6.0, 2.0, 2.0, 2.0, 2.0],
    })
    magnitude = pd.DataFrame({
        "head_idx": [0, 1, 2, 3, 4, 5, 6, 7],
        "layer": [0] * 8,
        "head_in_layer": [0, 1, 2, 3, 4, 5, 6, 7],
        "score": [1.0, 2.0, 3.0, 4.0, 10.0, 10.0, 10.0, 10.0],
    })
    gradient = pd.DataFrame({
        "head_idx": [0, 1, 2, 3, 4, 5, 6, 7],
        "layer": [0] * 8,
        "head_in_layer": [0, 1, 2, 3, 4, 5, 6, 7],
        "score": [0.0] * 8,
    })

    result = compare_rankings(causal, magnitude, gradient)

    # 75th percentile of causal is 7.25; heads 0,1 are above (9, 8)
    # 50th percentile of magnitude is 3.5; heads 0,1 are below (1, 2)
    assert set(result["keystone_candidates"]) == {0, 1}
    assert result["n_keystone"] == 2


def test_perfect_correlation_returns_tau_one():
    """Identical rankings produce tau = 1.0."""
    causal = pd.DataFrame({
        "head_idx": [0, 1, 2, 3],
        "layer": [0] * 4,
        "head_in_layer": [0, 1, 2, 3],
        "causal_score": [4.0, 3.0, 2.0, 1.0],
    })
    magnitude = pd.DataFrame({
        "head_idx": [0, 1, 2, 3],
        "layer": [0] * 4,
        "head_in_layer": [0, 1, 2, 3],
        "score": [4.0, 3.0, 2.0, 1.0],
    })
    gradient = pd.DataFrame({
        "head_idx": [0, 1, 2, 3],
        "layer": [0] * 4,
        "head_in_layer": [0, 1, 2, 3],
        "score": [4.0, 3.0, 2.0, 1.0],
    })

    result = compare_rankings(causal, magnitude, gradient)

    assert result["tau_causal_magnitude"] == 1.0
    assert result["rho_causal_magnitude"] == 1.0
