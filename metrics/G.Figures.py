"""
G.Figures.py
Metrics (figures): the figures of the in-silico evaluation in the manuscript,
drawn from the tables of S.CollectScenarioResults.py.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Day1.png, Day2.png                   hourly evaluation of the illustrative
                                         participant (2308): relative bias,
                                         hourly SD, compliance summary
    VariabilityDay1.png, ...Day2.png     SD before vs after, one dot per participant
    MeanDeviationDay1.png, ...Day2.png   delta taMAE per participant
    CompositeStabilityDay1.png, ...Day2.png   composite stability index I

Inputs
    globals.path3, globals.path4, globals.MGDL_PER_MMOL, globals.FIGURE_TITLES
    results/metrics/tables/metrics_by_participant.csv
    results/metrics/tables/hourly_mean_and_std_<id>_Day<k>.csv

Outputs
    results/metrics/figures/*.png   (300 dpi)

Notes
    - Same figure format as the packages of papers 1 and 2 (font size 14 so
      that the text stays legible once the figure is scaled to the page:
      hourly figures at the full text width, bar charts at the full text
      width, the SD scatter at about 0.6 of it),
      light grey grid (#DDDDDD), black zero line, secondary axis rescaled
      from the primary one (the data are drawn once, in mmol/L), 300 dpi,
      titles only if globals.FIGURE_TITLES is set (journals put them in the
      caption).
    - In the hourly figure, an hour without data would get a relative bias
      of 0 (fillna) and count as within +/-15%; with complete simulations
      this does not happen.
    - The values drawn are the same as in the earlier version of this
      script; only the format changed.
    - Day 1 and Day 2 use the same axis limits (SD, delta taMAE, I), so the
      two days can be compared directly; the hourly figures carry the panel
      letters (a), (b), (c) used in their captions.
"""

import os

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
matplotlib.rcParams.update({'font.size': 14});   # readable once scaled to the text width

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
path3 = globals.path3;
path4 = globals.path4;
os.makedirs(path3, exist_ok=True);
MGDL = globals.MGDL_PER_MMOL;          # mmol/L -> mg/dL
ILLUSTRATIVE = globals.ILLUSTRATIVE_ID;   # participant of the hourly evaluation figures (2308)
DAYS = ("Day1", "Day2");
COLOURS = sns.color_palette('pastel');


# -----------------------------------------------------------#
# Figure titles. Journals put the title in the caption, not in
# the image, so this is off for the submitted figures.
# -----------------------------------------------------------#
def figTitle(text, ax=None):
    if globals.FIGURE_TITLES:
        (ax or plt.gca()).set_title(text);


def label(pid):
    """Participant label as written in the manuscript (Mann01 -> Man01)."""
    return "Man" + pid[4:] if pid.startswith("Mann") else pid


def grid(ax):
    ax.grid(which='major', color='#DDDDDD', linewidth=0.8);
    ax.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5);
    ax.set_axisbelow(True);


def mgdl_axis(ax, text):
    # Secondary axis in mg/dL. Rescale only: the data is drawn once on ax.
    axb = ax.twinx();
    axb.set_ylim([v * MGDL for v in ax.get_ylim()]);
    axb.set_ylabel(text);
    axb.grid(False);


def save(name):
    plt.savefig(path3 + name, dpi=300, bbox_inches='tight');
    print("Saved:", os.path.abspath(path3 + name));
    plt.close('all');


m = pd.read_csv(path4 + "metrics_by_participant.csv", dtype={"ID": str});

# Same axis limits on Day 1 and Day 2, so the two days can be compared directly.
SD_TOP = 1.05 * max(m["STD_1_mmolL"].max(), m["STD_2_mmolL"].max()) if len(m) else 1;
TAMAE_TOP = 1.1 * m["DeltaTaMAE_mmolL"].max() if len(m) else 1;
TAMAE_BOTTOM = min(0, 1.1 * m["DeltaTaMAE_mmolL"].min()) if len(m) else 0;
I_TOP = 1.08 * m["Composite_Index"].max() if len(m) else 2;


def panel_label(ax, text):
    # Panel letter, as referred to in the figure caption.
    ax.text(-0.12, 1.04, text, transform=ax.transAxes, fontsize=16, fontweight='bold', va='bottom');

for day in DAYS:
    day_label = f"Day {day[-1]}";

    # -----------------------------------------------------------#
    # Hourly evaluation of the illustrative participant -> Day1.png, Day2.png
    # -----------------------------------------------------------#
    f = path4 + f"hourly_mean_and_std_{ILLUSTRATIVE}_{day}.csv";
    if os.path.isfile(f):
        df = pd.read_csv(f);
        df["relative_bias"] = ((df["BG_2_mean"] - df["BG_1_mean"]) / df["BG_1_mean"] * 100).fillna(0);
        within = (df["relative_bias"].abs() <= 15).mean() * 100;
        lower = (df["BG_2_std"] < df["BG_1_std"]).mean() * 100;

        fig, axes = plt.subplots(1, 3, figsize=(14, 4.8));   # shown at the full text width

        ax = axes[0];
        ax.bar(df["hour"], df["relative_bias"], color=COLOURS[0], edgecolor='black');
        ax.axhline(15, color='red', linestyle='--', label='±15% threshold');
        ax.axhline(-15, color='red', linestyle='--');
        ax.axhline(linewidth=2, color='Black');
        ax.set_xlabel("Hour of day");
        ax.set_ylabel("Relative bias, after vs before (%)");
        ax.set_xticks(range(0, 24, 4));
        grid(ax);
        ax.legend(loc='lower right');
        panel_label(ax, '(a)');
        figTitle("Relative bias (after vs before)", ax);

        ax = axes[1];
        ax.plot(df["hour"], df["BG_1_std"], marker='o', label='Before', color='tab:orange');
        ax.plot(df["hour"], df["BG_2_std"], marker='o', label='After', color='tab:green');
        ax.set_xlabel("Hour of day");
        ax.set_ylabel("Hourly SD of blood glucose (mmol/L)");
        ax.set_xticks(range(0, 24, 4));
        grid(ax);
        ax.legend(loc='upper right');
        panel_label(ax, '(b)');
        figTitle("Standard deviation by hour", ax);
        mgdl_axis(ax, "Hourly SD of blood glucose (mg/dL)");

        ax = axes[2];
        bars = ax.bar(["Within ±15%", "Lower SD after"], [within, lower],
                      color=[COLOURS[0], COLOURS[2]], edgecolor='black', width=0.5);
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2,
                    f"{b.get_height():.1f}%", ha='center');
        ax.set_ylim(0, 122);
        ax.set_yticks(range(0, 101, 20));   # the axis is a percentage: ticks end at 100
        ax.set_ylabel("Hours (%)");
        ax.text(0.5, 114, f"Mean bias: {df['relative_bias'].mean():.2f}%", ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='black'));
        panel_label(ax, '(c)');
        grid(ax);
        figTitle("Compliance summary", ax);

        if globals.FIGURE_TITLES:
            plt.suptitle("Evaluation of the basal insulin adjustment (before vs after)");
        plt.tight_layout();
        save(f"{day}.png");
    else:
        print(f"Skipped {day}.png: {os.path.basename(f)} not found");

    # -----------------------------------------------------------#
    # Cohort figures of the day
    # -----------------------------------------------------------#
    d = m[m["Day"] == day].copy();
    if d.empty:
        print(f"Skipped cohort figures for {day}: no rows");
        continue
    d["Label"] = d["ID"].map(label);
    d = d.sort_values("Label");

    # SD before vs after -> Variability<day>.png
    plt.figure(figsize=(6.5, 6.5));   # shown at about 0.6 of the text width
    ax = plt.gca();
    ax.scatter(d["STD_1_mmolL"], d["STD_2_mmolL"], color=COLOURS[0], edgecolor='black', s=80, zorder=3);
    top = SD_TOP;
    ax.plot([0, top], [0, top], 'r--', label='Identity line (no change)');
    ax.set_xlim(0, top); ax.set_ylim(0, top);
    ax.set_aspect('equal');
    ax.set_xlabel("SD before (mmol/L)");
    ax.set_ylabel("SD after (mmol/L)");
    grid(ax);
    ax.legend(loc='upper left');
    figTitle(f"Glucose variability before vs after the basal adjustment, {day_label}");
    mgdl_axis(ax, "SD after (mg/dL)");
    save(f"Variability{day}.png");

    # delta taMAE -> MeanDeviation<day>.png
    plt.figure(figsize=(12, 8));
    ax = plt.gca();
    ax.bar(d["Label"], d["DeltaTaMAE_mmolL"], color=COLOURS[0], edgecolor='black', width=0.6);
    ax.axhline(linewidth=2, color='Black');
    plt.xticks(rotation=45, ha='right');
    ax.set_xlabel("Participant ID");
    ax.set_ylim(TAMAE_BOTTOM, TAMAE_TOP);
    ax.set_ylabel("ΔtaMAE (mmol/L)");
    grid(ax);
    figTitle(f"Improvement in mean deviation from target (6 mmol/L), {day_label}");
    mgdl_axis(ax, "ΔtaMAE (mg/dL)");
    save(f"MeanDeviation{day}.png");

    # Composite stability index -> CompositeStability<day>.png
    plt.figure(figsize=(12, 8));
    ax = plt.gca();
    ax.bar(d["Label"], d["Composite_Index"], color=COLOURS[4], edgecolor='black', width=0.6);
    ax.axhline(1, color='Black', linestyle='--', linewidth=1.5, label='No change (I = 1)');
    plt.xticks(rotation=45, ha='right');
    ax.set_xlabel("Participant ID");
    ax.set_ylim(0, I_TOP);
    ax.set_ylabel("Composite stability index (I)");
    grid(ax);
    ax.legend(loc='upper right');
    figTitle(f"Composite stability index across participants, {day_label}");
    save(f"CompositeStability{day}.png");
