# Person 2 Pipeline Additions

Builds three recommendation models on top of the Person 1 baseline, sharing one
feature space. Demonstrated in `Person2.ipynb`; run via `run_all.py`.

## New files (`src/`)

| File | What it does |
|---|---|
| `feature_matrix.py` | Builds 5 component matrices (interest, skill, education, job_zone, labor_market); drops occupations missing OEWS data, median-imputes smaller gaps. |
| `scaling.py` | Scales each block to `[0, 1]` using documented O*NET/questionnaire scale bounds (not empirical fit). |
| `compatibility.py` | Per-component compatibility scores + the interpretable weighted model. |
| `vector_builder.py` | Shared combined feature vector for the cosine/KNN models, with block-width correction. |
| `cosine_model.py` | Cosine-similarity recommender. |
| `knn_model.py` | K-nearest-neighbors recommender (Euclidean distance). |
| `sensitivity.py` | Weight-configuration and K-value sensitivity tests. |
| `explain.py` | Model-agnostic "why this occupation" explanations, ranked by weighted contribution. |
| `evaluate.py` | Runs all 3 models across every test profile, saves results to `outputs/`. |

`run_all.py` now also calls `src.evaluate.main()`.

## Two things to flag

1. **Recommendable catalog is 956 occupations, not 1,016.** 60 occupations are
   dropped for missing OEWS labor-market data and can never appear in any
   model's output. Use 956 as the catalog-coverage denominator, and check any
   "expected relevant occupation" pick against this eligible set.
2. **`baseline_model.py`'s output schema doesn't match the 3 new models.** It has
   no `interest_score`/`skill_score`/`education_score`/`job_zone_score` columns.
   A unified comparison table across all models needs to handle this column
   mismatch explicitly.