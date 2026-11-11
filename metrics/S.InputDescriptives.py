"""
S.InputDescriptives.py
Metrics: CGM coverage of the analysis days of every participant, for the data
appendix of the chapter (as G.CGMCoverage.py in papers 1 and 2).

Created: November 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each participant, over the analysis days (the days that build the
    composite profile, the rule of globals.day_split):
    - coverage of each day: share of the 288 five-minute slots of the day
      with at least one CGM reading, from the glucose before the meal
      exclusion (BGValue2 of the _UoMGlucose files);
    - per participant: days, mean, median, minimum and maximum coverage,
      and days with coverage of at least 70%.
    And the cohort totals: days, mean coverage and days with >= 70%.

Inputs
    globals.PAIRS_FILE, globals.invivo_dir, globals.path4,
    globals.MAX_ANALYSIS_DAYS, globals.RESERVED_DAYS
    InVivo processed/<id>/_UoMGlucose<id>_<date>.csv  (4.MealBolusDetection)

Outputs (in results/metrics/tables/)
    InputDescriptives_by_participant.csv
    InputCoverage_by_day.csv
    InputDescriptives_tables.tex   the coverage table of the data appendix, LaTeX

Notes
    - Descriptive only: no day or participant is excluded by coverage, and
      no reported result depends on this script.
    - Coverage uses BGValue2, the glucose before the meal exclusion, so it
      measures the sensor record and not the effect of the algorithm (as
      G.CGMCoverage.py in papers 1 and 2).
    - It counts 5-minute slots with at least one reading rather than
      readings, so that extra readings between the regular ones (present in
      some records) do not raise it above 100%.

Usage (from the metrics folder, with the project root on PYTHONPATH)
    python S.InputDescriptives.py
"""

import csv
import os

import pandas as pd

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
OUT = globals.path4
SLOT_MIN = 5                   # sensor interval, minutes
SLOTS_PER_DAY = 1440 // SLOT_MIN
COVERAGE_MIN = 70              # % of a full day, as in the consensus guidance


def label(pid):
    """Participant label as written in the manuscript (Mann01 -> Man01)."""
    return "Man" + pid[4:] if pid.startswith("Mann") else pid


# -----------------------------------------------------------#
# Participants
# -----------------------------------------------------------#
with open(globals.PAIRS_FILE, newline="", encoding="utf-8") as f:
    lines = (l for l in f if l.strip() and not l.lstrip().startswith("#"))
    pids = [r["id"].strip() for r in csv.DictReader(lines)]

rows, days_rows = [], []
for pid in pids:
    proc = globals.invivo_dir(pid)
    dates = globals._dates(proc, f"UoMGlucose{pid}_")
    n_an = max(0, min(globals.MAX_ANALYSIS_DAYS, len(dates) - globals.RESERVED_DAYS))
    cov = []
    for d in dates[:n_an]:
        p = os.path.join(proc, f"_UoMGlucose{pid}_{d}.csv")
        if not os.path.isfile(p):
            continue
        b = pd.read_csv(p)
        has = pd.to_numeric(b["BGValue2"], errors="coerce").notna()
        k = b["Key"].astype(str).str.strip()
        minute = k.str[:2].astype(int) * 60 + k.str[3:5].astype(int)
        slots = (minute[has] // SLOT_MIN).nunique()
        c = min(100.0, 100 * slots / SLOTS_PER_DAY)
        cov.append(c)
        days_rows.append({"ID": pid, "date": d, "coverage_pct": c})
    cov = pd.Series(cov, dtype=float)
    rows.append({"ID": pid, "Label": label(pid), "Analysis_days": len(cov),
                 "Coverage_mean_pct": cov.mean(), "Coverage_median_pct": cov.median(),
                 "Coverage_min_pct": cov.min(), "Coverage_max_pct": cov.max(),
                 "Days_ge70_coverage": int((cov >= COVERAGE_MIN).sum()),
                 "Days_ge70_pct": 100 * (cov >= COVERAGE_MIN).mean() if len(cov) else float("nan")})
    print(f"[{pid}] {len(cov)} analysis days, coverage {cov.mean():.1f}%")

# -----------------------------------------------------------#
# Save
# -----------------------------------------------------------#
t = pd.DataFrame(rows)
d = pd.DataFrame(days_rows)
os.makedirs(OUT, exist_ok=True)
t.round(2).to_csv(OUT + "InputDescriptives_by_participant.csv", index=False)
d.round(2).to_csv(OUT + "InputCoverage_by_day.csv", index=False)

print(t.drop(columns="ID").round(1).to_string(index=False))
print(f"\nCohort: {len(d)} analysis days, mean coverage {d['coverage_pct'].mean():.1f}%, "
      f"{int((d['coverage_pct'] >= COVERAGE_MIN).sum())} days with >= {COVERAGE_MIN}% coverage")
print("Saved:", os.path.abspath(OUT + "InputDescriptives_by_participant.csv"))
print("Saved:", os.path.abspath(OUT + "InputCoverage_by_day.csv"))


# -----------------------------------------------------------#
# LaTeX table of the data appendix, in the format of the appendix
# sections of the chapters of papers 1 and 2 (same columns and summary row)
# -----------------------------------------------------------#
def f1(x, n=1):
    return f"{x:.{n}f}"


days = t["Analysis_days"]
tex = [r"""% Data appendix of the chapter of paper 3: CGM coverage.
% Written by metrics/S.InputDescriptives.py.
\begin{table}[htbp]
\centering
\small
\caption{CGM coverage per participant, Chapter~\ref{Chap:Paper3}. Days: analysis days. Coverage: percentage of the 288 five-minute slots of each day with at least one reading, before the exclusion of the post-meal windows, summarised over days. Days $\geq$70\%: days with coverage of at least 70\%. SD: standard deviation.}
% Source: InputDescriptives_by_participant.csv
\label{tab:P3_CGMCoverage}
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{ID} & \textbf{Days} & \makecell{\textbf{Coverage}\\\textbf{mean (\%)}} & \makecell{\textbf{Coverage}\\\textbf{median (\%)}} & \makecell{\textbf{Coverage}\\\textbf{min (\%)}} & \makecell{\textbf{Days $\geq$70\%}\\\textbf{n (\%)}} \\
\hline"""]
for _, x in t.iterrows():
    tex.append(f"{x.Label} & {int(x.Analysis_days)} & {f1(x.Coverage_mean_pct)} & {f1(x.Coverage_median_pct)} & "
               f"{f1(x.Coverage_min_pct)} & {int(x.Days_ge70_coverage)} ({f1(x.Days_ge70_pct)}) \\\\")
tex.append(r"""\hline
\multicolumn{6}{|l|}{\textit{Summary: days, mean (SD) [range]; coverage, mean (SD); days $\geq$70\%, mean percentage}} \\
\hline""")
tex.append(f"All (n={len(t)}) & {days.mean():.1f} ({days.std(ddof=1):.1f}) [{int(days.min())}--{int(days.max())}] & "
           f"{t['Coverage_mean_pct'].mean():.1f} ({t['Coverage_mean_pct'].std(ddof=1):.1f}) & & & "
           f"{t['Days_ge70_pct'].mean():.1f}\\% \\\\")
tex.append(r"""\hline
\end{tabular}
\end{table}
""")
with open(OUT + "InputDescriptives_tables.tex", "w", encoding="utf-8") as fh:
    fh.write("\n".join(tex))
print("Saved:", os.path.abspath(OUT + "InputDescriptives_tables.tex"))
