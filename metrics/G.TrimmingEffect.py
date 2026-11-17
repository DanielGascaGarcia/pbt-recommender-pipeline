"""
G.TrimmingEffect.py
Metrics (figures): the trimming of low-reliability hours in the InVivo guide,
from the table of S.TrimmingEffect.py.

Created: November 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    TrimmingEffect_cohort.png   every participant-hour: original hourly median
                                relative change (x) against the value in the
                                guide (y). Kept hours lie near the identity
                                line (they change only through the smoothing);
                                trimmed hours show how far and in which
                                direction the reconstruction moved them.
    TrimmingEffect_<id>.png     one participant over 24 h: original value
                                (bars, red if trimmed) and guide (line).

Inputs
    results/metrics/tables/TrimmingEffect_by_hour.csv   (S.TrimmingEffect.py)

Outputs
    results/metrics/figures/TrimmingEffect_cohort.png, TrimmingEffect_<id>.png

Notes
    - Same figure format as papers 1 and 2 (font size 12, light grey grid,
      black zero line, 300 dpi). The title is kept: this is a check figure,
      not a manuscript figure.

Usage
    python G.TrimmingEffect.py         cohort figure and every participant
    python G.TrimmingEffect.py 2308    cohort figure and that participant
"""

import os
import sys

import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.size': 12})   # same figure format as papers 1 and 2
import numpy as np
import pandas as pd

import globals

# T: tables folder; F: figures folder (results/metrics/).
T, F = globals.path4, globals.path3
os.makedirs(F, exist_ok=True)
h = pd.read_csv(os.path.join(T, "TrimmingEffect_by_hour.csv"), dtype={"ID": str})
# keep / trim: the kept and the trimmed participant-hours.
keep, trim = h[~h.trimmed], h[h.trimmed]

# ---- cohort
fig, ax = plt.subplots(figsize=(7, 7))
# Symmetric axis limits from the largest absolute value, with a 5% margin.
lim = np.nanmax(np.abs(h[["original", "guide"]].to_numpy())) * 1.05
ax.plot([-lim, lim], [-lim, lim], color="grey", lw=1, ls="--", label="No change")
ax.axhline(linewidth=1, color="Black"); ax.axvline(0, linewidth=1, color="Black")
ax.scatter(keep.original, keep.guide, s=18, color="tab:blue", alpha=0.6,
           label=f"Kept hours (n = {len(keep)})")
ax.scatter(trim.original, trim.guide, s=40, color="tab:red", marker="x",
           label=f"Trimmed hours (n = {len(trim)})")
ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect("equal")
ax.set_xlabel("Original hourly median relative change (mmol/L per hour)")
ax.set_ylabel("Value in the guide after trimming and interpolation (mmol/L per hour)")
# How many trimmed hours became smaller in magnitude (shown in the title).
smaller = int((trim.magnitude == "smaller").sum())
ax.set_title(f"Trimmed hours smaller in magnitude: {smaller} of {len(trim)} "
             f"({100 * smaller / max(len(trim), 1):.0f}%)", fontsize=11)
ax.legend(loc="upper left"); ax.grid(which='major', color='#DDDDDD', linewidth=0.8); ax.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5)
fig.tight_layout(); fig.savefig(os.path.join(F, "TrimmingEffect_cohort.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("Saved:", os.path.abspath(os.path.join(F, "TrimmingEffect_cohort.png")))

# ---- per participant
ids = sys.argv[1:] or sorted(h.ID.unique())
for pid in ids:
    # One participant: bars = original value (red if trimmed), line = guide.
    d = h[h.ID == pid].sort_values("hour")
    if d.empty:
        print(f"[{pid}] not in TrimmingEffect_by_hour.csv; skipped")
        continue
    fig, ax = plt.subplots(figsize=(10, 4.5))
    colours = np.where(d.trimmed, "tab:red", "tab:blue")
    ax.bar(d.hour + 0.5, d.original, width=0.8, color=colours, alpha=0.45,
           label="Original value (red: trimmed)")
    ax.plot(d.hour + 0.5, d.guide, "o-", color="black", lw=1.5, ms=4, label="Guide")
    ax.axhline(linewidth=2, color="Black")
    ax.set_xticks(range(0, 25, 2)); ax.set_xlabel("Hour of day")
    ax.set_ylabel("Hourly relative change (mmol/L per hour)")
    ax.set_title(f"{pid}: {int(d.trimmed.sum())} of {len(d)} hours trimmed", fontsize=11)
    ax.legend(); ax.grid(which='major', color='#DDDDDD', linewidth=0.8); ax.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5)
    fig.tight_layout()
    out = os.path.join(F, f"TrimmingEffect_{pid}.png")
    fig.savefig(out, dpi=300, bbox_inches="tight"); plt.close(fig)
    print("Saved:", os.path.abspath(out))
