from __future__ import annotations
from typing import Iterable
import numpy as np
import pandas as pd
from .config import DISPLAY_COLUMNS
from .user_profile import UserProfile


def _normalized_weights(salary_importance: float, employment_importance: float) -> tuple[float, float]:
    if salary_importance < 0 or employment_importance < 0:
        raise ValueError("Importance values cannot be negative.")
    total = salary_importance + employment_importance
    if total == 0:
        return 0.5, 0.5
    return salary_importance / total, employment_importance / total


def prepare_baseline_data(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only occupations with known wage and employment percentiles.

    Missing BLS values are excluded rather than filled with zero because zero
    would incorrectly imply a known low wage or employment level.
    """
    required = ["median_wage_percentile", "employment_percentile"]
    clean = df.dropna(subset=required).copy()
    clean = clean.drop_duplicates(subset=["onet_soc_code"], keep="first")
    return clean


def recommend_baseline(
    df: pd.DataFrame,
    profile: UserProfile,
    top_n: int = 10,
) -> pd.DataFrame:
    """Rank occupations using wage and employment opportunity only.

    The precomputed labor_market_opportunity_score is retained for reporting,
    but not added to the formula because it is already derived from wage and
    employment percentiles. Adding it would double-count the same information.
    """
    profile.validate()
    if top_n <= 0:
        raise ValueError("top_n must be a positive integer.")

    result = prepare_baseline_data(df)
    salary_weight, employment_weight = _normalized_weights(
        profile.salary_importance, profile.employment_importance
    )
    result["baseline_score"] = (
        salary_weight * result["median_wage_percentile"]
        + employment_weight * result["employment_percentile"]
    )
    result["profile_name"] = profile.profile_name
    result = result.sort_values(
        ["baseline_score", "labor_market_opportunity_score", "occupation_title"],
        ascending=[False, False, True]
    ).head(top_n).copy()
    result.insert(1, "rank", np.arange(1, len(result) + 1))
    result["salary_weight"] = salary_weight
    result["employment_weight"] = employment_weight

    output_columns = [
        "profile_name", "rank", "onet_soc_code", "soc_code", "occupation_title",
        "baseline_score", "salary_weight", "employment_weight", "a_median",
        "tot_emp", "median_wage_percentile", "employment_percentile",
        "labor_market_opportunity_score"
    ]
    return result[output_columns]


def recommend_for_profiles(
    df: pd.DataFrame,
    profiles: Iterable[UserProfile],
    top_n: int = 10,
) -> pd.DataFrame:
    frames = [recommend_baseline(df, profile, top_n=top_n) for profile in profiles]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
