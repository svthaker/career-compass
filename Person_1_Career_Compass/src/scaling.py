
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .feature_matrix import (
    FeatureMatrices, EDUCATION_BUCKET_COLUMN, JOB_ZONE_COLUMN,
)

# min and max as documented for each scale:
#   RIASEC (Occupational Interest, O*NET Career Interest Types): 1-7
#   Skills (O*NET Importance scale, Scales Reference "IM"): 1-5
#   Education bucket (the 5-level questionnaire scale): 1-5
#   Job Zone (O*NET Job Zone Reference): 1-5
#   Labor-market percentiles (OEWS as percentiles): 0-1
INTEREST_BOUNDS = (1.0, 7.0)
SKILL_BOUNDS = (1.0, 5.0)
EDUCATION_BOUNDS = (1.0, 5.0)
JOB_ZONE_BOUNDS = (1.0, 5.0)
LABOR_MARKET_BOUNDS = (0.0, 1.0)


def fixed_minmax_scale(values, bounds: tuple[float, float]):
    """Scale a Series/array/scalar onto [0, 1] """
    lo, hi = bounds
    scaled = (values - lo) / (hi - lo)
    return scaled.clip(0.0, 1.0) if hasattr(scaled, "clip") else max(0.0, min(1.0, scaled))


def rescale_range(value: float, old_bounds: tuple[float, float], new_bounds: tuple[float, float]) -> float:
    """Linearly remap a value from one documented scale onto another.

    Used to put the questionnaire's 1-5 RIASEC slider answers onto O*NET's 
    1-7 interest scale before scaling
    """
    old_lo, old_hi = old_bounds
    new_lo, new_hi = new_bounds
    return new_lo + (value - old_lo) * (new_hi - new_lo) / (old_hi - old_lo)


@dataclass
class ScaledMatrices:
    interest: pd.DataFrame
    skill: pd.DataFrame
    education: pd.Series          
    job_zone: pd.Series           
    labor_market: pd.DataFrame


def scale_matrices(matrices: FeatureMatrices) -> ScaledMatrices:
    return ScaledMatrices(
        interest=fixed_minmax_scale(matrices.interest, INTEREST_BOUNDS),
        skill=fixed_minmax_scale(matrices.skill, SKILL_BOUNDS),
        education=fixed_minmax_scale(matrices.education[EDUCATION_BUCKET_COLUMN], EDUCATION_BOUNDS),
        job_zone=fixed_minmax_scale(matrices.job_zone[JOB_ZONE_COLUMN], JOB_ZONE_BOUNDS),
        labor_market=fixed_minmax_scale(matrices.labor_market, LABOR_MARKET_BOUNDS),
    )