"""
S.CheckRawData.py
Data stage, step 4 (check, optional): format and range checks of the input
files of every participant in raw/<id>/ (both datasets). Nothing is changed.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each of UoMGlucose, UoMNutrition, UoMBolus and UoMBasal it reports:
        rows            number of rows (blank rows ignored)
        bad_ts          time stamps that cannot be read as dd/mm/yyyy hh:mm
        bad_value       values that are missing or not numeric
        duplicates      repeated time stamps
        unordered       time stamps earlier than the previous row
        negative        values below 0
        out_of_range    glucose outside 2.2-22.2 mmol/L (usual CGM reporting
                        range), meals above 300 g, boluses above 30 U, basal
                        above 5 U/h
        first, last     first and last date
        step_min        median interval between readings, in minutes
                        (glucose only)
    and lists the files with anything to look at.

Inputs
    globals.raw_dir, globals.path4
    raw/<id>/UoM{Glucose,Nutrition,Bolus,Basal}<id>.csv

Output
    <path4>/RawDataCheck.csv   one row per participant and file

Notes
    - Glucose is assumed to be in mmol/L, as in both datasets.
    - The time column is the one ending in "_ts"; a file without it, or
      without the expected value column, is reported as "columns not
      recognised".
    - The insulin_kind column of the clinical basal files is not checked.
    - Run it after S.CleanRawData.py to confirm the cleaning; run before, it
      shows what the cleaning will remove (duplicates).

Usage (from the data folder, with the project root on PYTHONPATH)
    python S.CheckRawData.py
"""

import glob
import os

import pandas as pd

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
RAW = os.path.dirname(globals.raw_dir("x").rstrip("/"))
FILES = {  # kind: (value column, upper limit)
    "Glucose": ("value", 22.2),
    "Nutrition": ("carbs_g", 300),
    "Bolus": ("bolus_dose", 30),
    "Basal": ("basal_dose", 5),
}
LOW_GLUCOSE = 2.2

# -----------------------------------------------------------#
# Checks, participant by participant
# -----------------------------------------------------------#
rows = []
for pid in sorted(d for d in os.listdir(RAW) if os.path.isdir(os.path.join(RAW, d))):
    for kind, (vcol, upper) in FILES.items():
        f = os.path.join(RAW, pid, f"UoM{kind}{pid}.csv")
        if not os.path.isfile(f):
            rows.append({"ID": pid, "file": kind, "problem": "file missing"})
            continue
        d = pd.read_csv(f, dtype=str)
        d.columns = [c.strip() for c in d.columns]
        d = d[d.apply(lambda s: s.fillna("").str.strip() != "").any(axis=1)]   # blank rows
        tcol = next((c for c in d.columns if c.endswith("_ts")), None)
        if tcol is None or vcol not in d.columns:
            rows.append({"ID": pid, "file": kind, "rows": len(d),
                         "problem": f"columns not recognised: {list(d.columns)}"})
            continue
        ts = pd.to_datetime(d[tcol].str.strip(), format="%d/%m/%Y %H:%M", errors="coerce")
        v = pd.to_numeric(d[vcol], errors="coerce")
        out = (v > upper) | ((v < LOW_GLUCOSE) if kind == "Glucose" else False)
        r = {"ID": pid, "file": kind, "rows": len(d),
             "bad_ts": int(ts.isna().sum()),
             "bad_value": int(v.isna().sum()),
             "duplicates": int(ts.dropna().duplicated().sum()),
             "unordered": int((ts.diff().dt.total_seconds() < 0).sum()),
             "negative": int((v < 0).sum()),
             "out_of_range": int(out.sum()),
             "first": ts.min().date() if ts.notna().any() else None,
             "last": ts.max().date() if ts.notna().any() else None}
        if kind == "Glucose" and ts.notna().sum() > 1:
            r["step_min"] = ts.dropna().sort_values().diff().dt.total_seconds().median() / 60
        flags = [k for k in ("bad_ts", "bad_value", "duplicates", "unordered", "negative", "out_of_range") if r[k]]
        r["problem"] = ", ".join(flags) if flags else ""
        rows.append(r)

# -----------------------------------------------------------#
# Saving and summary
# -----------------------------------------------------------#
t = pd.DataFrame(rows)
t.to_csv(os.path.join(globals.path4, "RawDataCheck.csv"), index=False)
pd.set_option("display.width", 200)
print(t.to_string(index=False))
issues = t[t.problem.fillna("") != ""]
print(f"\n{len(issues)} of {len(t)} files with something to look at." if len(issues)
      else f"\nNo problems found in {len(t)} files.")
