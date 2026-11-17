"""
S.CollectScenarioResults.py
Metrics, step 2: read the simulated glucose of every before/after scenario
and write the per-participant metrics and the results tables of the
manuscript.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For every InSilico/simulations/<id>/Simulation_<id2>/Day<k>/{Before,After}/
    it reads IG (mmol/L) from state_results.xlsx (sheet Patient_0) and
    computes, per participant and day:
        STD          SD of IG (sample, ddof = 1), mmol/L and mg/dL
        TIR          % of minutes with IG between 3.9 and 10.0 mmol/L
        taMAE        mean absolute deviation of IG from 6 mmol/L
        I            sqrt((STD_before / STD_after) x (taMAE_before / taMAE_after))
        basal_U_day  total basal insulin of the scenario (U/day)
    and, from the hourly means and SDs:
        Mean_Bias_%     mean over hours of (after - before) / before x 100
        Within15_%hrs   % of hours with |relative bias| <= 15%
        LowerVar_%hrs   % of hours with a lower SD after than before

Inputs
    globals.sims_root, globals.path4, globals.MGDL_PER_MMOL
    InSilico/simulations/<id>/Simulation_<id2>/Day<k>/{Before,After}/
        state_results.xlsx, simulation_settings.json

Outputs (in results/metrics/tables/)
    Day1.csv, Day2.csv              BG_1_<id> (before), BG_2_<id> (after), per minute
    hourly_mean_and_std_<id>_Day<k>.csv   hourly mean and SD of BG_1 and BG_2
    metrics_by_participant.csv      the metrics above, one row per participant and day
    Table3_Day1.csv, Table4_Day2.csv   variability, excursion and I, as in the manuscript
    Table5_Safety.csv               bias, +/-15% hours, lower-variability hours, TIR
                                    and delta insulin, both days

Notes
    - The +/-15% band is used by analogy with ISO 15197:2013, as a bound on
      the size of the change; it is not a claim of conformity.
    - A tiny constant (1e-12) avoids division by zero in I.
    - delta insulin is computed from the basal profiles of the settings
      files (each rate x minutes to the next change), not from the
      simulated insulin.
    - Day1.csv, Day2.csv and the hourly files keep the layout read by the
      earlier scripts 0.Metrics.py and 0.ISO.py.
    - A scenario without state_results.xlsx is reported and skipped.
"""

import glob
import json
import os

import numpy as np
import pandas as pd

import globals

# Scenarios simulated in the InSilico module (Code3/InSilico/simulations/).
SIM_ROOT = globals.sims_root()
OUT = globals.path4
# Target range (TIR) 3.9-10.0 mmol/L; taMAE is measured against 6 mmol/L.
TIR_LOW, TIR_HIGH, TARGET = 3.9, 10.0, 6.0
MGDL = globals.MGDL_PER_MMOL          # mmol/L -> mg/dL
DAYS = ("Day1", "Day2")


def read_ig(folder):
    """IG (mmol/L), one value per minute, from state_results.xlsx."""
    d = pd.read_excel(os.path.join(folder, "state_results.xlsx"), sheet_name="Patient_0")
    # Clean the column names (Excel headers can carry spaces).
    d.columns = d.columns.str.strip()
    return d["IG (mmol/L)"].reset_index(drop=True)


def basal_units_per_day(folder):
    """Total basal insulin (U/day) of the profile in simulation_settings.json:
    each rate (U/h) times the minutes until the next change, over 1440 min."""
    s = json.load(open(os.path.join(folder, "simulation_settings.json"), encoding="utf-8"))
    rates = s["inputs"]["basal_insulin"]["magnitude"][0]
    starts = list(s["inputs"]["basal_insulin"]["start_time"][0]) + [1440]
    return sum(r * (starts[i + 1] - starts[i]) / 60 for i, r in enumerate(rates))


def metrics(bg1, bg2):
    std1, std2 = bg1.std(), bg2.std()          # sample SD (ddof=1)
    # taMAE: mean |IG - 6| of each arm.
    ta1, ta2 = np.mean(np.abs(bg1 - TARGET)), np.mean(np.abs(bg2 - TARGET))
    # TIR: % of minutes within the target range.
    in_range = lambda x: 100 * ((x >= TIR_LOW) & (x <= TIR_HIGH)).mean()
    eps = 1e-12
    return {
        "STD_1_mmolL": std1, "STD_2_mmolL": std2,
        "STD_1_mgdl": std1 * MGDL, "STD_2_mgdl": std2 * MGDL,
        "STD_Reduction_%": (std1 - std2) / std1 * 100 if std1 else np.nan,
        "TIR_1_%": in_range(bg1), "TIR_2_%": in_range(bg2),
        "taMAE_1_mmolL": ta1, "taMAE_2_mmolL": ta2,
        "DeltaTaMAE_mmolL": ta1 - ta2, "DeltaTaMAE_mgdl": (ta1 - ta2) * MGDL,
        "Composite_Index": np.sqrt(((std1 + eps) / (std2 + eps)) * ((ta1 + eps) / (ta2 + eps))),
    }


def label(pid):
    """Participant label as written in the manuscript (Mann01 -> Man01)."""
    return "Man" + pid[4:] if pid.startswith("Mann") else pid


def write_manuscript_tables(m):
    """The results tables of the manuscript, same columns and rounding."""
    # Manuscript labels (Man01, ...), sorted; columns renamed and rounded as in
    # the manuscript tables.
    m = m.assign(ID=m["ID"].map(label)).sort_values("ID")
    cols = {"STD_1_mmolL": "SD1 (mmol/L)", "STD_2_mmolL": "SD2 (mmol/L)",
            "STD_1_mgdl": "SD1 (mg/dL)", "STD_2_mgdl": "SD2 (mg/dL)",
            "STD_Reduction_%": "SD Red. (%)",
            "DeltaTaMAE_mmolL": "DeltaTaMAE (mmol/L)", "DeltaTaMAE_mgdl": "DeltaTaMAE (mg/dL)",
            "Composite_Index": "I"}
    for day, name in (("Day1", "Table3_Day1.csv"), ("Day2", "Table4_Day2.csv")):
        d = m[m["Day"] == day]
        if len(d):
            (d[["ID"] + list(cols)].rename(columns=cols).round(2)
               .to_csv(os.path.join(OUT, name), index=False))
    # Table 5: the hourly measures and TIR of both days side by side, plus the
    # change in daily basal insulin.
    safety = {"Mean_Bias_%": "Mean Bias (%)", "Within15_%hrs": "Within ±15% (%hrs)",
              "LowerVar_%hrs": "Lower Variability (%hrs)",
              "TIR_1_%": "TIR1 (%)", "TIR_2_%": "TIR2 (%)"}
    parts = []
    for day, tag in (("Day1", "D1"), ("Day2", "D2")):
        d = m[m["Day"] == day].set_index("ID")[list(safety)].round(1)
        d.columns = [f"{v} {tag}" for v in safety.values()]
        parts.append(d)
    t = pd.concat(parts, axis=1)
    t["DeltaInsulin (U/day)"] = m.groupby("ID")["DeltaInsulin_U_day"].first().round(2)
    t.reset_index().to_csv(os.path.join(OUT, "Table5_Safety.csv"), index=False)


os.makedirs(OUT, exist_ok=True)
per_day = {d: {} for d in DAYS}
rows = []
# Every Simulation_<id2> folder: id from its parent folder, id2 from its name.
for sim in sorted(glob.glob(os.path.join(SIM_ROOT, "*", "Simulation_*"))):
    pid = os.path.basename(os.path.dirname(sim))
    vid = os.path.basename(sim)[len("Simulation_"):]
    for day in DAYS:
        before, after = os.path.join(sim, day, "Before"), os.path.join(sim, day, "After")
        missing = [p for p in (before, after)
                   if not os.path.isfile(os.path.join(p, "state_results.xlsx"))]
        if missing:
            print(f"[{pid}] {day}: state_results.xlsx missing in "
                  + ", ".join(os.path.relpath(m, sim) for m in missing))
            continue
        # IG before (BG_1) and after (BG_2); also kept by day for Day1.csv, Day2.csv.
        bg1, bg2 = read_ig(before), read_ig(after)
        per_day[day][f"BG_1_{pid}"] = bg1
        per_day[day][f"BG_2_{pid}"] = bg2

        # Hourly mean and SD of each arm (hour = minute // 60).
        hours = np.arange(len(bg1)) // 60
        h = pd.DataFrame({"hour": hours, "BG_1": bg1, "BG_2": bg2}).groupby("hour")
        hourly = pd.concat([h.mean().add_suffix("_mean"), h.std().add_suffix("_std")], axis=1)
        hourly.to_csv(os.path.join(OUT, f"hourly_mean_and_std_{pid}_{day}.csv"))
        # Relative bias of each hour, then the three hourly measures of Table 5.
        rel_bias = (hourly["BG_2_mean"] - hourly["BG_1_mean"]) / hourly["BG_1_mean"] * 100
        iso = {"Mean_Bias_%": rel_bias.mean(),
               "Within15_%hrs": 100 * (rel_bias.abs() <= 15).mean(),
               "LowerVar_%hrs": 100 * (hourly["BG_2_std"] < hourly["BG_1_std"]).mean()}

        # Daily basal insulin of each arm, from its settings, and the change.
        u1, u2 = basal_units_per_day(before), basal_units_per_day(after)
        rows.append({"ID": pid, "VirtualPatient": vid, "Day": day,
                     **metrics(bg1, bg2), **iso,
                     "Basal_1_U_day": u1, "Basal_2_U_day": u2,
                     "DeltaInsulin_U_day": u2 - u1})
        print(f"[{pid}] {day}: done")

# Save the per-minute tables, the metrics and the manuscript tables.
for day, cols in per_day.items():
    if cols:
        pd.DataFrame(cols).to_csv(os.path.join(OUT, f"{day}.csv"), index=False)
m = pd.DataFrame(rows)
m.to_csv(os.path.join(OUT, "metrics_by_participant.csv"), index=False)
if len(m):
    write_manuscript_tables(m)
print(f"\n{len(rows)} participant-days. Saved to {os.path.abspath(OUT)}")
