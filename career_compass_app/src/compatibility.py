"""Steps 4-5: per-component compatibility scores, and the interpretable weighted
compatibility model that combines them.

Each component score is bounded to [0, 1] so the weighted combination in
`compute_weighted_compatibility` is directly interpretable ("this occupation scored
0.82 on skills, 0.40 on education") regardless of the weights chosen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .config import RIASEC_COLUMNS, SKILL_COLUMNS
from .feature_matrix import FeatureMatrices
from .scaling import (
    ScaledMatrices, INTEREST_BOUNDS, SKILL_BOUNDS, EDUCATION_BOUNDS, JOB_ZONE_BOUNDS,
    fixed_minmax_scale, rescale_range,
)
from .user_profile import UserProfile, SKILL_LABEL_TO_COLUMN

# Questionnaire's interest slider is 1-5; O*NET's native interest scale is 1-7.
QUESTIONNAIRE_INTEREST_BOUNDS = (1.0, 5.0)

DEFAULT_WEIGHTS = {
    "interest": 0.30,
    "skill": 0.30,
    "education": 0.15,
    "job_zone": 0.10,
    "labor_market": 0.15,
}


def normalize_weights(weights: dict[str, float] | None) -> dict[str, float]:
    weights = dict(weights) if weights else dict(DEFAULT_WEIGHTS)
    missing = set(DEFAULT_WEIGHTS) - set(weights)
    if missing:
        raise ValueError(f"Missing weight(s) for component(s): {sorted(missing)}")
    if any(w < 0 for w in weights.values()):
        raise ValueError("Weights cannot be negative.")
    total = sum(weights.values())
    if total == 0:
        raise ValueError("At least one weight must be positive.")
    return {k: v / total for k, v in weights.items()}


def _user_interest_vector(profile: UserProfile) -> np.ndarray:
    raw = [
        profile.interest_realistic, profile.interest_investigative, profile.interest_artistic,
        profile.interest_social, profile.interest_enterprising, profile.interest_conventional,
    ]
    rescaled = [rescale_range(v, QUESTIONNAIRE_INTEREST_BOUNDS, INTEREST_BOUNDS) for v in raw]
    return fixed_minmax_scale(np.array(rescaled), INTEREST_BOUNDS)


def _user_skill_vector(profile: UserProfile) -> pd.Series:
    raw = pd.Series(1.0, index=SKILL_COLUMNS)
    for label in profile.selected_skills:
        raw[SKILL_LABEL_TO_COLUMN[label]] = 5.0
    return fixed_minmax_scale(raw, SKILL_BOUNDS)


def interest_score(profile: UserProfile, scaled: ScaledMatrices) -> pd.Series:
    user_vec = _user_interest_vector(profile).reshape(1, -1)
    sims = cosine_similarity(user_vec, scaled.interest[RIASEC_COLUMNS].to_numpy())
    return pd.Series(sims.ravel(), index=scaled.interest.index, name="interest_score")


def skill_score(profile: UserProfile, scaled: ScaledMatrices) -> pd.Series:
    user_vec = _user_skill_vector(profile).to_numpy().reshape(1, -1)
    sims = cosine_similarity(user_vec, scaled.skill[SKILL_COLUMNS].to_numpy())
    return pd.Series(sims.ravel(), index=scaled.skill.index, name="skill_score")


def _asymmetric_preparation_score(user_level: float, occupation_level: pd.Series, scale_bounds: tuple[float, float]) -> pd.Series:
    """Full credit when the occupation needs at most as much preparation as the user
    is willing to do; score decays linearly as the requirement exceeds that ceiling.
    An occupation requiring LESS preparation than the user's ceiling is never
    penalized -- being over-qualified is not treated as a mismatch.
    """
    _, scale_max = scale_bounds
    gap = (occupation_level - user_level).clip(lower=0)
    max_gap = max(scale_max - user_level, 1e-9)
    return (1 - gap / max_gap).clip(lower=0.0, upper=1.0)


def education_score(profile: UserProfile, scaled: ScaledMatrices) -> pd.Series:
    user_bucket = float(profile.education_preference)
    occupation_scaled = scaled.education
    user_scaled = fixed_minmax_scale(user_bucket, EDUCATION_BOUNDS)
    return _asymmetric_preparation_score(user_scaled, occupation_scaled, (0.0, 1.0)).rename("education_score")


def job_zone_score(profile: UserProfile, scaled: ScaledMatrices) -> pd.Series:
    user_zone = float(profile.job_zone_preference)
    occupation_scaled = scaled.job_zone
    user_scaled = fixed_minmax_scale(user_zone, JOB_ZONE_BOUNDS)
    return _asymmetric_preparation_score(user_scaled, occupation_scaled, (0.0, 1.0)).rename("job_zone_score")


def labor_market_score(profile: UserProfile, scaled: ScaledMatrices) -> pd.Series:
    total = profile.salary_importance + profile.employment_importance
    if total == 0:
        salary_weight = employment_weight = 0.5
    else:
        salary_weight = profile.salary_importance / total
        employment_weight = profile.employment_importance / total
    score = (
        salary_weight * scaled.labor_market["median_wage_percentile"]
        + employment_weight * scaled.labor_market["employment_percentile"]
    )
    return score.rename("labor_market_score")


def compute_component_scores(profile: UserProfile, scaled: ScaledMatrices) -> pd.DataFrame:
    profile.validate()
    return pd.concat(
        [
            interest_score(profile, scaled),
            skill_score(profile, scaled),
            education_score(profile, scaled),
            job_zone_score(profile, scaled),
            labor_market_score(profile, scaled),
        ],
        axis=1,
    )


def compute_weighted_compatibility(
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profile: UserProfile,
    weights: dict[str, float] | None = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """The interpretable weighted compatibility model (steps 4-5 combined).

    Returns one row per recommended occupation with the overall score AND every
    component score, so the ranking is fully explainable without recomputation.
    """
    w = normalize_weights(weights)
    components = compute_component_scores(profile, scaled)
    overall = (
        w["interest"] * components["interest_score"]
        + w["skill"] * components["skill_score"]
        + w["education"] * components["education_score"]
        + w["job_zone"] * components["job_zone_score"]
        + w["labor_market"] * components["labor_market_score"]
    )
    result = matrices.lookup.join(components)
    result["overall_score"] = overall
    result["profile_name"] = profile.profile_name
    for name, value in w.items():
        result[f"weight_{name}"] = value

    result = result.sort_values("overall_score", ascending=False).head(top_n).copy()
    result.insert(1, "rank", np.arange(1, len(result) + 1))
    result["model"] = "weighted"
    return result.reset_index(drop=True)