"""
S.CleanRawData.py
Data stage, step 3: remove repeated records from the input files in
raw/<id>/ (both datasets) before the pipeline is run. Run it after
S.GetZenodoData.py and S.ConvertClinicalData.py --to-raw, and before InVivo.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each participant and each of UoMGlucose, UoMNutrition, UoMBolus and
    UoMBasal:
        1. Blank rows are dropped (left by spreadsheet editing).
        2. Exact copies (same time stamp and same values) are dropped,
           keeping one.
        3. Glucose only: when the same time stamp carries different values,
           the first record in the file is kept and the others are dropped.
        4. Bolus only: a bolus with the same dose as the previous one and
           recorded within REPEAT_MINUTES (15) of it is taken as a second
           record of the same bolus and dropped. Records are paired in time
           order, so a dropped record is never used to drop the next one.
    Rows are otherwise left in their original order and format; nothing is
    rounded or re-sorted.

Inputs
    globals.raw_dir
    raw/<id>/UoM{Glucose,Nutrition,Bolus,Basal}<id>.csv

Outputs
    raw/<id>/UoM*.csv                      cleaned files (same names)
    raw/<id>/original/UoM*.csv             untouched originals
    raw/<id>/original/cleaned_md5.json     checksum of each cleaned file
    raw/<id>/original/cleaning_log.csv     rows removed, by rule

Notes
    - The script always cleans from raw/<id>/original/, so running it again
      gives the same result. A file in raw/<id>/ whose checksum is not the
      one recorded in cleaned_md5.json is taken as new input (for example,
      written again by S.GetZenodoData.py) and becomes the new original.
    - "First record in the file" (rule 3) follows the order of the file, not
      the time order.
    - Bolus records whose time stamp cannot be read are never treated as
      repeated.
    - In 2304 every bolus appears twice a few minutes apart; this rule halves
      its daily bolus (54.08 -> 27.04 U/day).

Usage (from the data folder, with the project root on PYTHONPATH)
    python S.CleanRawData.py
"""

import hashlib
import json
import os
import shutil

import pandas as pd

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
# RAW: the raw/ folder (raw_dir('x') without its last part).
RAW = os.path.dirname(globals.raw_dir("x").rstrip("/"))
KINDS = ["Glucose", "Nutrition", "Bolus", "Basal"]
REPEAT_MINUTES = 15


# -----------------------------------------------------------#
# Helpers
# -----------------------------------------------------------#
def repeated_boluses(d):
    """Index of the bolus records that repeat the previous bolus (same dose,
    within REPEAT_MINUTES), pairing records in time order."""
    # Time stamp and dose of each record; records are visited in time order
    # (stable sort keeps the file order for equal times; unreadable times are
    # left out).
    ts = pd.to_datetime(d["bolus_ts"].str.strip(), format="%d/%m/%Y %H:%M", errors="coerce")
    dose = pd.to_numeric(d["bolus_dose"], errors="coerce")
    order = ts.dropna().sort_values(kind="stable").index
    drop, prev = [], None
    for i in order:
        # Same dose as the previous record and within REPEAT_MINUTES: repeated.
        if (prev is not None and dose[i] == dose[prev]
                and (ts[i] - ts[prev]).total_seconds() <= REPEAT_MINUTES * 60):
            drop.append(i)
            prev = None                  # the pair is closed
        else:
            prev = i
    return pd.Series(d.index.isin(drop), index=d.index)

def md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# -----------------------------------------------------------#
# Main
# -----------------------------------------------------------#
summary = []
# Each participant folder in raw/.
for pid in sorted(d for d in os.listdir(RAW) if os.path.isdir(os.path.join(RAW, d))):
    folder = os.path.join(RAW, pid)
    # original/: the untouched files, the checksums and the log.
    keep_dir = os.path.join(folder, "original")
    os.makedirs(keep_dir, exist_ok=True)
    log = []
    stamp_file = os.path.join(keep_dir, "cleaned_md5.json")
    # stamps: name -> MD5 of the cleaned file written last time.
    stamps = json.load(open(stamp_file, encoding="utf-8")) if os.path.isfile(stamp_file) else {}
    for kind in KINDS:
        name = f"UoM{kind}{pid}.csv"
        cur, orig = os.path.join(folder, name), os.path.join(keep_dir, name)
        # A file whose checksum is not the one recorded after cleaning is new input.
        if os.path.isfile(cur) and md5(cur) != stamps.get(name):
            shutil.copy2(cur, orig)                     # new input: it becomes the original
        # No original (the file never existed for this participant): nothing to do.
        if not os.path.isfile(orig):
            continue
        # Always clean from the original, read as text so nothing is reformatted.
        d = pd.read_csv(orig, dtype=str)
        n0 = len(d)
        # Rule 1: blank rows.
        # A row is blank if every cell is empty or only spaces.
        blank = ~d.apply(lambda s: s.fillna("").str.strip() != "").any(axis=1)
        d = d[~blank]
        # Rule 2: exact copies.
        exact = d.duplicated(keep="first")
        d = d[~exact]
        conflict = pd.Series(False, index=d.index)
        # Rule 3 (glucose): same time stamp, different value -> keep the first.
        if kind == "Glucose":
            # The time-stamp column is the one whose name ends in _ts.
            tcol = next(c for c in d.columns if c.strip().endswith("_ts"))
            conflict = d[tcol].str.strip().duplicated(keep="first")
            d = d[~conflict]
        repeated = pd.Series(False, index=d.index)
        # Rule 4 (bolus): same dose repeated within REPEAT_MINUTES.
        if kind == "Bolus":
            repeated = repeated_boluses(d)
            d = d[~repeated]
        # Overwrite the file in raw/<id>/ with the cleaned version.
        d.to_csv(cur, index=False)
        stamps[name] = md5(cur)                         # this file is now the cleaned version
        log.append({"file": name, "rows_before": n0, "blank": int(blank.sum()),
                    "exact_copies": int(exact.sum()), "conflicting_glucose": int(conflict.sum()),
                    "repeated_bolus": int(repeated.sum()),
                    "rows_after": len(d)})
    # Save the checksums and the log of this participant.
    if log:
        json.dump(stamps, open(stamp_file, "w", encoding="utf-8"), indent=1)
        pd.DataFrame(log).to_csv(os.path.join(keep_dir, "cleaning_log.csv"), index=False)
        for r in log:
            removed = r["rows_before"] - r["rows_after"]
            if removed:
                summary.append(f"{pid:7} {r['file']:26} -{removed:6}  (blank {r['blank']}, "
                               f"exact copies {r['exact_copies']}, conflicting {r['conflicting_glucose']}, "
                               f"repeated bolus {r['repeated_bolus']})")

# One line per file with rows removed.
print("\n".join(summary) if summary else "Nothing to remove.")
print("\nOriginal files kept in raw/<id>/original/; details in cleaning_log.csv.")
