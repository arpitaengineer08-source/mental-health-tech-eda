# Mental Health in Tech — EDA Capstone

Exploratory analysis of the **OSMI 2014 Mental Health in Tech Survey** (1,259 responses,
27 questions), delivered as a fully written-up Jupyter notebook plus an interactive
Streamlit dashboard.

**The headline:** 50.5% of respondents have sought mental-health treatment, and the strongest
employer-side lever is not what a company provides — it is whether employees *know* what exists.
Knowing your care options is associated with a 30-point difference in treatment rate; merely
having benefits, 16 points.

---

## Quick start

```bash
# 1. install (a virtual environment is recommended)
pip install -r requirements.txt

# 2. launch the dashboard
streamlit run app.py

# 3. open the analysis
jupyter notebook notebooks/Mental_Health_in_Tech_EDA.ipynb
```

The dashboard opens at <http://localhost:8501>. On Windows you can double-click `run.bat`;
on macOS or Linux run `./run.sh`.

Requires Python 3.9 or newer. Nothing else — no API keys, no database, no internet connection.

---

## What's inside

```
mental-health-tech-eda/
├── app.py                                   Streamlit dashboard (6 tabs, live filters)
├── src/data_prep.py                         All cleaning + feature engineering
├── notebooks/
│   └── Mental_Health_in_Tech_EDA.ipynb      Full EDA, 25 charts, already executed
├── data/survey.csv                          Raw survey, untouched
├── requirements.txt
├── run.sh / run.bat                         One-click launch
└── .streamlit/config.toml                   Theme
```

The notebook and the dashboard both import `src/data_prep.py`, so a number can never differ
between the report and the app. Change the cleaning in one place and both update.

---

## The analysis in six findings

1. **Half the workforce.** 50.5% have sought treatment — 632 people out of 1,251. Mental illness
   in tech is not an edge case.
2. **Treatment is reactive.** It tracks work interference almost perfectly (r = 0.65), rising from
   14% among people whose condition never affects work to 85% among those it affects often.
   People wait until the job is at stake.
3. **Awareness beats provision.** Knowing your care options: 69% treated vs 39% for "not sure".
   Having benefits: 64% vs 48%. The most common answer across all five support questions is
   "I don't know".
4. **Scale doesn't help.** Large companies provide far more support on paper (avg score 2.3 of 5
   vs 0.8 at small firms) yet see barely higher treatment rates. The spend leaks between the
   benefits page and the employee.
5. **Stigma survives policy.** 80% would not raise mental health in a job interview, against 40%
   for a physical condition. Only 27% believe their employer treats the two equally.
6. **Two under-treated groups.** Men (46% vs 69% for women) and people with no family history
   (35% vs 74%). Both are large, and neither is plausibly healthier.

### What the data does *not* support

Remote work changes almost nothing (53% vs 50%), and willingness to talk at work barely predicts
treatment (47–58% across the openness scale). Both are popular assumptions with no backing here.

---

## Data cleaning decisions

| Problem | Decision | Why |
|---|---|---|
| `Age` contains −1726 and 99999999999 | Keep 18–75 only (8 rows dropped) | Impossible values destroy every mean and axis |
| `Gender` has 49 free-text spellings | Rule-based collapse to 3 buckets | Reproducible, not hand-mapped |
| `work_interfere` blank for 264 people | Fill as **"Not applicable"** | Blank means "no condition", not missing. Dropping these rows would inflate the headline rate from 50% to ~62% |
| `comments` 87% empty | Drop | Free text, not analysable here |
| `state` blank for 41% | "Not in US" | The question only applies to US respondents |
| `self_employed` blank for 18 | "No" | Survey default when skipped |

**Engineered features:** `Employer_Support_Score` (0–5, how many of benefits / care options /
wellness programme / seek-help resources / anonymity an employer provides) and `Openness_Score`
(0–3, how many of coworkers / supervisor / interviewer the respondent would tell).

---

## Dashboard tabs

| Tab | What it does |
|---|---|
| **Overview** | The headline rate, the severity curve, and a ranked correlation chart |
| **Who answered** | Age, gender, country, family history — and the treatment gap in each |
| **The workplace** | What employers provide, the support-score gradient, company size, leave policy |
| **Stigma** | Mental vs physical health, side by side, on the same respondents |
| **Deep dive** | Build your own cross-tab — any two questions, treatment rate in every cell |
| **The data** | Cleaning audit trail, filtered table, CSV download |

Sidebar filters (country, gender, age, company size, remote work) apply to every chart, and the
app warns you when a filter combination leaves too few people to read anything into.

---

## Limitations

Self-reported and self-selected, from 2014. The sample is 79% male and 60% American, and only
seven countries clear 20 responses. Every relationship shown is **correlational** — people already
in treatment have a reason to learn their care options, so causality runs in both directions.
This is enough to rank priorities and justify a pilot. It is not enough to promise an outcome.

---

## Source

Open Sourcing Mental Illness (OSMI), *Mental Health in Tech Survey*, 2014.
Licensed CC BY-SA 4.0. <https://osmihelp.org>
