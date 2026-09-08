"""Shared combined-vector builder used by both the cosine-similarity and KNN
recommenders (steps 6-7), so the two models operate on the exact same feature
space and are comparable.

Two corrections are applied that a naive concatenation would miss:

1. Blocks have very different widths (30 skills vs. 1 job-zone column). Each column is scaled before combining, so a
   block's total contribution tracks its assigned weight instead of its column count.
2. Higher pay and higher employment are always
   better, so the user's target for both columns is fixed at 1.0 which is the top of the
   percentile scale
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .compatibility import normalize_weights, _user_interest_vector, _user_skill_vector
from .config import RIASEC_COLUMNS, SKILL_COLUMNS
from .feature_matrix import FeatureMatrices
from .scaling import ScaledMatrices, EDUCATION_BOUNDS, JOB_ZONE_BOUNDS, fixed_minmax_scale
from .user_profile import UserProfile

EDUCATION_COMBINED_COLUMN = "_education_scaled"
JOB_ZONE_COMBINED_COLUMN = "_job_zone_scaled"
WAGE_COLUMN = "median_wage_percentile"
EMPLOYMENT_COLUMN = "employment_percentile"
LABOR_MARKET_COMBINED_COLUMNS = [WAGE_COLUMN, EMPLOYMENT_COLUMN]

BLOCK_COLUMNS = {
    "interest": RIASEC_COLUMNS,
    "skill": SKILL_COLUMNS,
    "education": [EDUCATION_COMBINED_COLUMN],
    "job_zone": [JOB_ZONE_COMBINED_COLUMN],
    "labor_market": LABOR_MARKET_COMBINED_COLUMNS,
}


def _block_multiplier(block: str, weights: dict[str, float]) -> float:
    n_columns = len(BLOCK_COLUMNS[block])
    return math.sqrt(weights[block] / n_columns)


def _labor_market_sub_weights(profile: UserProfile) -> tuple[float, float]:
    total = profile.salary_importance + profile.employment_importance
    if total == 0:
        return 0.5, 0.5
    return profile.salary_importance / total, profile.employment_importance / total


def build_occupation_matrix(
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profile: UserProfile,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    w = normalize_weights(weights)
    salary_weight, employment_weight = _labor_market_sub_weights(profile)
    labor_multiplier = _block_multiplier("labor_market", w)

    frame = pd.concat(
        [
            scaled.interest[RIASEC_COLUMNS] * _block_multiplier("interest", w),
            scaled.skill[SKILL_COLUMNS] * _block_multiplier("skill", w),
            (scaled.education.rename(EDUCATION_COMBINED_COLUMN) * _block_multiplier("education", w)),
            (scaled.job_zone.rename(JOB_ZONE_COMBINED_COLUMN) * _block_multiplier("job_zone", w)),
            (scaled.labor_market[WAGE_COLUMN] * math.sqrt(salary_weight) * labor_multiplier),
            (scaled.labor_market[EMPLOYMENT_COLUMN] * math.sqrt(employment_weight) * labor_multiplier),
        ],
        axis=1,
    )
    return frame


def build_user_vector(profile: UserProfile, weights: dict[str, float] | None = None) -> np.ndarray:
    w = normalize_weights(weights)
    profile.validate()

    interest_part = _user_interest_vector(profile) * _block_multiplier("interest", w)
    skill_part = _user_skill_vector(profile).to_numpy() * _block_multiplier("skill", w)

    education_scaled = fixed_minmax_scale(float(profile.education_preference), EDUCATION_BOUNDS)
    education_part = np.array([education_scaled]) * _block_multiplier("education", w)

    job_zone_scaled = fixed_minmax_scale(float(profile.job_zone_preference), JOB_ZONE_BOUNDS)
    job_zone_part = np.array([job_zone_scaled]) * _block_multiplier("job_zone", w)

    salary_weight, employment_weight = _labor_market_sub_weights(profile)
    labor_multiplier = _block_multiplier("labor_market", w)
    # Target = 1.0: to maximize wage/employment percentile
  
    labor_market_part = np.array([
        1.0 * math.sqrt(salary_weight) * labor_multiplier,
        1.0 * math.sqrt(employment_weight) * labor_multiplier,
    ])

    return np.concatenate([interest_part, skill_part, education_part, job_zone_part, labor_market_part])