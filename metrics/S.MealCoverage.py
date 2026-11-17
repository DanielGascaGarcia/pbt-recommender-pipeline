"""
S.MealCoverage.py
Metrics: meal coverage of the four-largest-meals rule, for the values quoted
in the Methods and Limitations of the manuscript.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Evaluation days (the two simulated days per participant): share of
       the day's carbohydrate covered by its four largest meals.
    2. Analysis days (the days that build the composite profile): the same
       share per day and per participant.
    3. Retained glucose: of the readings kept after the meal exclusion, the
       share within 6 h after a meal beyond the four largest of the day, and
       the share from analysis days without any meal record.

Inputs
    globals.ROOT, globals.raw_dir, globals.invivo_dir, globals.sims_root,
    globals.path4, globals.MAX_ANALYSIS_DAYS, globals.RESERVED_DAYS
    raw/<id>/UoMNutrition<id>.csv
    InVivo processed/<id>/_UoMGlucose<id>_<date>.csv, UoMNutrition<id>_<date>.csv
    InSilico/simulations/<id>/Simulation_*/meal_scenarios.csv   (S.BuildMealScenarios.py)

Outputs (in results/metrics/tables/)
    MealCoverage_evaluation_days.csv, MealCoverage_analysis_days.csv,
    MealCoverage_by_participant.csv, MealCoverage_summary.csv

Notes
    - The four largest meals are selected with the same call as
      4.MealBolusDetection.py; entries of 0 g are not counted as meals.
    - The analysis days are recomputed here with the rule of
      globals.day_split (it uses globals._dates on the InVivo folder),
      because day_split reads the folder of the calling module.
    - The shares of retained readings are upper bounds: small meals have
      little effect, and days without a record may be genuinely meal-free.
"""

import glob
import os
import warnings
from datetime import datetime, timedelta

import pandas as pd

import globals

# Silence pandas UserWarnings (date parsing).
warnings.simplefilter("ignore", UserWarning)

ROOT = globals.ROOT
OUT = globals.path4
SIMS = globals.sims_root()
# WINDOW_MIN: the 6-h window after a meal, in minutes.
WINDOW_MIN = globals.MEAL_WINDOW_HOURS * 60


def find_col(df, keys):
    # First column whose name contains one of the keys (the two datasets name
    # their columns differently).
    for c in df.columns:
        if any(k in c.lower() for k in keys):
            return c
    return None


def minutes(key):
    # HH:MM:SS -> minute of the day.
    h, m, s = str(key).strip()[:8].split(":")
    return int(h) * 60 + int(m) + int(s) / 60


def raw_meals(pid):
    """All recorded meals of a participant: date (YYYYMMDD) and grams."""
    f = os.path.join(globals.raw_dir(pid), f"UoMNutrition{pid}.csv")
    if not os.path.isfile(f):
        return None
    r = pd.read_csv(f)
    tcol, ccol = find_col(r, ["ts", "time", "date", "key"]), find_col(r, ["carb", "cho"])
    out = pd.DataFrame({"date": pd.to_datetime(r[tcol], errors="coerce", dayfirst=True).dt.strftime("%Y%m%d"),
                        "g": pd.to_numeric(r[ccol], errors="coerce")})
    return out[out.g > 0]


def share(g):
    # share: number of meals, total grams, grams of the N_MEALS largest.
    g = g.sort_values(ascending=False)
    return len(g), g.sum(), g.head(globals.N_MEALS).sum()


def find(folder, name):
    # First file with that name anywhere under the folder.
    hits = glob.glob(os.path.join(folder, "**", name), recursive=True)
    return hits[0] if hits else None


pids = sorted(d for d in os.listdir(SIMS) if os.path.isdir(os.path.join(SIMS, d)))
ev, an, part = [], [], []

for pid in pids:
    meals = raw_meals(pid)
    if meals is None:
        print(f"[{pid}] raw nutrition file not found; skipped")
        continue

    # 1. Evaluation days
    # Meals of the evaluation days, from meal_scenarios.csv (S.BuildMealScenarios).
    ms = glob.glob(os.path.join(SIMS, pid, "Simulation_*", "meal_scenarios.csv"))
    if len(ms) == 1:
        m = pd.read_csv(ms[0], sep=None, engine="python")
        for _, row in m.iterrows():
            d = pd.to_datetime(str(row["date"]), format="%Y%m%d").strftime("%Y%m%d")
            n, tot, top = share(meals.loc[meals.date == d, "g"])
            ev.append({"ID": pid, "Day": row["day"], "date": d, "meals": n,
                       "total_g": tot, "top4_g": top, "top4_pct": 100 * top / tot if tot else None})

    # 2. Analysis days and 3. retained exposure
    # globals.day_split reads processed/ of the calling module; from metrics/ the
    # per-day glucose files are in InVivo, so the same rule is applied there.
    all_dates = globals._dates(globals.invivo_dir(pid), f"UoMGlucose{pid}_")
    n_an = max(0, min(globals.MAX_ANALYSIS_DAYS, len(all_dates) - globals.RESERVED_DAYS))
    analysis_dates = all_dates[:n_an]
    dates = [str(d) for d in analysis_dates]
    proc = globals.invivo_dir(pid)
    # retained: minutes of the readings kept on each day; windows: the 6-h
    # windows of the meals NOT among the 4 largest; no_meals: days without a meal
    # file.
    retained, windows, no_meals = {}, {d: [] for d in dates}, set()
    for d in dates:
        n, tot, top = share(meals.loc[meals.date == d, "g"])
        if n:
            an.append({"ID": pid, "date": d, "meals": n, "total_g": tot, "top4_g": top,
                       "top4_pct": 100 * top / tot})
        bg = find(proc, f"_UoMGlucose{pid}_{d}.csv")
        if bg is None:
            continue
        b = pd.read_csv(bg)
        # Minutes of the readings kept after the meal exclusion (BGValue not empty).
        retained[d] = [minutes(k) for k, v in zip(b["Key"], b["BGValue"]) if pd.notna(v)]
        mf = find(proc, f"UoMNutrition{pid}_{d}.csv")
        if mf is None:
            no_meals.add(d)
            continue
        dm = pd.read_csv(mf)
        small = dm.drop(index=dm.sort_values(by="CHO", ascending=False).head(globals.N_MEALS).index)  # as 4.MealBolusDetection.py
        small = small[pd.to_numeric(small["CHO"], errors="coerce") > 0]   # 0 g entries (e.g. coffee) carry no meal effect
        # 6-h window of each small meal; the part after midnight goes to the next day.
        for k in small["Key"]:
            t0 = minutes(k)
            t1 = t0 + WINDOW_MIN
            windows[d].append((t0, min(t1, 1440)))
            if t1 > 1440:
                nd = (datetime.strptime(d, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
                windows.setdefault(nd, []).append((0, t1 - 1440))
    # Retained readings, those inside a small-meal window, and those on days
    # without meal records.
    n_ret = sum(len(v) for v in retained.values())
    n_small = sum(sum(any(a <= t <= b for a, b in windows.get(d, [])) for t in v) for d, v in retained.items())
    n_nomeal = sum(len(retained[d]) for d in no_meals if d in retained)
    a = [r for r in an if r["ID"] == pid]
    tot, top = sum(r["total_g"] for r in a), sum(r["top4_g"] for r in a)
    part.append({"ID": pid, "analysis_days": len(dates), "days_with_meals": len(a),
                 "days_over_4_meals": sum(r["meals"] > 4 for r in a),
                 "top4_pct_pooled": 100 * top / tot if tot else None,
                 "retained_readings": n_ret,
                 "after_small_meal_pct": 100 * n_small / n_ret if n_ret else None,
                 "days_without_meal_record": len(no_meals),
                 "on_days_without_meals_pct": 100 * n_nomeal / n_ret if n_ret else None,
                 "_small": n_small, "_nomeal": n_nomeal, "_tot": tot, "_top": top})

# Save the three tables and the cohort summary (pooled over participants).
ev, an, part = pd.DataFrame(ev), pd.DataFrame(an), pd.DataFrame(part)
ev.round(1).to_csv(os.path.join(OUT, "MealCoverage_evaluation_days.csv"), index=False)
an.round(1).to_csv(os.path.join(OUT, "MealCoverage_analysis_days.csv"), index=False)
part.drop(columns=[c for c in part.columns if c.startswith("_")]).round(1).to_csv(
    os.path.join(OUT, "MealCoverage_by_participant.csv"), index=False)

R = part.retained_readings.sum()
summary = {
    "evaluation_days": len(ev),
    "evaluation_days_all_meals_in_top4": int((ev.meals <= 4).sum()),
    "evaluation_top4_pct_mean": ev.top4_pct.mean(),
    "evaluation_top4_pct_min": ev.top4_pct.min(),
    "analysis_days_with_meals": len(an),
    "analysis_top4_pct_pooled": 100 * part._top.sum() / part._tot.sum(),
    "analysis_top4_pct_participant_min": part.top4_pct_pooled.min(),
    "analysis_top4_pct_participant_max": part.top4_pct_pooled.max(),
    "retained_after_small_meal_pct": 100 * part._small.sum() / R,
    "retained_after_small_meal_pct_max": part.after_small_meal_pct.max(),
    "retained_on_days_without_meals_pct": 100 * part._nomeal.sum() / R,
    "retained_on_days_without_meals_pct_max": part.on_days_without_meals_pct.max(),
}
pd.DataFrame([summary]).round(1).to_csv(os.path.join(OUT, "MealCoverage_summary.csv"), index=False)

for k, v in summary.items():
    print(f"{k:42} {round(v, 1)}")
print("Saved: MealCoverage_evaluation_days.csv, MealCoverage_analysis_days.csv,")
print("       MealCoverage_by_participant.csv, MealCoverage_summary.csv in", OUT)
