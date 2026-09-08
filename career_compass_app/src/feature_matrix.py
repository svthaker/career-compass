
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import RIASEC_COLUMNS, SKILL_COLUMNS

JOB_ZONE_COLUMN = "job_zone"
EDUCATION_COLUMN = "education_expected_category"
EDUCATION_SUPPORT_COLUMN = "education_bachelors_or_higher_pct"
EDUCATION_BUCKET_COLUMN = "education_category_bucket"
LABOR_MARKET_COLUMNS = ["median_wage_percentile", "employment_percentile"]

ID_COLUMN = "onet_soc_code"
LOOKUP_COLUMNS = ["onet_soc_code", "soc_code", "occupation_title", "occupation_description"]

# Raw O*NET education category -> questionnaire's 5-level EDUCATION_OPTIONS scale.
# 1 = less than HS, 2 = HS diploma, 3-5 = post-secondary certificate/some college/
# associate's, 6 = bachelor's, 7-12 = post-bacc certificate through post-doctoral.
_EDUCATION_BUCKET_EDGES = [-float("inf"), 1.5, 2.5, 5.5, 6.5, float("inf")]
_EDUCATION_BUCKET_LABELS = [1, 2, 3, 4, 5]


def bucket_education_category(values: pd.Series) -> pd.Series:
    """Map the continuous ~1-12 O*NET education value onto the 1-5 questionnaire scale."""
    bucketed = pd.cut(values, bins=_EDUCATION_BUCKET_EDGES, labels=_EDUCATION_BUCKET_LABELS)
    return bucketed.astype("float").astype("Int64")


@dataclass
class FeatureMatrices:
    lookup: pd.DataFrame           
    interest: pd.DataFrame         
    skill: pd.DataFrame            
    education: pd.DataFrame        
    job_zone: pd.DataFrame         
    labor_market: pd.DataFrame     

    @property
    def index(self) -> pd.Index:
        return self.interest.index


def build_feature_matrices(modeling_df: pd.DataFrame, verbose: bool = True) -> FeatureMatrices:
    df = modeling_df.copy()

    n_start = len(df)
    df = df.dropna(subset=LABOR_MARKET_COLUMNS)
    n_dropped = n_start - len(df)
    if verbose:
        print(f"Dropped {n_dropped} / {n_start} occupations missing labor-market data "
              f"(no OEWS wage/employment estimate). Not recommendable.")

    impute_columns = RIASEC_COLUMNS + SKILL_COLUMNS + [JOB_ZONE_COLUMN, EDUCATION_COLUMN]
    remaining_missing = df[impute_columns].isna().sum()
    remaining_missing = remaining_missing[remaining_missing > 0]
    if verbose and len(remaining_missing):
        print(f"Median-imputing remaining gaps in {len(remaining_missing)} columns "
              f"for the {len(df)} eligible occupations:")
        print(remaining_missing)
    df[impute_columns] = df[impute_columns].fillna(df[impute_columns].median(numeric_only=True))

    df[EDUCATION_BUCKET_COLUMN] = bucket_education_category(df[EDUCATION_COLUMN])
    # Bucketing can itself introduce NaN only if the input was NaN post-impute, which
    # shouldn't happen; guard anyway with the column median bucket as a fallback.
    if df[EDUCATION_BUCKET_COLUMN].isna().any():
        fallback = int(df[EDUCATION_BUCKET_COLUMN].median())
        df[EDUCATION_BUCKET_COLUMN] = df[EDUCATION_BUCKET_COLUMN].fillna(fallback)

    df = df.set_index(ID_COLUMN, drop=False)

    lookup = df[LOOKUP_COLUMNS].copy()
    interest = df[RIASEC_COLUMNS].copy()
    skill = df[SKILL_COLUMNS].copy()
    education = df[[EDUCATION_BUCKET_COLUMN, EDUCATION_SUPPORT_COLUMN]].copy()
    job_zone = df[[JOB_ZONE_COLUMN]].copy()
    labor_market = df[LABOR_MARKET_COLUMNS].copy()

    return FeatureMatrices(
        lookup=lookup, interest=interest, skill=skill,
        education=education, job_zone=job_zone, labor_market=labor_market,
    )


if __name__ == "__main__":
    from .config import DATA_PATH
    from .data_prep import load_master_data, create_person1_modeling_data

    modeling = create_person1_modeling_data(load_master_data(DATA_PATH))
    matrices = build_feature_matrices(modeling)
    print(f"\nFinal eligible occupation count: {len(matrices.index)}")