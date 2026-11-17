"""
S.CurveAgreement.py
Metrics: agreement between the reference curve of each participant (InVivo)
and the basal-only simulation built from it (InSilico), i.e. how well the
manual simulator input follows the participant.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Per participant, on 24 hourly means:
        r           Pearson correlation between the two curves (shape)
        MAE_c       mean |difference| of the curves, each centred on its own
                    mean, mmol/L
        MAE_c high_rel   the same, each curve centred on the mean of its
                    high-reliability hours (at least MIN_HIGH_REL_HOURS, 6;
                    otherwise all hours, reported), so that unreliable hours
                    such as the 12 mmol/L plateaus do not set the level
        offset      mean of the simulation minus mean of the reference
                    (reflects the 6 mmol/L anchoring)
        range_ref, range_sim   max - min of each curve
        r and MAE_c without trimmed hours: leaving out the hours set aside
                    by 13.InterpolationRChZenodo.py (replicated exactly)
        r without grey and trimmed hours (r_clean): leaving out also the
                    hours without BG data, i.e. the hours the simulator input
                    was meant to follow

Inputs
    globals.invivo_dir, globals.sims_root, globals.path4, globals.MGDL_PER_MMOL
    InVivo processed/<id>/BGwNMLeftJoinedHourlyInterpolated<id>.csv   reference
    InVivo processed/<id>/BGHourRelativeChange<id>0To24medians_wCN.csv   reliability
    InVivo processed/<id>/ComparisonJoinedNoActivity<id>.csv   trimmed hours
    InSilico/simulations/<id>/Simulation_*/state_results.xlsx   basal-only run

Outputs (in results/metrics/tables/)
    CurveAgreement_by_participant.csv
    CurveAgreement_summary.csv
    CurveAgreement_by_hour.csv          one row per participant-hour, with reliability
    CurveAgreement_by_reliability.csv   |difference| between the centred curves by
                                        reliability level: hours, and mean and median
                                        with each centring (all hours; high-reliability hours)

Notes
    - r without grey and trimmed hours (r_clean) is the shape measure of the
      criterion used to rebuild simulator inputs (r_clean >= 0.5 and centred
      difference < 1 mmol/L in high-reliability hours); it is labelled
      "descriptive" in the printed output.
    - The centred difference in high-reliability hours of the criterion is
      MAE_centred_high_rel_in_high_rel_hours_mmolL.
    - The reference is the hourly mean of the curve of
      0.InterpolationBGHourlyDataZenodo.py, after its 3-12 mmol/L clip and
      cubic interpolation, so it can show plateaus at 12 and some overshoot.
    - Descriptive only: hourly points are autocorrelated and the simulation
      was fitted to the reference, so no p-values are given.
"""

import glob
import os

import numpy as np
import pandas as pd

import globals

ROOT = globals.ROOT
OUT = globals.path4
SIMS = globals.sims_root()
MGDL = globals.MGDL_PER_MMOL
MIN_HIGH_REL_HOURS = globals.MIN_HIGH_REL_HOURS   # minimum high-reliability hours to centre on them


def reference_hourly(pid):
    f = os.path.join(globals.invivo_dir(pid), f"BGwNMLeftJoinedHourlyInterpolated{pid}.csv")
    if not os.path.isfile(f):
        return None, None
    d = pd.read_csv(f)
    # Key column and the numeric value column (the median curve), whatever its
    # exact name.
    key = next(c for c in d.columns if c.strip().lower() == "key")
    num = [c for c in d.columns if c != key and not c.lower().startswith("unnamed")
           and pd.api.types.is_numeric_dtype(d[c])]
    col = next((c for c in num if "med" in c.lower()), num[-1])
    # Hourly mean of the minute values (24 values); to mmol/L if stored in mg/dL.
    hour = d[key].astype(str).str.strip().str[:2].astype(int)
    h = d.groupby(hour)[col].mean().reindex(range(24))
    if h.median() > 30:                     # stored in mg/dL
        h = h / MGDL
    return h.to_numpy(), col


def reliability_hourly(pid):
    """Reliability of each hour from 10.PivotGeneratormediansZenodo.py:
    1 low, 2 medium, 3 high; 0 when the hour has no BG data."""
    f = os.path.join(globals.invivo_dir(pid), f"BGHourRelativeChange{pid}0To24medians_wCN.csv")
    if not os.path.isfile(f):
        return None
    d = pd.read_csv(f)
    hour = d["Key"].astype(str).str.strip().str[:2].astype(int)
    first = d.groupby(hour).first()
    flag = first["Flag"].where(first["MedRelChange"].notna(), 0)
    return flag.reindex(range(24)).fillna(0).astype(int).to_numpy()


def trimmed_hours(pid):
    """Hours set aside by the interquartile trimming when the guide was built, replicating
    13.InterpolationRChZenodo.py exactly: rows j % 60 == 59 of
    ComparisonJoinedNoActivity<id>.csv over 4 days (96 samples, each hour
    repeated 4 times), P25/P75 over the non-high-reliability samples."""
    f = os.path.join(globals.invivo_dir(pid), f"ComparisonJoinedNoActivity{pid}.csv")
    if not os.path.isfile(f):
        return np.zeros(24, bool)
    data = pd.read_csv(f)
    # Same loop as step 13: the node at minute :59 of every hour over four days.
    vals, flags, hours = [], [], []
    j = 0
    for _ in range(4 * 1440):
        if j == 1440:
            j = 0
        if j % 60 == 59:
            vals.append(data.loc[j, "MedRelChange"])
            flags.append(data.loc[j, "Flag"])
            hours.append(j // 60)
        j += 1
    s = pd.DataFrame({"hour": hours, "v": vals, "flag": flags})
    low = s[s["flag"] != 3]
    out = np.zeros(24, bool)
    if len(low) == 0 or low["v"].notna().sum() == 0:
        return out
    q1, q3 = np.nanpercentile(low["v"], [25, 75])
    for h in low.loc[(low["v"] < q1) | (low["v"] > q3), "hour"]:
        out[int(h)] = True
    return out


def simulated_hourly(pid):
    f = glob.glob(os.path.join(SIMS, pid, "Simulation_*", "state_results.xlsx"))
    if len(f) != 1:
        return None
    # Hourly mean of the simulated IG over the first day.
    ig = pd.read_excel(f[0], sheet_name="Patient_0")["IG (mmol/L)"].to_numpy()[:1440]
    return np.array([ig[h * 60:(h + 1) * 60].mean() for h in range(24)])


rows, hours = [], []
LEVEL = {3: "high", 2: "medium", 1: "low", 0: "no data"}
# One row per participant that has both a reference and a basal-only run.
for pid in sorted(d for d in os.listdir(SIMS) if os.path.isdir(os.path.join(SIMS, d))):
    ref, col = reference_hourly(pid)
    sim = simulated_hourly(pid)
    if ref is None or sim is None:
        print(f"[{pid}] reference or basal-only simulation not found; skipped")
        continue
    # ok: hours where both curves have a value. a, b: reference and simulation on
    # those hours; rc, sc: each centred on its own mean.
    ok = ~np.isnan(ref) & ~np.isnan(sim)
    a, b = ref[ok], sim[ok]
    rc, sc = a - a.mean(), b - b.mean()
    rel = reliability_hourly(pid)
    # Centring on the high-reliability hours only (unreliable hours, e.g. the
    # 12 mmol/L clip plateaus, do not set the level). Falls back to all hours
    # if there are fewer than MIN_HIGH_REL_HOURS.
    g = (rel == 3)[ok] if rel is not None else np.zeros(int(ok.sum()), bool)
    if g.sum() >= MIN_HIGH_REL_HOURS:
        rg, sg = a - a[g].mean(), b - b[g].mean()
        centring_hr = "high_rel"
    else:
        rg, sg = rc, sc
        centring_hr = "all_hours_fallback"
    # Without the trimmed hours: r and centred MAE over the kept hours.
    outl = trimmed_hours(pid)[ok]
    keep = ~outl
    a2, b2 = a[keep], b[keep]
    r_k = np.corrcoef(a2, b2)[0, 1] if keep.sum() > 2 else np.nan
    mae_k = np.abs((a2 - a2.mean()) - (b2 - b2.mean())).mean() if keep.sum() else np.nan
    # Descriptive r over the hours the input was meant to follow: no grey hours
    # (no BG data) and no trimmed hours.
    grey = (rel == 0)[ok] if rel is not None else np.zeros(int(ok.sum()), bool)
    target = keep & ~grey
    r_t = np.corrcoef(a[target], b[target])[0, 1] if target.sum() > 2 else np.nan
    # One row per participant-hour (for the tables by hour and by reliability).
    if rel is not None:
        for h, dr, ds, gr, gs in zip(np.arange(24)[ok], rc, sc, rg, sg):
            hours.append({"ID": pid, "hour": int(h), "reliability": LEVEL[int(rel[h])],
                          "trimmed_hour": bool(trimmed_hours(pid)[h]),
                          "abs_diff_centred_mmolL": abs(dr - ds),
                          "abs_diff_centred_high_rel_mmolL": abs(gr - gs)})
    # One row per participant: every measure described in the header.
    rows.append({"ID": pid, "hours": int(ok.sum()), "reference_column": col,
                 "r": np.corrcoef(a, b)[0, 1],
                 "MAE_centred_mmolL": np.abs(rc - sc).mean(),
                 "high_rel_hours": int(g.sum()),
                 "centring_high_rel": centring_hr,
                 "MAE_centred_high_rel_mmolL": np.abs(rg - sg).mean(),
                 "MAE_centred_high_rel_in_high_rel_hours_mmolL":
                     np.abs(rg - sg)[g].mean() if g.any() else np.nan,
                 "offset_mmolL": b.mean() - a.mean(),
                 "range_ref_mmolL": a.max() - a.min(), "range_sim_mmolL": b.max() - b.min(),
                 "trimmed_hours": int(outl.sum()),
                 "r_without_trimmed_hours": r_k,
                 "target_hours": int(target.sum()),
                 "r_without_grey_and_trimmed_hours": r_t,
                 "MAE_centred_without_trimmed_hours_mmolL": mae_k})

# Save the table by participant, then the cohort summary.
t = pd.DataFrame(rows)
t.round(3).to_csv(os.path.join(OUT, "CurveAgreement_by_participant.csv"), index=False)
if len(t):
    s = {"participants": len(t),
         "r_median": t.r.median(), "r_min": t.r.min(), "r_max": t.r.max(),
         "MAE_centred_median_mmolL": t.MAE_centred_mmolL.median(),
         "MAE_centred_max_mmolL": t.MAE_centred_mmolL.max(),
         "MAE_centred_high_rel_median_mmolL": t.MAE_centred_high_rel_mmolL.median(),
         "MAE_centred_high_rel_max_mmolL": t.MAE_centred_high_rel_mmolL.max(),
         # Second value of the criterion (centred |difference| in high-reliability
         # hours), quoted in the manuscript: median, maximum and who has the maximum.
         "MAE_in_high_rel_hours_median_mmolL": t.MAE_centred_high_rel_in_high_rel_hours_mmolL.median(),
         "MAE_in_high_rel_hours_max_mmolL": t.MAE_centred_high_rel_in_high_rel_hours_mmolL.max(),
         "MAE_in_high_rel_hours_max_ID": t.loc[t.MAE_centred_high_rel_in_high_rel_hours_mmolL.idxmax(), "ID"],
         "offset_median_mmolL": t.offset_mmolL.median(),
         "r_without_trimmed_hours_median": t.r_without_trimmed_hours.median(),
         "r_without_trimmed_hours_min": t.r_without_trimmed_hours.min(),
         "r_without_grey_and_trimmed_hours_median": t.r_without_grey_and_trimmed_hours.median(),
         "r_without_grey_and_trimmed_hours_min": t.r_without_grey_and_trimmed_hours.min(),
         "r_without_grey_and_trimmed_hours_max": t.r_without_grey_and_trimmed_hours.max(),
         "MAE_centred_without_trimmed_hours_median_mmolL": t.MAE_centred_without_trimmed_hours_mmolL.median()}
    pd.DataFrame([s]).round(3).to_csv(os.path.join(OUT, "CurveAgreement_summary.csv"), index=False)
    print(t.round(3).to_string(index=False))
    if hours:
        hrs = pd.DataFrame(hours)
        hrs.round(3).to_csv(os.path.join(OUT, "CurveAgreement_by_hour.csv"), index=False)
        # Table by reliability: hours, and mean and median |difference| with each
        # centring, under a single header row.
        order = ["high", "medium", "low", "no data"]
        g = hrs.groupby("reliability")
        rel_tab = pd.DataFrame({
            "hours": g.size(),
            "centred_all_hours_mean_mmolL": g["abs_diff_centred_mmolL"].mean(),
            "centred_all_hours_median_mmolL": g["abs_diff_centred_mmolL"].median(),
            "centred_high_rel_mean_mmolL": g["abs_diff_centred_high_rel_mmolL"].mean(),
            "centred_high_rel_median_mmolL": g["abs_diff_centred_high_rel_mmolL"].median(),
        }).reindex(order).dropna(how="all")
        rel_tab.index.name = "reliability"
        rel_tab["hours"] = rel_tab["hours"].astype(int)
        rel_tab.round(3).to_csv(os.path.join(OUT, "CurveAgreement_by_reliability.csv"))
        print("\nAbsolute difference of the centred curves by reliability (mmol/L):")
        print(rel_tab.round(3).to_string())
    print()
    for k, v in s.items():
        print(f"{k:28} {round(v, 3) if isinstance(v, float) else v}")   # the ID is text
