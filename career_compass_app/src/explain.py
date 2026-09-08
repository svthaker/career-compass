"""Step 9: recommendation explanations.

"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .compatibility import _user_interest_vector, _user_skill_vector
from .config import RIASEC_COLUMNS, SKILL_COLUMNS
from .feature_matrix import FeatureMatrices
from .scaling import ScaledMatrices
from .user_profile import UserProfile

COMPONENT_LABELS = {
    "interest_score": "Interests",
    "skill_score": "Skills",
    "education_score": "Education fit",
    "job_zone_score": "Preparation-level fit",
    "labor_market_score": "Labor-market opportunity",
}


_COMPONENT_TO_WEIGHT_KEY = {
    "interest_score": "weight_interest",
    "skill_score": "weight_skill",
    "education_score": "weight_education",
    "job_zone_score": "weight_job_zone",
    "labor_market_score": "weight_labor_market",
}

def _friendly_skill_name(column: str) -> str:
    return (
        column.replace("essential_skill_", "")
        .replace("transferable_skill_", "")
        .replace("_im", "")
        .replace("_", " ")
        .capitalize()
    )


def _friendly_interest_name(column: str) -> str:
    return column.replace("interest_", "").capitalize()


def _top_contributing_dimension(
    profile: UserProfile, scaled: ScaledMatrices, onet_soc_code: str, columns: list[str], block: str
) -> str:
    """Identify which single skill/interest dimension contributed most to the match
    for one occupation, via elementwise product of the (scaled) user and
    occupation vectors -- the same quantity cosine similarity sums over."""
    if block == "interest":
        user_vec = _user_interest_vector(profile)
        occ_vec = scaled.interest.loc[onet_soc_code, columns].to_numpy()
        friendly = _friendly_interest_name
    else:
        user_vec = _user_skill_vector(profile).to_numpy()
        occ_vec = scaled.skill.loc[onet_soc_code, columns].to_numpy()
        friendly = _friendly_skill_name

    contributions = user_vec * occ_vec
    best_idx = int(np.argmax(contributions))
    return friendly(columns[best_idx])


def explain_recommendations(
    results: pd.DataFrame,
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profile: UserProfile,
    top_components: int = 2,
) -> pd.DataFrame:
    """Attach a plain-language `why` column to any model's top-N result table.

    The returned DataFrame has the same rows as `results` but with an additional `why` column
    """
    explained = results.copy()
    reasons = []

    for _, row in explained.iterrows():
        code = row["onet_soc_code"]
        component_values = {name: row[name] for name in COMPONENT_LABELS if name in row}
        contributions = {
            name: score * row[_COMPONENT_TO_WEIGHT_KEY[name]]
            for name, score in component_values.items()
        }
        ranked_components = sorted(component_values.items(), key=lambda kv: contributions[kv[0]], reverse=True)

        parts = []
        for component_name, score in ranked_components[:top_components]:
            label = COMPONENT_LABELS[component_name]
            if component_name == "interest_score":
                dim = _top_contributing_dimension(profile, scaled, code, RIASEC_COLUMNS, "interest")
                parts.append(f"{label} ({dim} interest, {score:.2f})")
            elif component_name == "skill_score":
                dim = _top_contributing_dimension(profile, scaled, code, SKILL_COLUMNS, "skill")
                parts.append(f"{label} ({dim}, {score:.2f})")
            elif component_name == "labor_market_score":
                wage_pctl = matrices.labor_market.loc[code, "median_wage_percentile"]
                parts.append(f"{label} ({wage_pctl:.0%} wage percentile)")
            else:
                parts.append(f"{label} ({score:.2f})")

        reasons.append("Strongest fit: " + "; ".join(parts) + ".")

    explained["why"] = reasons
    return explained