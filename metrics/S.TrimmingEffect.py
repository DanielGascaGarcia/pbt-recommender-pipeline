"""
S.TrimmingEffect.py
Metrics: how much the trimming of low-reliability hours changes the InVivo
guide (13.InterpolationRChZenodo.py), without changing the PBT or the
simulations.

Created: November 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each participant, at minute :59 of every hour (where 13 places its
    nodes), compares
        original   MedRelChange, the hourly median relative change
        guide      BGRChInt, the guide after trimming, interpolation and
                   smoothing
    in trimmed hours (the rule of 13, replicated) and kept hours (where the
    guide differs only through the smoothing). The difference beyond that of
    the kept hours is what the trimming adds.

Inputs
    globals.invivo_dir, globals.sims_root, globals.path4
    InVivo processed/<id>/ComparisonJoinedNoActivity<id>.csv, SampleJoined<id>.csv

Outputs (in results/metrics/tables/)
    TrimmingEffect_by_hour.csv          one row per participant-hour
    TrimmingEffect_by_participant.csv   trimmed hours, mean |guide - original|
                                        in trimmed and kept hours, how many
                                        trimmed hours grew, shrank or changed sign
    TrimmingEffect_summary.csv          the same over the cohort

Notes
    - Only the InVivo guide is analysed. In silico (one simulated day) every
      hour is of high reliability, so the trimming sets nothing aside there
      (see InSilico/10 and 13).
    - Values in mmol/L per hour.
"""

import os

import numpy as np
import pandas as pd

import globals

SIMS = globals.sims_root()
OUT = globals.path4


def hour_minute(keys):
    k = keys.astype(str).str.strip()
    return k.str[:2].astype(int), k.str[3:5].astype(int)


def at_minute_59(f, col):
    d = pd.read_csv(f)
    key = next(c for c in d.columns if c.strip().lower() == "key")
    h, m = hour_minute(d[key])
    s = d.loc[m == 59].assign(hour=h[m == 59]).groupby("hour")[col].first()
    return s.reindex(range(24))


def trimmed_hours(pid):
    """The rule of 13.InterpolationRChZenodo.py, replicated as in S.CurveAgreement.py."""
    data = pd.read_csv(os.path.join(globals.invivo_dir(pid), f"ComparisonJoinedNoActivity{pid}.csv"))
    vals, flags, hours = [], [], []
    j = 0
    for _ in range(4 * 1440):
        if j == 1440:
            j = 0
        if j % 60 == 59:
            vals.append(data.loc[j, "MedRelChange"]); flags.append(data.loc[j, "Flag"]); hours.append(j // 60)
        j += 1
    s = pd.DataFrame({"hour": hours, "v": vals, "flag": flags})
    low = s[s["flag"] != 3]
    out = np.zeros(24, bool)
    if len(low) and low["v"].notna().any():
        q1, q3 = np.nanpercentile(low["v"], [25, 75])
        for h in low.loc[(low["v"] < q1) | (low["v"] > q3), "hour"]:
            out[int(h)] = True
    return out


rows, parts = [], []
for pid in sorted(d for d in os.listdir(SIMS) if os.path.isdir(os.path.join(SIMS, d))):
    base = globals.invivo_dir(pid)
    f_orig = os.path.join(base, f"ComparisonJoinedNoActivity{pid}.csv")
    f_guide = os.path.join(base, f"SampleJoined{pid}.csv")
    if not (os.path.isfile(f_orig) and os.path.isfile(f_guide)):
        print(f"[{pid}] InVivo files not found; skipped")
        continue
    orig = at_minute_59(f_orig, "MedRelChange").to_numpy(float)
    guide = at_minute_59(f_guide, "BGRChInt").to_numpy(float)
    trim = trimmed_hours(pid)
    has = ~np.isnan(orig) & ~np.isnan(guide)
    for h in range(24):
        if has[h]:
            rows.append({"ID": pid, "hour": h, "trimmed": bool(trim[h]),
                         "original": orig[h], "guide": guide[h],
                         "abs_diff": abs(guide[h] - orig[h]),
                         "magnitude": ("larger" if abs(guide[h]) > abs(orig[h]) else
                                       "smaller" if abs(guide[h]) < abs(orig[h]) else "equal"),
                         "sign_changed": bool(np.sign(guide[h]) != np.sign(orig[h]) and orig[h] != 0)})
    t = pd.DataFrame([r for r in rows if r["ID"] == pid])
    tr, kp = t[t.trimmed], t[~t.trimmed]
    parts.append({"ID": pid, "hours": len(t), "trimmed_hours": len(tr),
                  "mean_abs_diff_trimmed": tr.abs_diff.mean() if len(tr) else np.nan,
                  "mean_abs_diff_kept": kp.abs_diff.mean() if len(kp) else np.nan,
                  "trimmed_larger": int((tr.magnitude == "larger").sum()),
                  "trimmed_smaller": int((tr.magnitude == "smaller").sum()),
                  "trimmed_sign_changed": int(tr.sign_changed.sum())})

h = pd.DataFrame(rows)
p = pd.DataFrame(parts)
os.makedirs(OUT, exist_ok=True)
h.round(4).to_csv(os.path.join(OUT, "TrimmingEffect_by_hour.csv"), index=False)
p.round(4).to_csv(os.path.join(OUT, "TrimmingEffect_by_participant.csv"), index=False)
if len(h):
    tr, kp = h[h.trimmed], h[~h.trimmed]
    s = {"participants": len(p), "hours": len(h), "trimmed_hours": len(tr),
         "mean_abs_diff_trimmed": tr.abs_diff.mean(), "median_abs_diff_trimmed": tr.abs_diff.median(),
         "mean_abs_diff_kept": kp.abs_diff.mean(), "median_abs_diff_kept": kp.abs_diff.median(),
         "trimmed_larger": int((tr.magnitude == "larger").sum()),
         "trimmed_smaller": int((tr.magnitude == "smaller").sum()),
         "trimmed_sign_changed": int(tr.sign_changed.sum())}
    pd.DataFrame([s]).round(4).to_csv(os.path.join(OUT, "TrimmingEffect_summary.csv"), index=False)
    print(p.round(3).to_string(index=False))
    print()
    for k, v in s.items():
        print(f"{k:26} {round(v, 3) if isinstance(v, float) else v}")
