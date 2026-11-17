"""
G.CurveCheck.py
Metrics (figure): visual and numeric check of the manual simulator input of
one participant, the reference curve (InVivo) against the basal-only
simulation built from it.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Prints the agreement numbers of S.CurveAgreement.py for one participant
    (r, centred differences overall and in high-reliability hours, the same
    without trimmed hours, r without grey and trimmed hours) and draws:
        top     both curves in mmol/L (the simulation starts at 6 mmol/L)
        bottom  both curves centred on their high-reliability hours, hours
                coloured by reliability (green high, yellow medium, red low,
                grey no data) and trimmed hours marked with x; the title
                gives r_clean and the difference in high-reliability hours
                (the criterion) and the r over 24 h

Inputs
    as S.CurveAgreement.py

Output
    results/metrics/figures/CurveCheck_<id>.png

Notes
    - Same figure format as papers 1 and 2 (font size 12, light grey grid,
      black zero line, 300 dpi). The title is kept: this is a check figure,
      not a manuscript figure.
    - Used while building the simulator input: simulate, put
      state_results.xlsx in InSilico/simulations/<id>/Simulation_*/, run this
      script, adjust, repeat. There must be a single Simulation_* folder.
    - r without grey and trimmed hours (r_clean) is the shape measure of the
      criterion used to rebuild simulator inputs (r_clean >= 0.5 and centred
      difference < 1 mmol/L in high-reliability hours). The figure title shows
      the two values of the criterion and the r over 24 h.
    - Hours where either curve is missing are left out of every number but
      are still drawn.
    - The reference is the hourly mean of the curve of
      0.InterpolationBGHourlyDataZenodo.py, after its 3-12 mmol/L clip and
      cubic interpolation, so it can show plateaus at 12 and some overshoot.

Usage (from the metrics folder, with the project root on PYTHONPATH)
    python G.CurveCheck.py 2301      one participant
    python G.CurveCheck.py           every participant (as metrics calls it)
"""

import glob
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.size': 12})   # same figure format as papers 1 and 2

import globals

MIN_HIGH_REL_HOURS = globals.MIN_HIGH_REL_HOURS   # minimum high-reliability hours to centre on them
# SIMS: InSilico/simulations/ (working copy with the basal-only runs).
# COLOURS: reliability 3 high (green), 2 medium (gold), 1 low (red), 0 no BG
# data (grey).
SIMS = globals.sims_root()
COLOURS = {3: "green", 2: "gold", 1: "red", 0: "grey"}


def reference_hourly(pid):
    # Reference curve of InVivo (0.InterpolationBGHourlyDataZenodo.py): hourly mean
    # of its minute values, 24 values; to mmol/L if stored in mg/dL (median > 30).
    d = pd.read_csv(os.path.join(globals.invivo_dir(pid), f"BGwNMLeftJoinedHourlyInterpolated{pid}.csv"))
    col = "MedianBGValue" if "MedianBGValue" in d.columns else d.select_dtypes("number").columns[-1]
    h = d["Key"].astype(str).str.strip().str[:2].astype(int)
    v = d.groupby(h)[col].mean().reindex(range(24))
    return (v / globals.MGDL_PER_MMOL if v.median() > 30 else v).to_numpy()


def reliability_hourly(pid):
    # Reliability flag of each hour (step 10), from its first minute; 0 when the
    # hour has no BG data (empty median).
    d = pd.read_csv(os.path.join(globals.invivo_dir(pid), f"BGHourRelativeChange{pid}0To24medians_wCN.csv"))
    h = d["Key"].astype(str).str.strip().str[:2].astype(int)
    first = d.groupby(h).first()
    return first["Flag"].where(first["MedRelChange"].notna(), 0).reindex(range(24)).fillna(0).astype(int).to_numpy()


def trimmed_hours(pid):
    """Hours set aside by the interquartile trimming when the guide was built, replicating
    13.InterpolationRChZenodo.py exactly: rows j % 60 == 59 of
    ComparisonJoinedNoActivity<id>.csv over 4 days (96 samples, each hour
    repeated 4 times), P25/P75 over the non-high-reliability samples."""
    # Same loop as step 13: the node at minute :59 of every hour over four
    # repeated days (96 samples); P25 and P75 over the non-green samples; an hour
    # outside them is trimmed.
    f = os.path.join(globals.invivo_dir(pid), f"ComparisonJoinedNoActivity{pid}.csv")
    if not os.path.isfile(f):
        return np.zeros(24, bool)
    data = pd.read_csv(f)
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
    # Basal-only run of the participant: hourly mean of the simulated IG over the
    # first day (1,440 minutes). Exactly one Simulation_* folder is expected.
    f = glob.glob(os.path.join(SIMS, pid, "Simulation_*", "state_results.xlsx"))
    if len(f) != 1:
        raise FileNotFoundError(f"expected one state_results.xlsx in {SIMS}/{pid}/Simulation_*/, found {len(f)}")
    ig = pd.read_excel(f[0], sheet_name="Patient_0")["IG (mmol/L)"].to_numpy()[:1440]
    return np.array([ig[h * 60:(h + 1) * 60].mean() for h in range(24)]), os.path.dirname(f[0])


def check(pid):
    ref, rel = reference_hourly(pid), reliability_hourly(pid)
    sim, folder = simulated_hourly(pid)
    # Same valid-value mask as S.CurveAgreement.py: hours where either curve is
    # missing are left out of every number below (they are still drawn).
    ok = ~np.isnan(ref) & ~np.isnan(sim)
    # Centring on the mean of all hours (original)
    rc_all, sc_all = ref - np.nanmean(ref[ok]), sim - np.nanmean(sim[ok])
    d_all = np.abs(rc_all - sc_all)
    # Centring on the mean of the high-reliability hours only, so that unreliable
    # hours (e.g. the 12 mmol/L clip plateaus) do not set the level of the curve.
    g = (rel == 3) & ok
    if g.sum() >= MIN_HIGH_REL_HOURS:
        rc, sc = ref - np.nanmean(ref[g]), sim - np.nanmean(sim[g])
        centring = f"high-reliability hours ({int(g.sum())})"
    else:
        rc, sc = rc_all, sc_all
        centring = f"all hours (only {int(g.sum())} high-reliability hours)"
    d = np.abs(rc - sc)
    d[~ok] = np.nan
    # r: Pearson correlation of the hourly values (shape).
    # hi: centred |difference| in the high-reliability hours (second value of the
    # criterion, < 1 mmol/L).
    r = np.corrcoef(ref[ok], sim[ok])[0, 1]
    hi = np.nanmean(d[g]) if g.any() else np.nan
    # Without the trimmed hours: r and centred |difference|, each curve centred
    # on its own mean over those hours.
    outl = trimmed_hours(pid)
    k = ~outl & ok
    r_k = np.corrcoef(ref[k], sim[k])[0, 1]
    d_k = np.abs((ref[k] - ref[k].mean()) - (sim[k] - sim[k].mean())).mean()
    t = k & (rel != 0)                       # no grey hours, no trimmed hours
    # r_clean (first value of the criterion, >= 0.5): r over the hours with BG
    # data that were not trimmed.
    r_t = np.corrcoef(ref[t], sim[t])[0, 1] if t.sum() > 2 else np.nan

    # Printed summary, one block per participant.
    print(f"{pid}  ({os.path.basename(folder)})")
    print(f"  r (shape)                         {r:.2f}")
    print(f"  centring                           {centring}")
    print(f"  mean |difference|, centred, all   {np.nanmean(d):.2f} mmol/L"
          f"  (centred on all hours: {np.nanmean(d_all[ok]):.2f})")
    print(f"  mean |difference|, high-rel hours {hi:.2f} mmol/L"
          f"  (centred on all hours: {d_all[g].mean() if g.any() else np.nan:.2f})")
    print(f"  without the {int(outl.sum())} trimmed hours: r {r_k:.2f}, mean |difference| {d_k:.2f} mmol/L"
          f"  (hours {', '.join(str(h) for h in np.where(outl)[0]) or 'none'})")
    print(f"  without grey and trimmed hours ({int(t.sum())} hours): r {r_t:.2f}  (r_clean, criterion >= 0.5)")
    if (~ok).any():
        print(f"  hours left out for missing values: {', '.join(str(h) for h in np.where(~ok)[0])}")
    summary = os.path.join(globals.path4, "CurveAgreement_summary.csv")
    if os.path.isfile(summary):
        s = pd.read_csv(summary).iloc[0]
        print(f"  cohort: median r {s['r_median']:.2f}, median MAE (centred) {s['MAE_centred_median_mmolL']:.2f} mmol/L")

    # Figure. Each hour drawn at its middle (h + 0.5).
    # Top: both curves in mmol/L. Bottom: both curves centred, points coloured by
    # reliability, trimmed hours marked with x.
    hours = np.arange(24) + 0.5
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    a1.plot(hours, ref, "o-", label="Reconstructed median (InVivo)")
    a1.plot(hours, sim, "s--", label="Basal-only simulation")
    a1.set_ylabel("BG (mmol/L)"); a1.legend(); a1.grid(which='major', color='#DDDDDD', linewidth=0.8); a1.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5)
    a2.axhline(linewidth=2, color="Black")
    a2.plot(hours, rc, "-", color="tab:blue", label="Reference, centred")
    a2.plot(hours, sc, "--", color="tab:orange", label="Simulation, centred")
    a2.scatter(hours, rc, c=[COLOURS[int(x)] for x in rel], s=60, zorder=3, edgecolors="black")
    if outl.any():
        a2.scatter(hours[outl], rc[outl], marker="x", s=140, color="black", zorder=4,
                   label="Trimmed hour (outside P25–P75, set aside in the guide)")
    a2.set_ylabel("Centred BG (mmol/L)\n" + ("on high-rel. hours" if rc is not rc_all else "on all hours")); a2.set_xlabel("Hour of day")
    a2.set_xticks(range(0, 25, 2)); a2.legend(); a2.grid(which='major', color='#DDDDDD', linewidth=0.8); a2.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5)
    a2.set_title(f"Criterion: r_clean = {r_t:.2f} (>= 0.5), |diff| high-reliability {hi:.2f} mmol/L (< 1); "
                  f"r 24 h = {r:.2f}", fontsize=11)
    os.makedirs(globals.path3, exist_ok=True)
    out = os.path.join(globals.path3, f"CurveCheck_{pid}.png")
    fig.tight_layout(); fig.savefig(out, dpi=300, bbox_inches="tight")
    print("Saved:", os.path.abspath(out))


# IDs given, or every participant with a working simulation folder. A
# participant with missing files is skipped with a message.
ids = sys.argv[1:] or sorted(d for d in os.listdir(SIMS) if os.path.isdir(os.path.join(SIMS, d)))
for pid in ids:
    try:
        check(pid)
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"[{pid}] skipped: {e}")
    plt.close("all")
    print()
