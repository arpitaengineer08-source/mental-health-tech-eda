"""
data_prep.py
------------
Single source of truth for cleaning the OSMI 2014 "Mental Health in Tech" survey.

The notebook and the Streamlit app both import from here, so the numbers you see
in the EDA are exactly the numbers the dashboard shows.
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Column groups used across the project
# --------------------------------------------------------------------------- #
SUPPORT_COLS = ["benefits", "care_options", "wellness_program", "seek_help", "anonymity"]
OPENNESS_COLS = ["coworkers", "supervisor", "mental_health_interview"]
COMPANY_SIZE_ORDER = ["1-5", "6-25", "26-100", "100-500", "500-1000", "More than 1000"]
LEAVE_ORDER = ["Very easy", "Somewhat easy", "Don't know", "Somewhat difficult", "Very difficult"]
INTERFERE_ORDER = ["Never", "Rarely", "Sometimes", "Often", "Not applicable"]
AGE_BINS = [17, 24, 30, 36, 45, 75]
AGE_LABELS = ["18-24", "25-30", "31-36", "37-45", "46+"]

_MALE = {
    "male", "m", "male-ish", "maile", "mal", "male (cis)", "make", "man", "msle",
    "mail", "malr", "cis man", "cis male", "male ", "guy (-ish) ^_^", "males",
    "ostensibly male, unsure what that really means", "something kinda male?",
    "male leaning androgynous", "maile ", "mle",
}
_FEMALE = {
    "female", "f", "woman", "femake", "female ", "cis female", "cis-female/femme",
    "female (cis)", "femail", "cis woman", "femme", "women",
}


def default_csv_path() -> str:
    """Resolve data/survey.csv relative to the project root, wherever it is run from."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "data", "survey.csv")


def clean_gender(value: str) -> str:
    """Collapse 49 free-text gender answers into Male / Female / Non-binary & other."""
    g = str(value).strip().lower()
    if g in _MALE:
        return "Male"
    if g in _FEMALE:
        return "Female"
    if "trans" in g or "queer" in g or "non-binary" in g or "nonbinary" in g:
        return "Non-binary & other"
    if g.startswith("m") and "fem" not in g:
        return "Male"
    if g.startswith("f") or g.startswith("w"):
        return "Female"
    return "Non-binary & other"


def load_raw(path: str | None = None) -> pd.DataFrame:
    """Read the survey exactly as distributed - no cleaning applied."""
    path = path or default_csv_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"survey.csv not found at {path}. Keep the CSV inside the data/ folder."
        )
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning pipeline.

    1. Drop the free-text `comments` column (87% empty, not analysable here).
    2. Keep only plausible ages (18-75). The raw file contains -1726 and 99999999999.
    3. Normalise Gender into three analysable buckets.
    4. Fill the meaningful nulls instead of dropping rows:
       - self_employed  -> "No"             (survey default when skipped)
       - work_interfere -> "Not applicable" (blank = "I have no condition")
       - state          -> "Not in US"
    5. Engineer: Age_Group, Employer_Support_Score, Openness_Score, Treated flag.
    """
    d = df.copy()

    d = d.drop(columns=[c for c in ["comments"] if c in d.columns])
    d["Timestamp"] = pd.to_datetime(d["Timestamp"], errors="coerce")

    d["Age"] = pd.to_numeric(d["Age"], errors="coerce")
    d = d[(d["Age"] >= 18) & (d["Age"] <= 75)].copy()

    d["Gender"] = d["Gender"].apply(clean_gender)
    d["self_employed"] = d["self_employed"].fillna("No")
    d["work_interfere"] = d["work_interfere"].fillna("Not applicable")
    d["state"] = d["state"].fillna("Not in US")

    # Trim stray whitespace in every remaining object column.
    for col in d.select_dtypes(include="object").columns:
        d[col] = d[col].str.strip()

    d["Age_Group"] = pd.cut(d["Age"], bins=AGE_BINS, labels=AGE_LABELS)
    d["Treated"] = (d["treatment"] == "Yes").astype(int)

    # How much mental-health support does the employer actually provide? (0-5)
    d["Employer_Support_Score"] = sum((d[c] == "Yes").astype(int) for c in SUPPORT_COLS)

    # How open is the respondent about mental health at work? (0-3)
    openness = (d["coworkers"].isin(["Yes", "Some of them"])).astype(int)
    openness += (d["supervisor"].isin(["Yes", "Some of them"])).astype(int)
    openness += (d["mental_health_interview"] == "Yes").astype(int)
    d["Openness_Score"] = openness

    d = d.drop_duplicates()
    return d.reset_index(drop=True)


def load_clean(path: str | None = None) -> pd.DataFrame:
    """Convenience: read + clean in one call."""
    return clean(load_raw(path))


def treatment_rate(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """% of respondents who sought treatment, grouped by a categorical column."""
    out = (
        df.groupby(by, observed=True)["Treated"]
        .agg(rate="mean", n="size")
        .reset_index()
        .sort_values("rate", ascending=False)
    )
    out["rate"] = (out["rate"] * 100).round(1)
    return out


def encode_for_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Ordinal-encode the survey answers so a correlation matrix becomes meaningful."""
    yes_no = {"Yes": 1, "No": 0, "Maybe": 0.5, "Don't know": 0.5, "Not sure": 0.5,
              "Some of them": 0.5}
    ordinal_maps = {
        "no_employees": {v: i for i, v in enumerate(COMPANY_SIZE_ORDER)},
        "leave": {"Very easy": 0, "Somewhat easy": 1, "Don't know": 2,
                  "Somewhat difficult": 3, "Very difficult": 4},
        "work_interfere": {"Not applicable": 0, "Never": 1, "Rarely": 2,
                           "Sometimes": 3, "Often": 4},
    }
    cols = [
        "Age", "family_history", "treatment", "work_interfere", "no_employees",
        "remote_work", "tech_company", "benefits", "care_options", "wellness_program",
        "seek_help", "anonymity", "leave", "mental_health_consequence",
        "phys_health_consequence", "coworkers", "supervisor", "mental_health_interview",
        "phys_health_interview", "mental_vs_physical", "obs_consequence",
        "Employer_Support_Score", "Openness_Score",
    ]
    enc = pd.DataFrame(index=df.index)
    for c in cols:
        if c in ordinal_maps:
            enc[c] = df[c].map(ordinal_maps[c])
        elif not pd.api.types.is_numeric_dtype(df[c]):
            enc[c] = df[c].map(yes_no)
        else:
            enc[c] = df[c]
    return enc.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
