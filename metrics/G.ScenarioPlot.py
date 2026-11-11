"""
G.ScenarioPlot.py
Metrics (figure): simulated glucose of one participant before and after the
recommended basal, for the two evaluation days.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For Day1 and Day2 draws the glucose before (solid) and after (dashed),
    the target range (3.9-10.0 mmol/L), the meal times with their grams, and
    below, the basal profiles before and after. Prints, per day and arm, the
    mean glucose, SD (ddof = 1) and time in range.

Inputs
    globals.sims_root, globals.path3
    InSilico/simulations/<id>/Simulation_*/Day1|Day2/Before|After/
        state_results.xlsx, simulation_settings.json

Output
    results/metrics/figures/Scenarios_<id>.png

Notes
    - Same figure format as papers 1 and 2 (font size 12, light grey grid,
      black zero line, 300 dpi). The title is kept: this is a check figure,
      not a manuscript figure.
    - There must be a single Simulation_* folder per participant.
    - The meal labels are placed at the top of the axis as it stands when
      they are drawn.

Usage (from the metrics folder, with the project root on PYTHONPATH)
    python G.ScenarioPlot.py Mann06    one participant
    python G.ScenarioPlot.py           every participant (as metrics calls it)
"""

import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.size': 12})   # same figure format as papers 1 and 2

import globals

SIMS = globals.sims_root()


def load(base, day, label):
    d = os.path.join(base, day, label)
    ig = pd.read_excel(os.path.join(d, "state_results.xlsx"), sheet_name="Patient_0")["IG (mmol/L)"].to_numpy()[:1440]
    s = json.load(open(os.path.join(d, "simulation_settings.json"), encoding="utf-8"))
    meals = s["inputs"]["meal_carb"]["start_time"][0]
    carbs = s["inputs"]["meal_carb"]["magnitude"][0]
    b = s["inputs"]["basal_insulin"]
    return ig, list(zip(meals, carbs)), b["start_time"][0], b["magnitude"][0]


def plot(pid):
    folders = glob.glob(os.path.join(SIMS, pid, "Simulation_*"))
    if len(folders) != 1:
        raise FileNotFoundError(f"expected one Simulation_* folder in {SIMS}/{pid}, found {len(folders)}")
    base = folders[0]
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1]})
    for col, day in enumerate(["Day1", "Day2"]):
        ax, axb = axes[0, col], axes[1, col]
        ax.axhspan(3.9, 10.0, color="green", alpha=0.08, label="Target range 3.9-10.0")
        print(f"{pid} {day}")
        for label, style in (("Before", "-"), ("After", "--")):
            ig, meals, bt, bm = load(base, day, label)
            t = np.arange(len(ig)) / 60
            tir = 100 * np.mean((ig >= 3.9) & (ig <= 10.0))
            ax.plot(t, ig, style, lw=1.6, label=f"{label} (TIR {tir:.1f}%)")
            axb.step(np.r_[np.array(bt) / 60, 24], np.r_[bm, bm[-1]], style, where="post", label=label)
            print(f"  {label:6} mean {ig.mean():.2f} mmol/L, SD {ig.std(ddof=1):.2f}, TIR {tir:.1f}%")
        for m, g in meals:
            ax.axvline(m / 60, color="grey", lw=0.8, ls=":")
            ax.text(m / 60, ax.get_ylim()[1] * 0.97, f"{g:.0f} g", fontsize=10, ha="center", va="top")
        ax.set_title(f"{pid} - {day}"); ax.set_ylabel("IG (mmol/L)"); ax.grid(which='major', color='#DDDDDD', linewidth=0.8); ax.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5); ax.legend(fontsize=10)
        axb.set_ylabel("Basal (U/h)"); axb.set_xlabel("Hour of day"); axb.grid(which='major', color='#DDDDDD', linewidth=0.8); axb.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5); axb.legend(fontsize=10)
        axb.set_xticks(range(0, 25, 2))
    fig.tight_layout()
    os.makedirs(globals.path3, exist_ok=True)
    out = os.path.join(globals.path3, f"Scenarios_{pid}.png")
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print("Saved:", os.path.abspath(out))


ids = sys.argv[1:] or sorted(d for d in os.listdir(SIMS) if os.path.isdir(os.path.join(SIMS, d)))
for pid in ids:
    try:
        plot(pid)
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"[{pid}] skipped: {e}")
    plt.close("all")
