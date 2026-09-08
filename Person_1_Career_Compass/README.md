# Career Compass — Person 1 Code Package

This package completes the Person 1 development requirements:

- User-profile questionnaire and schema
- User-response to O*NET feature mapping
- Final modeling feature list
- Reduced Person 1 modeling dataset
- Labor-market baseline recommender
- Top-5 and top-10 recommendations for development profiles
- End-to-end project pipeline figure
- Streamlit questionnaire and baseline prototype

## Run everything

From this folder:

```bash
pip install -r requirements.txt
python run_all.py
```

The generated files will appear in `outputs/` and `figures/`.

## Run the Streamlit app

```bash
streamlit run app.py
```

## Important baseline decision

The baseline score uses `median_wage_percentile` and `employment_percentile` with weights controlled by the user's salary and employment importance answers. The existing `labor_market_opportunity_score` is retained in the result table but is not added to the formula because it is already calculated from wage and employment measures. Adding it again would double-count the same information.

## Person 3 handoff

The six profiles in `src/test_profiles.py` are temporary development profiles. Replace them with Person 3's final documented evaluation profiles once those are approved.
