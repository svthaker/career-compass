# Paul Matta — Data Preparation and Feature Engineering Deliverables

## Main workflow
Run from the repository root:

```bash
python code/data_preparation_feature_engineering.py
```

The script expects the official O*NET 30.3 Excel archive and May 2025 BLS OEWS All Data archive under `data/raw/onet` and `data/raw/bls` at the repo root. Generated files are written to `data/`.

## Generated outputs

All land in `data/` at the repo root:

- `career_compass_master.csv`: final occupation-level master dataset
- `bls_national_detailed_clean.csv`: filtered BLS national detailed occupation table
- `data_quality_report.csv`: validation results
- `missing_values_report.csv`: missingness by variable
- `unmatched_onet_occupations.csv`: O*NET records without a BLS match
- `feature_dictionary.csv`: source, data type, and modeling role for every final variable
- `results_summary.md`: key row, column, and match totals
- `data_preparation_and_feature_engineering_sections.md`: paper-ready draft sections using the actual results

## Important modeling note
The labor-market opportunity score uses current wage and employment percentiles. It is not a job-growth score because the OEWS file does not contain projections.
