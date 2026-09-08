"""Step 10: record the top recommendations from every model, for every
evaluation profile.

Mirrors the existing output pattern in run_person1.py (baseline_top5/top10) so
these new files sit alongside it consistently in outputs/.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from .compatibility import compute_weighted_compatibility
from .config import OUTPUT_DIR
from .cosine_model import recommend_cosine
from .explain import explain_recommendations
from .feature_matrix import FeatureMatrices, build_feature_matrices
from .knn_model import KNN_METRICS, recommend_knn
from .scaling import ScaledMatrices, scale_matrices
from .test_profiles import TEST_PROFILES
from .user_profile import UserProfile

RESULT_COLUMNS = [
    "model", "profile_name", "rank", "onet_soc_code", "soc_code", "occupation_title",
    "interest_score", "skill_score", "education_score", "job_zone_score", "labor_market_score",
    "why",
]


def run_all_models_for_profiles(
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profiles: Iterable[UserProfile],
    top_n: int = 10,
) -> dict[str, pd.DataFrame]:
    weighted_frames, cosine_frames = [], []
    knn_frames: dict[str, list[pd.DataFrame]] = {metric: [] for metric in KNN_METRICS}

    for profile in profiles:
        weighted = compute_weighted_compatibility(matrices, scaled, profile, top_n=top_n)
        weighted = explain_recommendations(weighted, matrices, scaled, profile)
        weighted_frames.append(weighted)

        cosine = recommend_cosine(matrices, scaled, profile, top_n=top_n)
        cosine = explain_recommendations(cosine, matrices, scaled, profile)
        cosine_frames.append(cosine)

        for metric, metric_kwargs in KNN_METRICS.items():
            knn = recommend_knn(matrices, scaled, profile, k=top_n, metric=metric, **metric_kwargs)
            knn = explain_recommendations(knn, matrices, scaled, profile)
            knn_frames[metric].append(knn)

    results = {
        "weighted": pd.concat(weighted_frames, ignore_index=True),
        "cosine": pd.concat(cosine_frames, ignore_index=True),
    }
    for metric, frames in knn_frames.items():
        results[f"knn_{metric}"] = pd.concat(frames, ignore_index=True)
    return results


def save_results(results: dict[str, pd.DataFrame], top_n: int = 10) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for model_name, df in results.items():
        df.to_csv(OUTPUT_DIR / f"{model_name}_top{top_n}_results.csv", index=False)

    available_columns = [c for c in RESULT_COLUMNS if c in next(iter(results.values())).columns]
    comparison = pd.concat(
        [df[available_columns][df[available_columns]["rank"] <= 5] for df in results.values()],
        ignore_index=True,
    ).sort_values(["profile_name", "model", "rank"])
    comparison.to_csv(OUTPUT_DIR / "model_comparison_top5.csv", index=False)


def main() -> None:
    from .config import DATA_PATH
    from .data_prep import load_master_data, create_person1_modeling_data

    modeling = create_person1_modeling_data(load_master_data(DATA_PATH))
    matrices = build_feature_matrices(modeling)
    scaled = scale_matrices(matrices)

    results = run_all_models_for_profiles(matrices, scaled, TEST_PROFILES, top_n=10)
    save_results(results, top_n=10)

    print("\nRecommender outputs created successfully.")
    for name, df in results.items():
        print(f"  {name}: {len(df)} rows ({df['profile_name'].nunique()} profiles x top-10)")


if __name__ == "__main__":
    main()