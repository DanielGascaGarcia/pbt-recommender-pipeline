"""
12.MergeRChBasalNoActZenodo.py
Step 12 (InVivo): put the median within-hour change, its reliability and the
basal insulin on the same minute grid, and draw them together.

Created: 10 May 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Joins the minute medians and flags (10.PivotGeneratormedians) with the
       basal action curve (6.SimulationBasalAutomated, every 5 min).
    2. Carries BasalInfused forward and interpolates ActiveInsulin over the
       minutes between its 5-min values.
    3. Draws two panels: basal rate and its action profile; median relative
       change coloured by reliability (red, yellow, green).

Inputs
    globals.id, globals.fileToSave
    processed/<id>/BGHourRelativeChange<id>0To24medians_wCN.csv   (10.PivotGeneratormediansZenodo.py)
    processed/<id>/BasalSimulated<id>.csv                          (6.SimulationBasalAutomatedZenodo.py)

Output
    processed/<id>/ComparisonJoinedNoActivity<id>.csv
        Key, MedRelChange, Flag, ActiveInsulin, BasalInfused

Figure
    results/invivo/figures/RelativeChange_2308.png (300 dpi), only for the
    illustrative participant (globals.ILLUSTRATIVE_ID): Figure 1 of the manuscript

Notes
    - "NoAct": no activity data are used in this experiment.
    - The figure converts mmol/L to mg/dL with 18.0 (not 18.0182); this
      affects the secondary axis of the figure only.
    - The figure is shown, not saved; it corresponds to Figure 1 of the
      manuscript.
"""

import pandas as pd
import os
from matplotlib import pyplot as plt
import numpy as np
import matplotlib
matplotlib.rcParams.update({'font.size': 15})
import globals
id=globals.id;
# 540,544,552,567,584,596,559,563,570,575,588,591
# id=588;
# id="adolescent#006";
# id="child#010";
# id="adult#001";
# path2: processed/<id>/. Sampling_time = 0.1 h: a point every 6 min in the
# figure. (The commented ids above are from earlier datasets.)
path2= globals.fileToSave;
fileToRead1="BGHourRelativeChange"+str(id);
fileToRead2="BasalSimulated"+str(id);
fileToSave="ComparisonJoinedNoActivity"+str(id);
Sampling_time=0.1;

# -----------------------------------------------------------#
# reading two csv files
# -----------------------------------------------------------#

# data1: minute grid with the hourly median and flag (step 10).
# data2: basal rate and active insulin every 5 minutes (step 6).
data1 = pd.read_csv(str(path2)+str(fileToRead1)+str("0To24")+"medians"+"_wCN"+".csv");
data2 = pd.read_csv(str(path2)+str(fileToRead2)+".csv");

data1['Key']=data1['Key'].str.strip();
# print(data1);
data2['Key']=data2['Key'].str.strip();
# print(data2);

# using merge function by setting how='left'
# Left join on Key: the 5-minute values land on their minutes; the other
# minutes are empty.
output1 = pd.merge(data1,data2,on='Key',how='left');

# Programmed rate holds between its 5-min values; the action curve is interpolated.
output1['BasalInfused'].fillna(method='ffill', inplace=True);
output2=output1.interpolate(limit=5, limit_direction="forward");
# This table is the output of the step; the rest of the script is the figure.
output2.to_csv(str(path2)+str(fileToSave)+".csv",index=False);

# -----------------------------------------------------------#
#             Conversion to arrays (cleaner version)
# -----------------------------------------------------------#
# Convert Key to decimal hours (safer than splitting by :)
key_time = pd.to_timedelta(output2["Key"] + ":00") if output2["Key"].str.count(":").eq(1).all() else pd.to_timedelta(output2["Key"])
key_hours = key_time.dt.total_seconds() / 3600.0

MedRelChange = output2["MedRelChange"].to_numpy()
ActiveInsulin = output2["ActiveInsulin"].to_numpy()
BasalInfused = output2["BasalInfused"].to_numpy()
Reliability = output2["Flag"].to_numpy()

# -----------------------------------------------------------#
#                 Uniform sampling by time
# -----------------------------------------------------------#
# One point every 'Sampling_time' hours (e.g. 0.1 h = 6 min)
Sampling_time = float(Sampling_time)
step = Sampling_time  # hours
# mask: the minutes that fall on a multiple of 0.1 h (every 6 minutes).
mask = np.isclose((key_hours / step) - np.round(key_hours / step), 0, atol=1e-6)

T_Key          = key_hours[mask]
T_MedRelChange = MedRelChange[mask]
T_ActiveInsulin= ActiveInsulin[mask]
T_BasalInfused = BasalInfused[mask]
T_Reliability  = Reliability[mask]

# -----------------------------------------------------------#
#                 Colors by reliability
# -----------------------------------------------------------#
# 1 = Low (Red), 2 = Medium (Yellow), else High (Green)
color_map = {1: "red", 2: "gold", 3: "green"}
colors = np.array([color_map.get(int(v), "green") for v in T_Reliability])

# -----------------------------------------------------------#
#                       Figure and style
# -----------------------------------------------------------#
plt.rcParams.update({"font.size": 12})   # same figure format as papers 1 and 2
fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, figsize=(11, 7))
if globals.FIGURE_TITLES:                # titles go in the caption of the manuscript
    fig.suptitle(f"Blood Glucose Dynamics — ID: {id}", y=0.98, fontsize=14)

# -----------------------------------------------------------#
#                      Insulin panel
# -----------------------------------------------------------#
ax1.set_ylabel("Basal Insulin (U)")
ax1.axhline(0, linewidth=2, color="black")
ax1.plot(T_Key, T_ActiveInsulin, "o", label="Simulated Action Profile")
ax1.plot(T_Key, T_BasalInfused, "o--", label="Preprogrammed Basal Rate")
ax1.grid(which="major", color="#DDDDDD", linewidth=0.8)
ax1.grid(which="minor", color="#DDDDDD", linestyle=":", linewidth=0.5)
major_ticks = np.arange(0, 24 + 1e-9, 5)
minor_ticks = np.arange(0, 24 + 1e-9, 1)
ax1.set_xticks(major_ticks)
ax1.set_xticks(minor_ticks, minor=True)
ax1.legend(loc="upper left")

# -----------------------------------------------------------#
#             Relative Blood Glucose panel
# -----------------------------------------------------------#
# Choose base unit for left axis
BASE_UNIT = "mmol/L"  # change to "mg/dL" if your input is in mg/dL

# Conversion functions
def mmol_to_mg(y):  # mmol/L -> mg/dL
    return y * globals.MGDL_PER_MMOL

def mg_to_mmol(y):  # mg/dL -> mmol/L
    return y / globals.MGDL_PER_MMOL

# Plot series in chosen base unit
if BASE_UNIT.lower() == "mmol/l":
    y_primary = T_MedRelChange
    left_label = "BG Relative Change (mmol/L)"
    sec = ax2.secondary_yaxis('right', functions=(mmol_to_mg, mg_to_mmol))
    sec.set_ylabel("BG Relative Change (mg/dL)")
else:
    y_primary = T_MedRelChange
    left_label = "BG Relative Change (mg/dL)"
    sec = ax2.secondary_yaxis('right', functions=(mg_to_mmol, mmol_to_mg))
    sec.set_ylabel("BG Relative Change (mmol/L)")

# Base line and series
ax2.axhline(0, linewidth=2, color="black")
ax2.plot(T_Key, y_primary, "o--", label="BG Rel. Change (series)", zorder=1)

# Points colored by reliability
# Each reliability label is added to the legend once.
labels_map = {1: "Low reliability of BG", 2: "Medium reliability of BG", 3: "High reliability of BG"}
used = set()
for x, y, r, c in zip(T_Key, y_primary, T_Reliability, colors):
    lbl = labels_map.get(int(r), "High reliability of BG")
    if lbl not in used:
        ax2.plot(x, y, "o", color=c, label=lbl, zorder=2)
        used.add(lbl)
    else:
        ax2.plot(x, y, "o", color=c, zorder=2)

ax2.set_ylabel(left_label)
ax2.set_xlabel("Time (h)")
ax2.grid(which="major", color="#DDDDDD", linewidth=0.8)
ax2.grid(which="minor", color="#DDDDDD", linestyle=":", linewidth=0.5)
ax2.set_xticks(major_ticks)
ax2.set_xticks(minor_ticks, minor=True)

# Reorder legend
handles, labels = ax2.get_legend_handles_labels()
priority = {"Low reliability of BG": 0, "Medium reliability of BG": 1, "High reliability of BG": 2, "BG Rel. Change (series)": 3}
order = np.argsort([priority.get(lbl, 99) for lbl in labels])
ax2.legend([handles[i] for i in order], [labels[i] for i in order], loc="best", fontsize=10, framealpha=0.9)

plt.tight_layout(rect=[0, 0, 1, 0.97])

# -----------------------------------------------------------#
#                     Save the figure
# -----------------------------------------------------------#
# Saved only for the illustrative participant (globals.ILLUSTRATIVE_ID, 2308):
# it is Figure 1 of the manuscript.
if str(id) == globals.ILLUSTRATIVE_ID:
    os.makedirs(globals.path3, exist_ok=True)
    out = os.path.join(globals.path3, f"RelativeChange_{id}.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print("Saved:", os.path.abspath(out))
plt.close("all")
