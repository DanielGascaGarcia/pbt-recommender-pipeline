"""
G.TrimmedHoursCheck.py
Development check (metrics): compare the trimmed hours computed in two ways,
to confirm that G.CurveCheck.py and S.CurveAgreement.py mark the same hours
that 13.InterpolationRChZenodo.py sets aside.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    A  exact replica of 13: rows j % 60 == 59 of
       ComparisonJoinedNoActivity<id>.csv over 4 days (96 samples, each hour
       repeated 4 times), P25/P75 over the non-green samples.
    B  the earlier method of CurveCheck: BGHourRelativeChange<id>0To24medians_wCN.csv,
       last value of each hour, P25/P75 over the 24 hours.
    Prints, per participant, the hours of each method and whether they match.

Inputs
    globals.invivo_dir, globals.sims_root; the two InVivo files above

Notes
    - B differed from A in 7 of 17 participants, always marking extra hours:
      the percentiles of 96 repeated samples give a wider interval than those
      of 24. CurveCheck and S.CurveAgreement now use A.
    - Not part of the pipeline; kept to document the check.

Usage (from the metrics folder)
    python G.TrimmedHoursCheck.py
"""

import os

import numpy as np
import pandas as pd

import globals

SIMS = globals.sims_root()


def trimmed_13(pid):
    f = os.path.join(globals.invivo_dir(pid), f"ComparisonJoinedNoActivity{pid}.csv")
    if not os.path.isfile(f):
        return None
    data = pd.read_csv(f)
    vals, flags, hours = [], [], []
    j = 0
    for _ in range(4 * 1440):              # same loop as the while of 13
        if j == 1440:
            j = 0
        if j % 60 == 59:
            vals.append(data.loc[j, "MedRelChange"])
            flags.append(data.loc[j, "Flag"])
            hours.append(j // 60)
        j += 1
    s = pd.DataFrame({"hour": hours, "v": vals, "flag": flags})
    low = s[s["flag"] != 3]
    if len(low) == 0:
        return set()
    q1, q3 = np.nanpercentile(low["v"], [25, 75])
    out = low[(low["v"] < q1) | (low["v"] > q3)]
    return set(int(h) for h in out["hour"])


def trimmed_curvecheck(pid):
    f = os.path.join(globals.invivo_dir(pid), f"BGHourRelativeChange{pid}0To24medians_wCN.csv")
    if not os.path.isfile(f):
        return None
    d = pd.read_csv(f)
    h = d["Key"].astype(str).str.strip().str[:2].astype(int)
    last = d.groupby(h).last().reindex(range(24))
    low = last["Flag"] != 3
    v = last.loc[low, "MedRelChange"]
    if v.notna().sum() == 0:
        return set()
    q1, q3 = np.nanpercentile(v, [25, 75])
    out = low & ((last["MedRelChange"] < q1) | (last["MedRelChange"] > q3))
    return set(int(x) for x in np.where(out.fillna(False).to_numpy())[0])


rows = []
for pid in sorted(d for d in os.listdir(SIMS) if os.path.isdir(os.path.join(SIMS, d))):
    a, b = trimmed_13(pid), trimmed_curvecheck(pid)
    if a is None or b is None:
        print(f"[{pid}] missing file; skipped")
        continue
    rows.append({"ID": pid,
                 "match": a == b,
                 "hours_13": sorted(a),
                 "hours_CurveCheck": sorted(b),
                 "only_in_13": sorted(a - b),
                 "only_in_CurveCheck": sorted(b - a)})

t = pd.DataFrame(rows)
print(t.to_string(index=False))
print(f"\nMatch in {int(t['match'].sum())} of {len(t)}")
