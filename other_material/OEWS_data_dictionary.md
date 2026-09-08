# OEWS (Occupational Employment and Wage Statistics) — Data Dictionary

Source: U.S. Bureau of Labor Statistics, OEWS program (directory: `oews_data_yearly/`).
Row counts, dtypes, and category values below were verified directly against
`all_data_M_2025.csv` (413,527 rows) and `oesm24nat/national_M2024_dl.xlsx` (1,403 rows,
national-only). Column layout is consistent across both.

## File inventory

| Files | Format | Notes |
|---|---|---|
| `all_data_M_2025.xlsx` / `all_data_M_2025.csv` | Excel 2007+ / CSV | Most recent full release (national + state + metro/nonmetro areas). The CSV export formats wage columns with comma thousands separators (`"69,770"`) and `"#"`/`"*"` as suppression markers — read with `pd.read_csv(..., thousands=",", na_values=["#","*"])`. |
| `oesmXXnat/national_MYYYY_dl.xlsx` (2012–2024) | Excel 2007+ | National-only estimates, one folder per year. Load with `pd.read_excel(path, engine="openpyxl")`. |
| `national_*_dl.xls`, `national_MYYYY_dl.xls` (1997–2011) | Legacy Excel (OLE/CFBF) | National-only, older schema — column names/layout may differ from the modern schema below; verify with `pd.ExcelFile(path).sheet_names` and `df.columns` before assuming it matches. Load with `pd.read_excel(path, engine="xlrd")` (requires `pip install xlrd`). |
| `field_descriptions.xls` | Legacy Excel | BLS's own field/code documentation — the authoritative source for exact category-code meanings (e.g. full `OWN_CODE` mapping) not otherwise re-derived here. |

**Row granularity:** each row is one estimate for a `(geographic area, industry, occupation)`
combination at a specific level of aggregation — not a flat, uniform table. `AREA_TYPE`,
`I_GROUP`, and `O_GROUP` (below) each encode a different aggregation level in the *same*
column, so rows must be filtered to one consistent level before aggregating anything
(summing `TOT_EMP` or averaging wage columns across unfiltered rows double-counts).

---

## Identifiers, predictors, and recommendation role

**Project goal:** a recommendation system that matches users to occupations based on
skills/education/interests (see `ONET_data_dictionary.md` for the matching features), plus
labor-market analytics on the matched occupations. OEWS's role here is **not** matching —
it's the analytics layer presented alongside a recommendation, so "predictors" doesn't apply
in the usual sense.

| Role | Fields |
|---|---|
| **Join key to O*NET** | `OCC_CODE` — joins to `O*NET-SOC Code` after stripping O*NET's `.00`/`.01` detail suffix (`onet_code[:7] == occ_code`). Expect multiple O*NET-SOC codes to map to one `OCC_CODE`, since OEWS reports at the standard 6-digit SOC level while O*NET splits some SOC codes into finer detailed occupations. |
| **Required filters before use** (not features — these define which "slice" of the table you're looking at) | `AREA_TYPE` (pick one geography level, e.g. `1`=national for an overall figure or `2`=state if the recommender is geography-aware), `O_GROUP` (must be `detailed` to match O*NET's occupation granularity), `I_GROUP`/`OWN_CODE` (use `cross-industry`/`1235` unless the recommendation is meant to be industry- or sector-specific). |
| **Labor-market analytics (the decision-support output, not a model input)** | `TOT_EMP` (job availability/market size), `H_MEAN`/`A_MEAN`, `H_MEDIAN`/`A_MEDIAN`, and the percentile spread `H_PCT10`…`A_PCT90` (typical pay and pay range) — these are what get *displayed* next to a recommended occupation, e.g. "Software Developers — median $X/yr, Y people employed nationally." |
| **Reliability qualifiers (surface alongside the analytics, don't hide them)** | `EMP_PRSE`, `MEAN_PRSE` — flag low-reliability estimates (high PRSE) in the UI rather than silently presenting a shaky number as fact. |
| **Geography-aware analytics (state/metro files only)** | `JOBS_1000`, `LOC_QUOTIENT`, `PCT_TOTAL`, `PCT_RPT` — only meaningful if the recommender supports location-based filtering (e.g. "this occupation is unusually concentrated in your state"); all `NaN` in the national-only file. |

**No target variable here either** — same as the O*NET side, OEWS supplies descriptive
analytics for display, not a label to predict. If a future iteration adds occupation-growth
forecasting, that would require a different BLS dataset (Employment Projections), which
isn't part of this download.

---

## Geography fields

| Column | Type | Description |
|---|---|---|
| `AREA` | int (code) | Geographic area code. `99` = United States (national total). Not a measurement — treat as an ID/join key, not a numeric field for summary stats. |
| `AREA_TITLE` | string | Human-readable area name (e.g. `"U.S."`, `"California"`, `"Abilene, TX"`). |
| `AREA_TYPE` | int (code) | Aggregation level of the area. Observed values: `1`=National (1 value, `"U.S."`), `2`=State (51: 50 states + DC), `3`=Territory (3, e.g. Guam), `4`=Metropolitan Statistical Area (393), `6`=Nonmetropolitan Area (137). |
| `PRIM_STATE` | string | Primary state abbreviation for the area (`"US"` for the national row). |

## Industry fields

| Column | Type | Description |
|---|---|---|
| `NAICS` | string/int (code) | NAICS industry code. `0` / `000000` = cross-industry (all industries combined). |
| `NAICS_TITLE` | string | Industry name (e.g. `"Cross-industry"`, specific NAICS sector/subsector names). |
| `I_GROUP` | string (code) | NAICS aggregation level for the row. Observed values: `cross-industry` (all industries, most common — 57% of rows), `cross-industry, ownership`, `sector`, `3-digit`, `4-digit`, `5-digit`, `6-digit`, `3-digit, ownership`, `4-digit, ownership`. Higher digit-count = more granular industry breakout. |
| `OWN_CODE` | int (code) | Ownership sector combination. Base codes: `1`=Federal Government, `2`=State Government, `3`=Local Government, `5`=Private. Combination codes concatenate the base digits: `123`=Federal+State+Local Government, `235`=State+Local Government+Private, `1235`=all ownerships combined (the dominant "total" code — row count matches `I_GROUP == "cross-industry"` exactly). Confirmed by cross-referencing each code's `NAICS_TITLE` values directly in the data (e.g. `OWN_CODE == 1` only appears with `"Postal Service (Federal Government)"` / `"Federal Executive Branch"`; `123` appears with the literal title `"Federal, State, and Local Government..."`). Three industry-specific composite codes (`57` — Arts/Entertainment/Recreation and Accommodation & Food Services; `58` — Health Care and Social Assistance; `59` — Transportation and Warehousing) could not be decoded this way — `field_descriptions.xls` predates `OWN_CODE` (it documents the 2002 schema) and doesn't cover them. Confirm against BLS's current OEWS technical documentation before relying on these three. |

## Occupation fields

| Column | Type | Description |
|---|---|---|
| `OCC_CODE` | string | SOC occupation code (e.g. `"00-0000"` = All Occupations, `"11-1000"` = Top Executives). 1,394 unique values. |
| `OCC_TITLE` | string | Occupation title. 1,137 unique values (fewer than `OCC_CODE` — some titles are shared/renamed across code revisions). |
| `O_GROUP` | string (code) | SOC hierarchy level of the row. Values: `total` (`"All Occupations"`, 1,034 rows), `major` (20,580), `minor` (23,441), `broad` (62,091), `detailed` (306,381 — most granular, most common). A `major` group and its child `detailed` occupations both appear as separate rows for the same area/industry — filter to one `O_GROUP` before aggregating. |

## Employment & reliability fields

| Column | Type | Description |
|---|---|---|
| `TOT_EMP` | numeric | Total employment estimate for the row. |
| `EMP_PRSE` | numeric | Percent relative standard error of `TOT_EMP` — reliability indicator; higher = less reliable estimate. |
| `JOBS_1000` | numeric | Jobs per 1,000 employment in the area. **Only populated in state/metro-area files** — entirely `NaN` in the national-only file. |
| `LOC_QUOTIENT` | numeric | Location quotient (concentration of the occupation in this area vs. the nation). **State/metro-area files only** — entirely `NaN` nationally. |
| `PCT_TOTAL` | numeric | Percent of total (industry-level) employment. **State/metro-area files only.** |
| `PCT_RPT` | numeric | Percent of establishments reporting. **State/metro-area files only.** |

## Wage fields

All wage columns are estimates at the row's `(area, industry, occupation)` combination.
`H_*` = hourly wage, `A_*` = annual wage.

| Column | Description |
|---|---|
| `H_MEAN`, `A_MEAN` | Mean wage. |
| `MEAN_PRSE` | Percent relative standard error of the mean wage. |
| `H_PCT10`, `H_PCT25`, `H_MEDIAN`, `H_PCT75`, `H_PCT90` | Hourly wage percentiles. |
| `A_PCT10`, `A_PCT25`, `A_MEDIAN`, `A_PCT75`, `A_PCT90` | Annual wage percentiles. |
| `ANNUAL` | Flag (non-null only for occupations BLS reports as annual-only, e.g. teachers — 83/1,403 rows in the national file). Blank is the normal case, not missing data. |
| `HOURLY` | Flag (non-null only for occupations reported hourly-only — rare, 7/1,403 rows nationally). Blank is the normal case. |

**Suppression markers** (confirmed against `field_descriptions.xls`): `"#"` = wage estimate
above the top-coded reporting ceiling, `"*"` = wage estimate not available, `"**"` = employment
estimate not available. In the raw files these appear as literal text inside otherwise-numeric
columns, which forces the whole column to load as `object` dtype unless handled at read time
(`na_values=["#", "*", "**"]` for CSV; coerce with `pd.to_numeric(errors="coerce")` after
`read_excel`, which does not auto-convert these). Missingness is concentrated at the high
percentiles (`H_PCT90`/`A_PCT90`), consistent with top-end wages being the least reliably
estimated.

---

## Notes

- **This is one wide table, not a relational set of files** (unlike O*NET) — every row already
  carries area, industry, and occupation context, so there are no separate crosswalk/reference
  files to join, only the aggregation-level filtering described above.
- **Schema drift across years**: the modern 31-column schema (documented above) applies to the
  `oesmXXnat` folders (2012–2024) and `all_data_M_2025.*`. The legacy `national_*_dl.xls` files
  (1997–2011) predate this layout and should have their columns checked individually before
  reuse — do not assume they match.
- **CSV vs Excel loading produces different raw dtypes** for the same data — see the file
  inventory table above. Standardize on one approach (or normalize dtypes immediately after
  loading) if combining CSV and Excel sources into the same analysis.
- Numeric-looking columns that are actually categorical codes: `AREA`, `AREA_TYPE`, `NAICS`,
  `OWN_CODE`. Exclude these from `.describe()`/histogram-style numeric summaries; use
  `value_counts()`/`nunique()` instead.
