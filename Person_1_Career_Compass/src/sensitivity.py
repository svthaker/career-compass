"""Step 8: test different feature weights and values of K.

There is no labeled ground truth for this recommender so we test its sensitivity to different feature weights and K values rather than its accuracy.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from .compatibility import compute_weighted_compatibility, DEFAULT_WEIGHTS
from .feature_matrix import FeatureMatrices
from .knn_model import recommend_knn
from .scaling import ScaledMatrices
from .user_profile import UserProfile

# A handful of named weight configurations spanning "emphasize one component
# heavily" to the balanced default, to see how much the top-N actually moves.
WEIGHT_CONFIGURATIONS = {
    "balanced_default": DEFAULT_WEIGHTS,
    "interest_heavy": {"interest": 0.55, "skill": 0.20, "education": 0.10, "job_zone": 0.05, "labor_market": 0.10},
    "skill_heavy": {"interest": 0.15, "skill": 0.55, "education": 0.10, "job_zone": 0.05, "labor_market": 0.15},
    "labor_market_heavy": {"interest": 0.15, "skill": 0.15, "education": 0.10, "job_zone": 0.05, "labor_market": 0.55},
    "education_and_job_zone_heavy": {"interest": 0.15, "skill": 0.15, "education": 0.30, "job_zone": 0.30, "labor_market": 0.10},
}

K_VALUES = [5, 10, 20, 50]


def test_weight_configurations(
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profiles: Iterable[UserProfile],
    weight_configs: dict[str, dict[str, float]] | None = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """Run the weighted compatibility model under each named weight configuration,
    for every profile, and return a long comparison table."""
    weight_configs = weight_configs or WEIGHT_CONFIGURATIONS
    frames = []
    for config_name, weights in weight_configs.items():
        for profile in profiles:
            result = compute_weighted_compatibility(matrices, scaled, profile, weights=weights, top_n=top_n)
            result.insert(0, "weight_config", config_name)
            frames.append(result)
    return pd.concat(frames, ignore_index=True)


def _top_set(df: pd.DataFrame, n: int) -> set:
    return set(df.sort_values("rank").head(n)["onet_soc_code"])


def test_k_values(
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profiles: Iterable[UserProfile],
    k_values: Iterable[int] | None = None,
    weights: dict[str, float] | None = None,
    stability_top_n: int = 5,
) -> pd.DataFrame:
    """Run the KNN recommender at each K, for every profile, and measure how
    stable the top-N neighbor set is between successive K values (Jaccard overlap).
    """
    k_values = sorted(k_values or K_VALUES)
    rows = []
    previous_top_set: dict[str, set] = {}

    for profile in profiles:
        for k in k_values:
            result = recommend_knn(matrices, scaled, profile, weights=weights, k=k)
            top_set = _top_set(result, stability_top_n)

            prev = previous_top_set.get(profile.profile_name)
            if prev is None:
                jaccard = None
            else:
                jaccard = len(top_set & prev) / len(top_set | prev) if (top_set | prev) else 1.0
            previous_top_set[profile.profile_name] = top_set

            rows.append({
                "profile_name": profile.profile_name,
                "k": k,
                f"top_{stability_top_n}_titles": ", ".join(
                    result.sort_values("rank").head(stability_top_n)["occupation_title"]
                ),
                "jaccard_overlap_vs_previous_k": jaccard,
            })
    return pd.DataFrame(rows)