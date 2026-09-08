from __future__ import annotations
import pandas as pd
from .config import DATA_PATH, OUTPUT_DIR, DISPLAY_COLUMNS, MODELING_COLUMNS


def load_master_data(path=DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    required = set(DISPLAY_COLUMNS + MODELING_COLUMNS)
    missing = sorted(required.difference(df.columns))
    if missing:
        raise KeyError(f"The master dataset is missing required columns: {missing}")
    return df


def create_person1_modeling_data(df: pd.DataFrame) -> pd.DataFrame:
    selected = list(dict.fromkeys(DISPLAY_COLUMNS + MODELING_COLUMNS))
    out = df[selected].copy()
    out = out.drop_duplicates(subset=["onet_soc_code"], keep="first")
    return out


def create_feature_list(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df.columns:
        if column in DISPLAY_COLUMNS and column not in MODELING_COLUMNS:
            role = "display_only"
        elif column in MODELING_COLUMNS:
            role = "modeling"
        else:
            role = "excluded"
        reason = {
            "modeling": "Questionnaire-compatible or labor-market feature used by recommendation models.",
            "display_only": "Retained to identify and explain recommendations, but not used as a model input.",
            "excluded": "Identifier, description, duplicate, intermediate, aggregate, or non-questionnaire feature."
        }[role]
        rows.append({"feature": column, "role": role, "reason": reason})
    return pd.DataFrame(rows)


def save_person1_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master_data()
    modeling = create_person1_modeling_data(master)
    feature_list = create_feature_list(master)
    modeling.to_csv(OUTPUT_DIR / "person1_modeling_data.csv", index=False)
    feature_list.to_csv(OUTPUT_DIR / "modeling_feature_list.csv", index=False)
    return modeling, feature_list

if __name__ == "__main__":
    modeling, features = save_person1_data()
    print(f"Saved modeling data: {modeling.shape[0]:,} rows x {modeling.shape[1]:,} columns")
    print(features["role"].value_counts())
