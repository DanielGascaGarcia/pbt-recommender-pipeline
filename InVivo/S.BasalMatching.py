"""
S.BasalMatching.py
InVivo, matching: daily basal and bolus insulin of every participant and the
virtual patient of Py-mgipsim it is matched to (Table 1 of the manuscript).

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Daily basal (U/day) = median of the daily totals of basal insulin.
       Daily total: step integration of the basal rate (each reading holds
       until the next one; the first also covers 00:00 to the first reading,
       the last up to 24:00). This gives the same result whether the file has
       a reading every few minutes or only the change points of a programmed
       profile. For insulin_kind == "L" (long-acting injections) the daily
       total is the sum of the doses of the day.
    2. Match: the virtual patient whose basal rate x 24 is closest to the
       daily basal of the participant.
    3. Daily bolus (U/day) = median of the daily sums of bolus_dose, over the
       days with at least one bolus record (a day without records is missing
       data, not 0 U). Descriptive only.

Inputs
    globals.PAIRS_FILE, globals.raw_dir, globals.path (Py-mgipsim patients)
    raw/<id>/UoMBasal<id>.csv, raw/<id>/UoMBolus<id>.csv
    Patient_<n>.json of Py-mgipsim, or the table VIRTUAL_BASAL_U_H

Output
    <path4>/Table1_basal_matching.csv
        ID, Regime, Basal_U_day (median), Mean_U_day, SD_U_day, Days,
        Partial_days, Bolus_U_day (median), Bolus_mean_U_day, Bolus_days,
        Virtual_selected, Virtual_basal_U_h, Virtual_in_pairs, Agrees

Notes
    - The whole basal file is used, not only the 45 analysis days: in some
      participants the basal records do not cover the same dates as the
      glucose records.
    - The first reading of a day is assumed to hold from 00:00, i.e. the
      rate at midnight is taken as the first rate of the day, not the last
      rate of the previous day.
    - Partial days (fewer rows than half the usual count) are counted, not
      excluded; the median keeps them from pulling the result.
    - The regime (pump or injections) is read from the first row only.
    - Repeated time stamps keep the first record.
    - The virtual basal rates are read from the Py-mgipsim files when all 20
      can be read; otherwise the values written in the script are used.
    - The match is approximate by design: only total daily basal is used.
      The script reports whether the rule agrees with pairs.csv; pairs.csv
      decides which virtual patient each participant uses.

Usage (from the InVivo folder, with the project root on PYTHONPATH)
    python S.BasalMatching.py             all participants in pairs.csv
    python S.BasalMatching.py 2301 2304   only these
"""

import csv
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
PAIRS_FILE = globals.PAIRS_FILE
PARTIAL_FRACTION = 0.5    # a day with fewer rows than half the usual count is partial

# Basal rate (U/h) of the 20 virtual patients of Py-mgipsim, used when their
# files cannot be read (Table 2 of the manuscript).
VIRTUAL_BASAL_U_H = {1: 1.14, 2: 1.45, 3: 1.25, 4: 0.93, 5: 0.77, 6: 0.59, 7: 2.00,
                     8: 0.73, 9: 0.98, 10: 0.46, 11: 1.77, 12: 1.09, 13: 1.26,
                     14: 0.51, 15: 1.19, 16: 0.39, 17: 1.50, 18: 1.56, 19: 1.15,
                     20: 1.00}


# -----------------------------------------------------------#
# Helpers
# -----------------------------------------------------------#
def load_pairs():
    with open(PAIRS_FILE, newline="", encoding="utf-8") as f:
        rows = (l for l in f if l.strip() and not l.lstrip().startswith("#"))
        return {r["id"].strip(): r["id2"].strip() for r in csv.DictReader(rows)}


def virtual_basal():
    """{patient number: basal U/h}, from the Py-mgipsim files when available."""
    out = {}
    for f in glob.glob(os.path.join(globals.path, "Patient_*.json")):
        try:
            info = json.load(open(f, encoding="utf-8"))["demographic_info"]
            key = next(k for k in info if "basal" in k.lower() and "total" not in k.lower())
            v = info[key]
            out[int(os.path.basename(f)[8:-5])] = float(v[0] if isinstance(v, list) else v)
        except (KeyError, StopIteration, ValueError, json.JSONDecodeError):
            continue
    return out if len(out) == len(VIRTUAL_BASAL_U_H) else dict(VIRTUAL_BASAL_U_H)


def load_basal(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df[[c for c in df.columns if not str(c).startswith("Unnamed")]]
    df["ts"] = pd.to_datetime(df["basal_ts"], format="%d/%m/%Y %H:%M", errors="coerce")
    df = df.dropna(subset=["ts"]).drop_duplicates("ts", keep="first")
    df = df.sort_values("ts").reset_index(drop=True)
    df["date"] = df["ts"].dt.date
    return df


def day_total(g, d):
    """Step integration of the rate over one day (U)."""
    t = g["ts"].tolist()
    r = g["basal_dose"].astype(float).tolist()
    start = pd.Timestamp(d)
    end = start + pd.Timedelta(days=1)
    tot = r[0] * (t[0] - start).total_seconds() / 3600
    for i in range(len(t)):
        nxt = t[i + 1] if i + 1 < len(t) else end
        tot += r[i] * (nxt - t[i]).total_seconds() / 3600
    return tot


def daily_bolus(pid):
    """Daily sums of bolus_dose (U), over the days with at least one bolus."""
    path = os.path.join(globals.raw_dir(pid), f"UoMBolus{pid}.csv")
    if not os.path.isfile(path):
        return pd.Series(dtype=float)
    df = pd.read_csv(path, encoding="utf-8-sig")
    ts = pd.to_datetime(df["bolus_ts"], format="%d/%m/%Y %H:%M", errors="coerce")
    dose = pd.to_numeric(df["bolus_dose"], errors="coerce")
    ok = ts.notna() & dose.notna()
    return dose[ok].groupby(ts[ok].dt.date).sum()


def daily_totals(df):
    kind = str(df["insulin_kind"].iloc[0]).strip().upper() if "insulin_kind" in df else "R"
    if kind == "L":
        return df.groupby("date")["basal_dose"].sum(), "L (injections)"
    return pd.Series({d: day_total(g, d) for d, g in df.groupby("date")}), "R (pump)"


# -----------------------------------------------------------#
# Main
# -----------------------------------------------------------#
pairs = load_pairs()
wanted = sys.argv[1:] or list(pairs)
vb = virtual_basal()
rows = []
for pid in wanted:
    path = os.path.join(globals.raw_dir(pid), f"UoMBasal{pid}.csv")
    if not os.path.isfile(path):
        print(f"[{pid}] basal file not found: {path}")
        continue
    df = load_basal(path)
    v, regime = daily_totals(df)
    per_day = df.groupby("date").size()
    partial = int((per_day < PARTIAL_FRACTION * per_day.median()).sum()) if regime.startswith("R") else 0
    u = float(v.median())
    # Closest virtual patient by total daily basal (rate x 24).
    best = min(vb, key=lambda k: abs(vb[k] * 24 - u))
    selected, in_pairs = f"Patient_{best}", pairs.get(pid, "")
    b = daily_bolus(pid)
    rows.append({"ID": pid, "Regime": regime,
                 "Basal_U_day": round(u, 2), "Mean_U_day": round(float(v.mean()), 2),
                 "SD_U_day": round(float(v.std(ddof=1)), 2) if len(v) > 1 else np.nan,
                 "Days": len(v), "Partial_days": partial,
                 "Bolus_U_day": round(float(b.median()), 2) if len(b) else np.nan,
                 "Bolus_mean_U_day": round(float(b.mean()), 2) if len(b) else np.nan,
                 "Bolus_days": len(b),
                 "Virtual_selected": selected, "Virtual_basal_U_h": vb[best],
                 "Virtual_in_pairs": in_pairs, "Agrees": selected == in_pairs})
    bolus_txt = f"{b.median():.2f}" if len(b) else "n/a"
    print(f"[{pid}] basal {u:.2f} U/day -> {selected}  (pairs.csv: {in_pairs}); bolus {bolus_txt} U/day")

out = pd.DataFrame(rows)
os.makedirs(globals.path4, exist_ok=True)
out.to_csv(os.path.join(globals.path4, "Table1_basal_matching.csv"), index=False)
if len(out):
    n = int(out["Agrees"].sum())
    print(f"\n{n}/{len(out)} participants match the virtual patient in pairs.csv.")
    for _, x in out[~out["Agrees"]].iterrows():
        print(f"  {x.ID}: rule gives {x.Virtual_selected}, pairs.csv has {x.Virtual_in_pairs}")
