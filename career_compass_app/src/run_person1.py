from __future__ import annotations
import json
import pandas as pd
from .config import OUTPUT_DIR
from .data_prep import save_person1_data
from .baseline_model import recommend_for_profiles
from .test_profiles import TEST_PROFILES
from .user_profile import QUESTIONNAIRE_SCHEMA, SKILL_LABEL_TO_COLUMN


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    modeling, feature_list = save_person1_data()

    with open(OUTPUT_DIR / "user_profile_questionnaire_schema.json", "w", encoding="utf-8") as f:
        json.dump(QUESTIONNAIRE_SCHEMA, f, indent=2)

    mapping = pd.DataFrame([
        {"user_response": label, "dataset_feature": column, "mapping_type": "selected skill -> O*NET skill importance"}
        for label, column in SKILL_LABEL_TO_COLUMN.items()
    ])
    base_mapping = pd.DataFrame([
        ["Realistic interest", "interest_realistic", "direct 1-5 preference"],
        ["Investigative interest", "interest_investigative", "direct 1-5 preference"],
        ["Artistic interest", "interest_artistic", "direct 1-5 preference"],
        ["Social interest", "interest_social", "direct 1-5 preference"],
        ["Enterprising interest", "interest_enterprising", "direct 1-5 preference"],
        ["Conventional interest", "interest_conventional", "direct 1-5 preference"],
        ["Education preference", "education_expected_category", "ordinal category 1-5"],
        ["Job-zone preference", "job_zone", "ordinal category 1-5"],
        ["Salary importance", "median_wage_percentile", "controls baseline weight"],
        ["Employment-opportunity importance", "employment_percentile", "controls baseline weight"],
    ], columns=["user_response", "dataset_feature", "mapping_type"])
    pd.concat([base_mapping, mapping], ignore_index=True).to_csv(
        OUTPUT_DIR / "user_response_feature_mapping.csv", index=False
    )

    top10 = recommend_for_profiles(modeling, TEST_PROFILES, top_n=10)
    top5 = top10[top10["rank"] <= 5].copy()
    top5.to_csv(OUTPUT_DIR / "baseline_top5_results.csv", index=False)
    top10.to_csv(OUTPUT_DIR / "baseline_top10_results.csv", index=False)

    profiles = pd.DataFrame([p.to_dict() for p in TEST_PROFILES])
    profiles.to_csv(OUTPUT_DIR / "development_test_profiles.csv", index=False)

    print("Person 1 outputs created successfully.")
    print(f"Modeling dataset: {modeling.shape}")
    print(f"Top-10 result rows: {len(top10)}")

if __name__ == "__main__":
    main()
