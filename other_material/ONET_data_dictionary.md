# O*NET 30.3 Database — Data Dictionary

Source: O*NET Resource Center, Database version 30.3, tab-separated `.txt` files
(directory: `db_30_3_text/`). 45 data files + `Read Me.txt`.

## Shared / recurring fields

These fields appear across most files and carry the same meaning everywhere:

| Field | Meaning |
|---|---|
| `O*NET-SOC Code` | Primary occupation identifier (SOC code + O*NET detail suffix, e.g. `15-1252.00`). Joins to `Occupation Data.txt`. |
| `Element ID` | Identifier for a Content Model element (ability, skill, knowledge area, work activity, etc.). Joins to `Content Model Reference.txt`. |
| `Element Name` | Text label for the `Element ID`. |
| `Scale ID` | Code for the rating scale used (e.g. `IM`=Importance, `LV`=Level). Joins to `Scales Reference.txt`. |
| `Data Value` | The numeric rating/score on the given `Scale ID`. |
| `N` | Number of survey respondents underlying the estimate. |
| `Standard Error` | Standard error of `Data Value`. |
| `Lower CI Bound` / `Upper CI Bound` | 95% confidence interval around `Data Value`. |
| `Recommend Suppress` | `Y`/`N` flag — whether O*NET recommends suppressing the estimate due to reliability concerns. |
| `Not Relevant` | `Y`/`N`/blank — whether respondents rated the element as not relevant to the occupation. |
| `Date` | Month/year the data was last updated (`MM/YYYY`). |
| `Domain Source` | Source of the data (e.g. `Incumbent`, `Occupational Expert`, `Analyst`). |

Most "descriptor" tables share the shape: one row per `(O*NET-SOC Code, Element ID, Scale ID)`.

---

## Identifiers, predictors, and recommendation role

**Project goal:** a recommendation system that matches users to occupations based on
skills/education/interests, plus labor-market analytics for the matched occupations
(joined from `OEWS_data_dictionary.md`). This isn't a supervised-learning target/label
problem — it's a **similarity-matching** problem, so "predictors" here means "occupation
profile features to compare a user's self-reported profile against," not features feeding
a regression/classifier.

| Role | Tables / fields |
|---|---|
| **Primary identifier** | `O*NET-SOC Code` — the join key across every O*NET table, and the key used to attach OEWS wage/employment data. **Format gotcha:** O*NET-SOC codes carry a 2-digit detail suffix (e.g. `15-1252.00`, `15-1252.01`) that OEWS's `OCC_CODE` does not (`15-1252`, no suffix). Multiple O*NET-SOC codes can collapse onto one OEWS `OCC_CODE` — strip the suffix (`code[:7]`) to join, and expect a many-to-one relationship when you do. |
| **Occupation profile features (the "predictors" for matching)** | `Abilities.txt`, `Knowledge.txt`, `Essential Skills.txt`, `Transferable Skills.txt`, `Software Skills.txt` (filter to one `Scale ID`, typically `IM` or `LV`, and pivot `Element Name` → columns to build a per-occupation feature vector), `Education.txt` / `Job Zones.txt` (required education/preparation level), `Career Interest Types.txt` (RIASEC/Holland code vector — directly matchable against a user's self-reported interest profile), `Specific Interest Areas.txt` (finer-grained interests), `Work Activities.txt`, `Work Context.txt`, `Work Styles.txt` (optional secondary features — working conditions/personality fit). |
| **User-input analogue** | For the recommender to compare a user against these tables, user-collected skills/education/interests need to be encoded on the **same scale and element set** as the O*NET tables above (e.g. a user's self-rated interest in "Investigative" activities maps to `Career Interest Types.txt`'s RIASEC categories). This mapping is a design decision for the intake form, not something derivable from the data alone. |
| **Occupation metadata (for display, not matching)** | `Occupation Data.txt` (`Title`, `Description`), `Job Titles.txt`, `Sample of Reported Titles.txt` — human-readable labels to show alongside a recommendation, not feature inputs. |
| **Candidate evaluation / ground truth** | `Related Occupations.txt` — BLS/O*NET's own occupation-similarity links. Useful as a sanity check or evaluation set: if your recommender's nearest-neighbor results for an occupation don't loosely agree with its `Related Occupations.txt` entries, that's worth investigating. |
| **Supporting reference (interpret other tables, not features themselves)** | `Content Model Reference.txt`, `Scales Reference.txt`, `Job Zone Reference.txt`, and the `*Categories.txt` / `Level Scale Anchors.txt` lookup tables — needed to decode `Element ID`/`Scale ID`/`Category` codes, but shouldn't be joined into a feature vector directly. |
| **Not used for matching** | `Task Statements.txt`, `Task Ratings.txt`, `Emerging Tasks.txt`, `Tasks to DWAs.txt`, `GWAs to IWAs*.txt`, `Occupation Level Metadata.txt`, `Survey Booklet Locations.txt` — internal O*NET survey/taxonomy machinery, not relevant to a skills/education/interest matcher. Could be reconsidered later if you add task-text similarity (e.g. embedding `Task` descriptions) as a feature. |

**No single target variable** — the "target" is a ranked similarity/relevance score between
a user profile and an occupation profile, produced by whatever matching method you choose
(e.g. cosine similarity over the feature vector above, or a learned ranking model). If the
project later adds a supervised component (e.g. predicting user-reported satisfaction with a
recommendation), that label would come from user feedback data you collect, not from O*NET.

---

## 1. Core occupation reference

### Occupation Data.txt (1,016 rows)
Master list of O*NET-SOC occupations — one row per occupation.
| Column | Description |
|---|---|
| `O*NET-SOC Code` | Occupation identifier (primary key). |
| `Title` | Occupation title. |
| `Description` | Narrative description of the occupation. |

### Occupation Level Metadata.txt (32,202 rows)
Survey administration metadata (response rates, sample composition) per occupation.
| Column | Description |
|---|---|
| `O*NET-SOC Code` | Occupation identifier. |
| `Item` | Metadata item name (e.g. establishment/employee response rate). |
| `Response` | Response category/label. |
| `N` | Count for the item/response. |
| `Percent` | Percentage for the item/response. |
| `Date` | Update date. |

### Job Titles.txt (57,543 rows)
Alternate/official job titles mapped to occupations.
| Column | Description |
|---|---|
| `O*NET-SOC Code` | Occupation identifier. |
| `Job Title` | Title text. |
| `Short Title` | Abbreviated title, if any. |
| `Source(s)` | Origin of the title (e.g. BLS, O*NET analyst). |

### Sample of Reported Titles.txt (7,953 rows)
Job titles reported by incumbents/employers during data collection.
| Column | Description |
|---|---|
| `O*NET-SOC Code` | Occupation identifier. |
| `Reported Job Title` | Title as reported. |
| `Shown in My Next Move` | `Y`/`N` — whether displayed on the My Next Move consumer site. |

---

## 2. Content model / lookup (reference) tables

These are dimension tables that other files' `Element ID` / `Scale ID` columns join against.

### Content Model Reference.txt (3,006 rows)
Master list of all Content Model elements (abilities, skills, knowledge, work activities, etc.).
| Column | Description |
|---|---|
| `Element ID` | Element identifier (primary key). |
| `Element Name` | Element label. |
| `Description` | Definition of the element. |

### Scales Reference.txt (32 rows)
Defines every rating scale used throughout the database.
| Column | Description |
|---|---|
| `Scale ID` | Scale identifier (primary key), e.g. `IM`, `LV`, `CTP`. |
| `Scale Name` | Full scale name (e.g. "Importance", "Level"). |
| `Minimum` | Minimum possible value. |
| `Maximum` | Maximum possible value. |

### Job Zone Reference.txt (4 rows)
Defines the 5 Job Zones (preparation levels required for an occupation).
| Column | Description |
|---|---|
| `Job Zone` | Job Zone number (1–5). |
| `Name` | Zone name (e.g. "Job Zone Two: Some Preparation Needed"). |
| `Experience` | Typical experience required. |
| `Education` | Typical education required. |
| `Job Training` | Typical on-the-job training required. |
| `Examples` | Example occupations. |
| `SVP Range` | Specific Vocational Preparation range. |

### Education Categories.txt (12 rows)
Response categories for the `Education.txt` survey item.
| Column | Description |
|---|---|
| `Element ID` | Related element (education level item). |
| `Element Name` | Element label. |
| `Scale ID` | Scale this category set applies to. |
| `Category` | Category code. |
| `Category Description` | Text label (e.g. "Bachelor's degree"). |

### Task Categories.txt (7 rows)
Response categories used in `Task Ratings.txt` (e.g. frequency, importance bins).
| Column | Description |
|---|---|
| `Scale ID` | Related scale. |
| `Category` | Category code. |
| `Category Description` | Text label. |

### Training and Experience Categories.txt (29 rows)
Response categories for the `Training and Experience.txt` items.
| Column | Description |
|---|---|
| `Element ID` | Related element. |
| `Element Name` | Element label. |
| `Scale ID` | Related scale. |
| `Category` | Category code. |
| `Category Description` | Text label. |

### Work Context Categories.txt (281 rows)
Response categories for categorical `Work Context.txt` items.
| Column | Description |
|---|---|
| `Element ID` | Related element. |
| `Element Name` | Element label. |
| `Scale ID` | Related scale. |
| `Category` | Category code. |
| `Category Description` | Text label. |

### Level Scale Anchors.txt (483 rows)
Behavioral anchor descriptions for each point on "Level" (`LV`) scales.
| Column | Description |
|---|---|
| `Element ID` | Related element. |
| `Element Name` | Element label. |
| `Scale ID` | Scale (typically `LV`). |
| `Anchor Value` | Numeric anchor point on the scale. |
| `Anchor Description` | Behavioral description at that anchor point. |

### Survey Booklet Locations.txt (211 rows)
Maps elements to their location/item number in the source survey booklets.
| Column | Description |
|---|---|
| `Element ID` | Related element. |
| `Element Name` | Element label. |
| `Survey Item Number` | Item number in the survey instrument. |
| `Scale ID` | Related scale. |

---

## 3. Occupation × element descriptor (rating) tables

One row per `(O*NET-SOC Code, Element ID, Scale ID)` unless noted. These are the core
"how much does this occupation require X" tables.

| File | Rows | Notes |
|---|---|---|
| Abilities.txt | 92,976 | Ratings on the 52 O*NET abilities. Columns: standard descriptor set + `Recommend Suppress`, `Not Relevant`. |
| Knowledge.txt | 59,004 | Ratings on the 33 knowledge areas. Same column set as Abilities. |
| Work Activities.txt | 73,308 | Ratings on generalized work activities (GWAs). Same column set as Abilities. |
| Work Context.txt | 297,676 | Ratings on work context items (physical/social/structural job conditions); includes categorical items via `Category`. Largest file in the database. |
| Work Styles.txt | 37,422 | Ratings on personality/work style constructs. Columns: `O*NET-SOC Code, Element ID, Element Name, Scale ID, Data Value, Date, Domain Source` (no `N`/CI columns). |
| Education.txt | 11,100 | Distribution of education levels reported for the occupation, via `Category`. Includes `N`/CI columns. |
| Training and Experience.txt | 26,025 | Related training/experience requirements, via `Category`. |
| Job Zones.txt | 923 | One row per occupation: assigned `Job Zone` (1–5). Columns: `O*NET-SOC Code, Job Zone, Date, Domain Source`. |
| Career Interest Types.txt | 8,307 | RIASEC interest profile ratings (Holland codes) per occupation. No `N`/CI columns. |
| Specific Interest Areas.txt | 73,062 | Finer-grained interest area ratings per occupation. No `N`/CI columns. |
| Essential Skills.txt | 17,880 | Ratings on "essential" (core) skills; full descriptor column set incl. `N`, CI bounds, `Not Relevant`. |
| Transferable Skills.txt | 44,700 | Ratings on transferable (cross-occupation) skills; same column set as Essential Skills. |
| Software Skills.txt | 31,821 | Software/technology tools associated with the occupation (not a rating scale table). Columns: `O*NET-SOC Code, Workplace Example, Element ID, Element Name, Hot Technology, In Demand`. `Hot Technology`/`In Demand` are `Y`/blank flags. |

---

## 4. Task-related tables

### Task Statements.txt (18,796 rows)
The task text library.
| Column | Description |
|---|---|
| `O*NET-SOC Code` | Occupation identifier. |
| `Task ID` | Task identifier (primary key with occupation). |
| `Task` | Task statement text. |
| `Task Type` | `Core` or `Supplemental`. |
| `Incumbents Responding` | Count of incumbents who rated this task. |
| `Date` | Update date. |
| `Domain Source` | Data source. |

### Task Ratings.txt (161,559 rows)
Importance/frequency/relevance ratings for each task.
| Column | Description |
|---|---|
| `O*NET-SOC Code`, `Task ID` | Join to Task Statements.txt. |
| `Scale ID` | Rating scale (e.g. `IM`, `RT`, `FT`). |
| `Category` | Response category (for frequency-type scales). |
| `Data Value`, `N`, `Standard Error`, `Lower/Upper CI Bound`, `Recommend Suppress` | Standard descriptor fields. |
| `Date`, `Domain Source` | Standard metadata fields. |

### Emerging Tasks.txt (328 rows)
New/candidate tasks identified for an occupation, pending full rating.
| Column | Description |
|---|---|
| `O*NET-SOC Code` | Occupation identifier. |
| `Task` | New task statement text. |
| `Category` | Status/category of the emerging task. |
| `Original Task ID` / `Original Task` | Related existing task, if applicable. |
| `Date`, `Domain Source` | Standard metadata fields. |

### Tasks to DWAs.txt (23,850 rows)
Links occupation-specific tasks to generalized Detailed Work Activities (DWAs).
| Column | Description |
|---|---|
| `O*NET-SOC Code`, `Task ID` | Join to Task Statements.txt. |
| `DWA Element ID` | Linked DWA identifier. |
| `Date`, `Domain Source` | Standard metadata fields. |

### GWAs to IWAs.txt (332 rows)
Work activity taxonomy: Generalized Work Activities (GWAs) → Intermediate Work Activities (IWAs).
| Column | Description |
|---|---|
| `GWA Element ID` | GWA identifier (from Content Model Reference). |
| `IWA Element ID` | IWA identifier. |
| `IWA Element Name` | IWA label. |

### GWAs to IWAs to DWAs.txt (2,087 rows)
Full work-activity taxonomy chain: GWA → IWA → DWA.
| Column | Description |
|---|---|
| `GWA Element ID` | Generalized Work Activity identifier. |
| `IWA Element ID` | Intermediate Work Activity identifier. |
| `DWA Element ID` | Detailed Work Activity identifier. |
| `DWA Element Name` | DWA label. |

---

## 5. Crosswalk / relationship tables

Element-to-element mappings (not occupation-specific) showing which descriptors relate
to which work activities/contexts.

| File | Rows | Maps |
|---|---|---|
| Abilities to Work Activities.txt | 381 | Ability ↔ Work Activity |
| Abilities to Work Context.txt | 139 | Ability ↔ Work Context |
| Essential Skills to Work Activities.txt | 110 | Essential Skill ↔ Work Activity |
| Essential Skills to Work Context.txt | 39 | Essential Skill ↔ Work Context |
| Transferable Skills to Work Activities.txt | 122 | Transferable Skill ↔ Work Activity |
| Transferable Skills to Work Context.txt | 57 | Transferable Skill ↔ Work Context |
| Work Styles to Work Activities.txt | 303 | Work Style ↔ Work Activity |
| Work Styles to Work Context.txt | 266 | Work Style ↔ Work Context |
| Specific Interest Areas to Career Interest Types.txt | 53 | Specific Interest Area ↔ RIASEC Career Interest Type |

Each has columns `<Domain A> Element ID`, `<Domain A> Element Name`, `<Domain B> Element ID`,
`<Domain B> Element Name` (or just IDs where noted above).

### Career Interest Type Keywords.txt (75 rows)
Keywords associated with each RIASEC interest type (used for search/matching tools).
| Column | Description |
|---|---|
| `Element ID`, `Element Name` | Interest type. |
| `Keyword` | Associated keyword text. |
| `Keyword Type` | Category of keyword. |

### Interests Illustrative Activities.txt (188 rows)
Example activities illustrating each interest type.
| Column | Description |
|---|---|
| `Element ID`, `Element Name` | Interest type. |
| `Interest Type` | RIASEC letter code. |
| `Activity` | Example activity text. |

### Interests Illustrative Occupations.txt (186 rows)
Example occupations illustrating each interest type.
| Column | Description |
|---|---|
| `Element ID`, `Element Name` | Interest type. |
| `Interest Type` | RIASEC letter code. |
| `O*NET-SOC Code` | Example occupation. |

---

## 6. Occupation relationships

### Related Occupations.txt (18,460 rows)
Occupation-to-occupation similarity links (used for career exploration tools).
| Column | Description |
|---|---|
| `O*NET-SOC Code` | Source occupation. |
| `Related O*NET-SOC Code` | Related occupation. |
| `Relatedness Tier` | Strength tier of the relationship (e.g. "Primary-Short", "Supplemental"). |
| `Index` | Ranking/order within the tier. |

---

## Notes

- `Read Me.txt` is plain-text release documentation, not a tabular data file — excluded above.
- Row counts are total lines in each file including the header row, from the raw `.txt` files in `db_30_3_text/`.
- Several tables use `Not Relevant` and `Recommend Suppress` flags — filter or handle these
  explicitly before aggregating `Data Value`, since suppressed/not-relevant rows can skew analysis.
- `Element ID` values are shared across *related* descriptor domains (e.g. an Essential Skill and
  a Transferable Skill can reference the same underlying skill concept) — always join back to
  `Content Model Reference.txt` to resolve the human-readable definition.
