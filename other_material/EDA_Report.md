# EDA Report — O*NET 30.3 and OEWS Datasets

Prepared in support of the capstone project goal: a data-driven recommendation system
matching users to occupations based on skills, education, and interests, paired with
labor-market analytics for informed decision-making.

All statistics below were computed directly against `db_30_3_text/` (O*NET 30.3) and
`oews_data_yearly/all_data_M_2025.csv` (OEWS). See `ONET_data_dictionary.md` and
`OEWS_data_dictionary.md` for full per-file/per-column schema reference — this report
focuses on variable roles, data quality, relevance, and relationships.

---

## 1. Main variables: identifiers, predictors, targets, derived variables

There is no single supervised target in this project — the system is a **similarity-matching
recommender**, not a regression/classification model. Variable roles are organized around
that fact.

### Identifiers

| Variable | Dataset | Role |
|---|---|---|
| `O*NET-SOC Code` | O*NET | Primary occupation key across all 45 O*NET tables. |
| `OCC_CODE` | OEWS | Occupation key in OEWS; joins to `O*NET-SOC Code`. |
| `Element ID` / `Scale ID` | O*NET | Identify *which descriptor* (ability, skill, knowledge area) and *which scale* (Importance/Level) a rating row refers to — structural keys, not content. |
| `AREA`, `NAICS`, `OWN_CODE` | OEWS | Geography/industry/ownership codes — join/filter keys, not measurements (see Section 2/4 on why these must not be treated as numeric predictors). |

**Join key mismatch (quantified):** O*NET-SOC codes carry a 2-digit detail suffix
(`15-1252.00`, `15-1252.01`, …) that OEWS's `OCC_CODE` doesn't. Stripping the suffix
(`code[:7]`) and joining, **67 of 798 OEWS occupation codes (8.4%) receive more than one
O*NET-SOC code**, with as many as **9 O*NET-SOC codes collapsing onto a single OEWS code**.
This is a structural limitation (OEWS reports at the 6-digit SOC level; O*NET splits some
SOC codes into finer detailed occupations) — it means wage data is coarser than occupation
matching can be, not a data error.

### Predictors (occupation-profile features for matching)

| Variable | Dataset | Why it's a predictor here |
|---|---|---|
| Abilities / Knowledge / Essential Skills / Software Skills `Data Value` (filtered to `Scale ID == "LV"`) | O*NET | The numeric feature vector a user's self-reported skill profile is compared against. |
| Education.txt `Category` distribution, `Job Zones.txt` `Job Zone` | O*NET | Encodes required credential/preparation level — see Section 4 for validation that this tracks real wage differences. |
| Career Interest Types (RIASEC) `Data Value` | O*NET | Direct feature space for interest-based matching (Holland code framework). |
| Specific Interest Areas `Data Value` | O*NET | Finer-grained interest sub-features, optional secondary signal. |

### Analytics outputs (not matching predictors — the "informed decision-making" layer)

| Variable | Dataset | Role |
|---|---|---|
| `A_MEDIAN`, `H_MEAN`, `A_PCT10`…`A_PCT90` | OEWS | Pay figures displayed alongside a recommended occupation. |
| `TOT_EMP` | OEWS | Job-market size / availability signal. |
| `EMP_PRSE`, `MEAN_PRSE` | OEWS | Reliability qualifiers — should be surfaced, not hidden, per the "informed" part of the project goal. |

### Derived variables (need to be engineered — not present as-is)

- **Per-occupation feature vector**: pivoting `Element Name` → columns from Abilities/Knowledge/Skills/Interests tables (currently long/tall format, one row per occupation-element-scale).
- **User profile vector**: constructed from intake-form responses, encoded onto the same scale/dimensions as the O*NET feature vector above — does not exist in either dataset and must be designed.
- **Similarity/match score**: computed at query time (e.g. cosine similarity between user vector and each occupation vector) — the closest thing to a "target," but it's computed, not learned or labeled.
- **Log-transformed wage/employment fields**: recommended derived versions of `A_MEDIAN` and `TOT_EMP` (see Section 4 — both are heavily right-skewed in raw form).
- **Filtered/deduplicated occupation-level wage table**: `OEWS` filtered to one `AREA_TYPE`/`O_GROUP`/`I_GROUP`/`OWN_CODE` combination — required before any analytics or joins to O*NET, not usable in raw form.

---

## 2. Data quality issues (quantified) and mitigation

### O*NET

| Issue | Quantified impact | Mitigation |
|---|---|---|
| **Type mismatch**: all columns load as `dtype=str` from the raw `.txt` files | 100% of numeric-intended columns (`Data Value`, `N`, `Standard Error`, etc.) load as text | Explicit `pd.to_numeric(errors="coerce")` pass on known numeric columns after load (see `ONET_data_dictionary.md`). |
| **Missing values** — `Not Relevant` flag | ~50% missing in Abilities/Essential Skills/Transferable Skills/Work Activities | By design: blank means "not flagged as irrelevant," not missing data — no imputation needed, just correct interpretation. |
| **Missing values** — CI bounds / Standard Error | 23–27% missing in Knowledge.txt; up to 67% in Education.txt | Traced to occupations with small survey samples where CI couldn't be computed — **not** primarily driven by the `Recommend Suppress` flag itself, which is rare (`Recommend Suppress == "Y"` in only **0.1%** of Abilities.txt rows). `Data Value` itself remains populated in almost all cases, so the core rating used for matching is largely intact; CI/SE fields are only relevant if you need estimate-uncertainty, not for the matching feature itself. |
| **Duplicates** | **0** duplicated `(O*NET-SOC Code, Element ID, Scale ID)` keys in Abilities.txt or Knowledge.txt; 0 duplicated SOC codes in Occupation Data.txt or Job Zones.txt | None found — no dedup step needed. |
| **Scale bound violations** | **0 / 92,976** Abilities rows and **0 / 59,004** Knowledge rows fall outside the documented min/max in Scales Reference.txt | Data respects its own documented bounds — validated, no clipping needed. |
| **Potential leakage** | `Related Occupations.txt` was proposed (see prior discussion) as an evaluation/ground-truth source for the recommender. If O*NET's own methodology derived occupation relatedness partly from the same skill/ability/interest similarity your recommender uses, evaluating against it risks circular validation (the "ground truth" and the "model" measuring the same underlying signal). | Treat `Related Occupations.txt` as a qualitative sanity check only, not a quantitative accuracy benchmark, unless you can confirm its derivation methodology is independent of your feature set. |

### OEWS

| Issue | Quantified impact | Mitigation |
|---|---|---|
| **Type mismatch** — CSV comma formatting | 100% of wage values in `all_data_M_2025.csv` load as text (`"69,770"`) unless handled | `pd.read_csv(..., thousands=",", na_values=["#","*","**"])` at load time. |
| **Suppression markers** (`"#"`, `"*"`, `"**"`) | On the analysis-relevant slice (national, `O_GROUP == "detailed"`, `I_GROUP == "cross-industry"`, 830 rows): `H_MEAN`/hourly percentiles **6.99%** missing, `A_MEAN`/annual percentiles **0.60%** missing | Coerce with `na_values` at load (CSV) or `pd.to_numeric(errors="coerce")` after `read_excel`. Note this is **much lower** than the unfiltered full-file missingness reported earlier in this project (33%+) — filtering to the correct aggregation level before assessing data quality matters; the raw full-file numbers overstated the problem for the slice actually used. |
| **Structurally absent fields** | `JOBS_1000`, `LOC_QUOTIENT`, `PCT_TOTAL`, `PCT_RPT` are **100% missing** in the national-only context | Not a defect — these only populate in state/metro-area rows. Exclude from national-level analysis; only use if the recommender adds geography-aware filtering. |
| **Duplicates** | 0 fully duplicated rows; but **3,541 / 413,527 (0.86%)** rows share the same `(AREA, NAICS, OCC_CODE, OWN_CODE)` combination despite not being fully identical. On the actual analysis slice (national/detailed/cross-industry), **0** duplicate `OCC_CODE`s. | The composite key needs to include `I_GROUP` (or another dimension) to be truly unique — worth widening the key before treating rows as one-per-combination at finer aggregation levels. The slice actually used for the recommender is clean. |
| **Outliers** | `A_MEDIAN` on the national/detailed slice: IQR-based outliers = **57 / 825 (6.9%)**, dominated by physician specialties (Pediatric Surgeons $559,030; Cardiologists $496,010; Radiologists $420,860). Raw skewness = **4.15**. | These are legitimate high-earning occupations, not data errors — do not remove. Log-transform (`log1p`) reduces skewness to **1.21**; recommended for any histogram/model use of wage figures rather than dropping outliers. |
| **Outliers / skew** | `TOT_EMP` raw skewness = **5.22**; after `log1p`, skewness = **0.06** (nearly symmetric) | Strongly recommend log-transforming employment counts for any visualization or magnitude-based feature — the raw scale is dominated by a few very large occupations (e.g. "All Occupations," retail/food service). |
| **Potential leakage / double-counting** | Mixing aggregation levels (e.g. `O_GROUP == "major"` and `"detailed"` rows together) causes the same underlying employment to be counted at multiple levels simultaneously if not filtered — functionally similar to a leakage problem in that an aggregate would "double count" information already present in its own subcomponents. | Always filter to exactly one `AREA_TYPE`/`O_GROUP`/`I_GROUP`/`OWN_CODE` combination before aggregating or joining (established in `OEWS_data_dictionary.md`). |

---

## 3. Connection to project goal — why each major variable matters

The project goal has two halves: **(a)** match users to occupations on skills/education/
interests, and **(b)** present labor-market analytics for informed decision-making. Each
major variable maps to one or the other:

- **`O*NET-SOC Code` / `OCC_CODE`** — without a working join key between the two datasets,
  the system can produce occupation matches (a) but never attach real wage/employment data
  to them (b). This single relationship is what makes the two datasets a combined system
  rather than two independent tools.
- **Abilities / Knowledge / Essential Skills / Software Skills `Data Value`** — this *is* the
  literal feature space for "matching users based on skills." Without it, "skills" in the
  project goal has no operational definition.
- **Education.txt / Job Zones.txt** — operationalizes "matching based on education."
  Cross-dataset analysis (Section 4) confirms Job Zone isn't just a labeling convenience — it
  tracks a real, substantial wage difference (median wage roughly doubles from Job Zone 2 to
  Job Zone 4), which justifies using it as a meaningful filter/feature rather than a cosmetic
  category.
- **Career Interest Types (RIASEC)** — operationalizes "matching based on interests" using a
  validated framework from career counseling research (Holland codes), giving the interest-
  matching component of the system a principled basis rather than an ad hoc survey.
- **OEWS wage and employment fields** — directly implement "labor market analytics that
  support informed decision-making." `A_MEDIAN`/`A_PCT10`-`A_PCT90` let the system show not
  just "this job pays well" but the realistic pay *range*, which matters given the
  heteroscedasticity finding in Section 4.
- **`EMP_PRSE`/`MEAN_PRSE`** — supports the "informed" requirement specifically: a
  recommendation system that presents unreliable estimates as if they were precise would
  undermine the stated goal rather than serve it.
- **`Related Occupations.txt`** — supports the "evaluate" half of the project goal as a
  sanity-check source for the recommender's own output (with the leakage caveat noted in
  Section 2).
- **Structural/filter fields** (`O_GROUP`, `AREA_TYPE`, `I_GROUP`, `OWN_CODE`, `Scale ID`) —
  contribute nothing to the user-facing recommendation or analytics directly, but are
  necessary preconditions: get these wrong and the "labor market analytics" become simply
  incorrect, which is worse than not having them at all.

---

## 4. Relationships between variables

### Within O*NET: Importance vs. Level are near-redundant

Pearson correlation between the `IM` (Importance) and `LV` (Level) scales, paired at the
`(occupation, element)` level:

- **Abilities.txt: r = 0.976** (n = 46,488 paired observations)
- **Knowledge.txt: r = 0.963**

This is strong multicollinearity — the two scales carry almost the same information for
matching purposes. **Implication:** include only one scale (recommend `LV`, since "level
required" is more directly comparable to a user's self-rated proficiency than "how important
is this in general") in the occupation feature vector, rather than both. Including both would
inflate the influence of well-correlated dimensions in a similarity computation without adding
real signal.

### RIASEC interest types are heavily imbalanced across occupations

Distribution of each occupation's *dominant* (highest-scoring) interest type:

| Interest type | % of occupations where it's dominant |
|---|---|
| Realistic | 42.0% |
| Conventional | 18.0% |
| Social | 14.0% |
| Investigative | 12.1% |
| Enterprising | 10.8% |
| Artistic | 3.0% |

This reflects the real composition of the labor market (many hands-on/technical occupations),
not a data defect. **Implication:** do not collapse a user's or occupation's interest profile
to a single "top type" categorical for matching — doing so would systematically over-serve
Realistic-leaning users and under-serve the 3%-share Artistic-leaning ones. Keep the full
continuous 6-dimension RIASEC vector as the matching feature instead.

### Ability importance doesn't scale linearly with Job Zone — implication for feature engineering

Average ability *importance* (`IM` scale, averaged across all 52 abilities) by Job Zone:

| Job Zone | Mean | Std | N occupations |
|---|---|---|---|
| 2 | 2.55 | 0.25 | 324 |
| 3 | 2.56 | 0.26 | 204 |
| 4 | 2.36 | 0.21 | 215 |
| 5 | 2.37 | 0.22 | 151 |

Despite Job Zone tracking wage strongly (below), the simple *mean* importance across all
abilities is roughly flat and even dips slightly at Job Zone 4–5. This suggests higher-prep
occupations don't need uniformly elevated importance across every ability — they need very
high importance on a *specific subset* (e.g. advanced reasoning for a scientist, but not
elevated physical-strength requirements), which a flat average washes out.
**Implication:** engineering a single "average skill importance" feature would lose the signal
that actually differentiates job zones; keep the full per-ability vector (or use a max/top-k
summary) rather than compressing to a scalar mean.

### OEWS wage measures are highly multicollinear; employment is nearly independent of wage

Correlation matrix (national, detailed occupations, cross-industry):

| | H_MEAN | A_MEAN | A_PCT10 | A_PCT25 | A_MEDIAN | A_PCT75 | A_PCT90 | TOT_EMP | EMP_PRSE |
|---|---|---|---|---|---|---|---|---|---|
| H_MEAN | 1.00 | 1.00 | 0.86 | 0.96 | 0.99 | 1.00 | 0.99 | -0.08 | 0.21 |
| A_MEDIAN | 0.99 | 0.98 | 0.85 | 0.96 | 1.00 | 0.99 | 0.93 | -0.09 | 0.21 |
| TOT_EMP | -0.08 | -0.09 | -0.09 | -0.09 | -0.09 | -0.09 | -0.08 | 1.00 | -0.26 |

Every wage measure correlates ≥ 0.77 with every other wage measure (most ≥ 0.93) —
severe multicollinearity. `TOT_EMP` and `EMP_PRSE`, however, correlate weakly with wage
(-0.08 to 0.21) and carry independent information. **Implication:** use one representative
wage figure (`A_MEDIAN` — more robust to the high-earner outliers noted in Section 2 than
`A_MEAN`) as "the" pay signal rather than including multiple near-duplicate wage columns;
keep `TOT_EMP` and `EMP_PRSE` as separate, independent signals (market size and estimate
confidence, respectively).

### Structural OEWS categories are severely imbalanced — by design, not a modeling problem

| Field | Dominant category | Share |
|---|---|---|
| `O_GROUP` | `detailed` | 74.1% |
| `AREA_TYPE` | National (1) | 42.9%, followed by Metro area (4) at 36.3% |
| `I_GROUP` | `cross-industry` | 57.4% |
| `OWN_CODE` | `1235` (all ownerships) | 57.4% |

These aren't classes to rebalance via resampling — they're filters that define the unit of
analysis (established in `OEWS_data_dictionary.md`). The implication is architectural:
always explicitly filter to one category per field before any aggregation, correlation, or
join, rather than treating this imbalance as something to correct statistically.

### Cross-dataset: Job Zone tracks wage, but with growing variance at higher zones

Joining O*NET Job Zones to OEWS `A_MEDIAN` via the stripped `OCC_CODE` key (96.1% match rate):

| Job Zone | Mean wage | Median wage | Std dev | N |
|---|---|---|---|---|
| 2 | $49,551 | $47,150 | $13,421 | 318 |
| 3 | $67,880 | $63,190 | $21,834 | 203 |
| 4 | $97,060 | $92,100 | $31,153 | 215 |
| 5 | $136,296 | $100,330 | $90,197 | 151 |

Median wage roughly doubles from Job Zone 2 to Job Zone 4, and mean/median diverge sharply
at Job Zone 5 ($136k mean vs. $100k median) — driven by the same high-earning outliers
identified in Section 2 (physicians, surgeons). Standard deviation grows **7x** from Job
Zone 2 to Job Zone 5. **Implication:** Job Zone is a genuinely useful coarse predictor of pay
(validating its use as a matching/filter feature), but a single point estimate is misleading
at the high end — the analytics layer should show the full wage distribution (e.g. 10th–90th
percentile range), not just a mean or median, especially for Job Zone 4–5 matches.

### Cross-dataset: many-to-one join limits achievable granularity

As noted in Section 1, 8.4% of OEWS occupation codes map to multiple O*NET-SOC codes
(max 9-to-1). Any correlation or joint analysis between O*NET occupation-level features and
OEWS wage is therefore bounded by OEWS's coarser granularity — several O*NET detailed
occupations will show identical wage figures when displayed, which should be disclosed as a
known limitation rather than treated as a modeling error to fix.

---

## Project Q&A

Plain-language answers to the standard project-milestone questions, grounded in the
findings above.

### What data will you be using, where does it come from, and how would production data be accessed?

Two public U.S. government datasets, joined on occupation: **O*NET 30.3** (O*NET Resource
Center / U.S. Department of Labor — occupation descriptions: abilities, skills, knowledge,
education, interests) and **OEWS** (Bureau of Labor Statistics — wage and employment
estimates by occupation, geography, and industry). Both were used here as static downloaded
snapshots, not live feeds.

In a production version: **O*NET** is revised on an annual release cycle, so the natural
approach is to batch-ingest each new full-database release on that cadence (the same file
format used here), rather than call an API per request — though O*NET does expose a public
Web Services API for on-demand single-occupation lookups if live queries were ever needed
instead of a locally held copy. **OEWS** is republished about once a year; production access
would be a scheduled batch job pulling BLS's annual public release into a warehouse table.
BLS's general Public Data API doesn't expose the full detailed occupation × geography ×
industry cross-tabulation used here, so batch file ingestion — not the API — is the realistic
path. The one genuinely live data source in a real product would be **user-submitted profile
data** (self-reported skills/education/interests) from the application's own database.

### What variables are present in the dataset (plain language)?

**From the occupation-description data:** the occupation's name and description; how
important a range of cognitive, physical, and sensory abilities are to the job and how much
of each is required; which knowledge areas the job draws on; core-to-every-job skills versus
skills that transfer across many occupations; associated software/technology tools; typical
education level and overall preparation tier (a five-level scale from minimal to extensive
preparation needed); day-to-day activities and work environment; personality/work-style fit;
a six-part interest profile (a well-established career-counseling framework); and which other
occupations are considered similar.

**From the labor-market data:** the geographic scope of the estimate (national, state, or
metro area); the industry covered; the occupation; how many people are employed in it;
typical pay, both hourly and annual, reported across the pay distribution (low end, middle,
high end) rather than as a single number; and reliability indicators showing how
statistically trustworthy each estimate is, since these come from a survey, not a census.

### What issues were present, how were they handled, what's their source, and how would a full pipeline address them?

**Missing data** is largely intentional, not accidental — agencies withhold specific
estimates when survey samples are too small to be reliable, or when reporting a wage would
risk identifying an individual; several O*NET flags are blank by design. Handled here by
treating these as meaningful categories and quantifying their extent per table rather than
filling them in. A production pipeline should keep this an explicit, monitored category —
never silently impute a wage that's missing because it's unreliable.

**Type mismatches on load** — O*NET's raw files load every column as text, and the wage
CSV uses comma-formatted numbers and suppression symbols pandas doesn't recognize by
default. One of these was serious: a suppression symbol specific to employment counts was
initially missed, which silently corrupted employment-size numbers for the entire dataset
until caught. Source: file-format artifacts from the publishing agencies, not flaws in the
underlying data. A production pipeline should run automated schema/sanity checks on every
refresh (values parse as numbers, key maximums fall in plausible ranges) rather than rely on
a person noticing a number looks too small.

**Skewed distributions** — pay and employment size are both heavily right-skewed by a small
number of genuinely very-high-paying or very-high-employment occupations, not by errors.
Confirmed the extreme values were legitimate, then applied a log transform, which brings
both much closer to symmetric. A production pipeline should apply that transform by default
anywhere these fields feed a model or visualization.

**Mismatched join keys** — the two datasets' occupation-coding systems don't line up
one-to-one; the skills dataset splits some occupations more finely than the wage dataset
reports them (about 8% of occupations collapse many-to-one). Source: the two agencies
maintain taxonomies at different levels of detail by design. Handled here by joining at the
shared level and explicitly measuring the collapse rate. A production pipeline should
maintain this as a versioned crosswalk table, since classification systems get revised
periodically and a hardcoded assumption would quietly break.

**Inconsistent granularity / duplicate-like rows** — the wage dataset stacks national,
state, and detailed-occupation rows together in one table; failing to filter to one
consistent level before aggregating would double-count. Source: an intentional, compact way
of publishing multiple aggregation levels in one file. Handled here by always filtering
explicitly before any calculation. A production pipeline should enforce this structurally
(separate tables, or a required filter parameter) rather than leave it as a step someone has
to remember.

### How do the variables relate to the project goal, and do patterns suggest they'll be useful?

The two datasets map directly onto the project's two halves: occupation-description
variables are the substance of matching users to occupations; wage/employment variables are
the substance of the labor-market analytics. Two findings support that they carry real
signal: the preparation-level variable tracks real, substantial pay differences (roughly
doubling from the lowest to a middle tier), suggesting it captures something genuine about
the labor market rather than an arbitrary label; and the interest-profile variable reflects
an established psychological framework and shows meaningful (if imbalanced) differentiation
across occupations rather than flat noise. One caution: a naive average-based summary of
ability requirements did *not* track preparation level cleanly even though preparation level
itself tracks pay well — a sign that not every variable is immediately useful in its rawest
form, and each proposed feature should be checked against a trusted outcome before assuming
it will help the matching model.

### How do the variables relate to each other, are there strong correlations, and how does that affect modeling?

Two strong-correlation findings, both pointing the same direction — don't feed near-duplicate
variables into the same model or similarity calculation. Within the occupation-description
data, the "importance" and "level required" ratings for the same ability move together
almost perfectly (r ≈ 0.96–0.98); they're measuring nearly the same thing. Within the wage
data, nearly every pay statistic is very highly correlated with every other one (mostly
above 0.9), while employment size and the reliability indicator are only weakly related to
pay and to each other, carrying genuinely separate information. Implication: collapse each
highly-correlated cluster to one representative measure rather than including all of them.
This matters more here than in a typical regression, because the core mechanism is a
similarity calculation — including several near-identical columns from one cluster silently
gives that cluster several times the influence of any other single feature in the match,
regardless of intent. Employment size and the reliability indicator, being largely
independent of pay, are safe to keep as their own separate signals.

---

## Summary of modeling implications

1. Use `LV` (not both `IM` and `LV`) for O*NET ability/knowledge/skill features — avoids redundant, correlated dimensions.
2. Keep RIASEC and per-ability vectors as continuous multi-dimensional features, not collapsed categoricals — preserves signal for underrepresented interest types and job-zone-differentiating abilities.
3. Log-transform `A_MEDIAN`/`TOT_EMP` before visualization or any magnitude-based use — both are heavily right-skewed in raw form.
4. Use `A_MEDIAN` as the single representative wage figure; don't feed multiple wage percentile columns as if independent.
5. Always filter OEWS to one `AREA_TYPE`/`O_GROUP`/`I_GROUP`/`OWN_CODE` combination before any aggregation or join — this is the single most consequential data-quality control in the whole pipeline.
6. Display wage as a range, not a point estimate, especially for Job Zone 4–5 recommendations, given the sharp increase in variance at higher preparation levels.
7. Disclose the many-to-one O*NET-to-OEWS join limitation in any write-up or UI that shows wage data next to a detailed occupation match.
