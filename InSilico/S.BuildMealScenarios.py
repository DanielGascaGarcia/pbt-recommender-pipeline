"""
S.BuildMealScenarios.py
InSilico, last step: write the meal scenarios of the two evaluation days of
one participant, before and after the recommendation, as Py-mgipsim
settings files ready to simulate.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each evaluation day (Day1, Day2):
        - meals: the N_MEALS (4) meals with the most carbohydrate of the day
          (CHO > 0; ties broken by the earlier time), by time;
        - one bolus per meal, at the same minute: CHO / carb_insulin_ratio
          of the virtual patient;
        - snacks set to 0 g;
        - basal: the starting profile (Before) or the recommended profile
          (After). Everything else is kept from the settings.

Inputs
    globals.id, globals.id2, globals.sim_dir, globals.invivo_dir
    Simulation_<id2>/simulation_settings_original.json   (Before)
    Simulation_<id2>/simulation_settings.json            (After, step 15)
    InVivo processed/<id>/Days/Day<k>/UoMNutrition<id>_<date>.csv   (S.SaveReservedDays.py)

Outputs (in InSilico/simulations/<id>/Simulation_<id2>/)
    Day<k>/Before/simulation_settings.json
    Day<k>/After/simulation_settings.json
    meal_scenarios.csv   (day, date, meals, total CHO, ICR, times)

Notes
    - Before and After have exactly the same meals and boluses; only the
      basal profile differs.
    - The meal duration is taken from the first meal of the template.
    - The boluses use the ICR of the virtual patient, not the participant's.
"""

import copy
import glob
import json
import os
import sys

import pandas as pd

import globals

# N_MEALS = 4 (globals.py); the two evaluation days.
N_MEALS = globals.N_MEALS
DAYS = ("Day1", "Day2")


def load_meals(nutrition_csv, n=N_MEALS):
    """(CHO list, minute list) of the n largest meals by CHO, ordered by time."""
    # Meal records of the day: clean the column names and times, keep CHO > 0,
    # minute of the day from HH:MM.
    d = pd.read_csv(nutrition_csv)
    d.columns = [c.strip() for c in d.columns]
    d["Key"] = d["Key"].astype(str).str.strip()
    d["CHO"] = pd.to_numeric(d["CHO"], errors="coerce")
    d = d[d["CHO"] > 0]
    d = d.assign(minute=d["Key"].str.slice(0, 2).astype(int) * 60
                 + d["Key"].str.slice(3, 5).astype(int))
    # The n largest by CHO (ties: the earlier first), put back in time order.
    top = (d.sort_values(["CHO", "minute"], ascending=[False, True], kind="stable")
             .head(n)
             .sort_values("minute", kind="stable"))
    # CHO as int when it is a whole number (keeps the JSON tidy).
    cho = [int(v) if float(v).is_integer() else float(v) for v in top["CHO"]]
    return cho, [int(v) for v in top["minute"]]


def build(template, cho, minutes):
    """Copy of the settings with the meal scenario written into its inputs."""
    # ICR (g/U) and meal duration of the virtual patient, from the template.
    s = copy.deepcopy(template)
    icr = float(s["patient"]["demographic_info"]["carb_insulin_ratio"][0])
    meal_duration = float(s["inputs"]["meal_carb"]["duration"][0][0])
    # Meals: the selected CHO at their minutes.
    s["inputs"]["meal_carb"] = {
        "magnitude": [cho],
        "start_time": [minutes],
        "duration": [[meal_duration] * len(cho)],
    }
    # One bolus per meal: CHO / ICR, at the same minute, lasting 1 minute.
    s["inputs"]["bolus_insulin"] = {
        "magnitude": [[c / icr for c in cho]],
        "start_time": [minutes],
        "duration": [[1.0] * len(cho)],
    }
    # Snacks of the template set to 0 g.
    snack = s["inputs"].get("snack_carb")
    if snack and snack.get("magnitude"):
        snack["magnitude"] = [[0.0] * len(snack["magnitude"][0])]
    return s, icr


# Before = starting profile; After = recommended profile (step 15). Stop if
# either is missing.
pid, vid = globals.id, globals.id2
sim = globals.sim_dir(vid, pid)
settings = {
    "Before": os.path.join(sim, "simulation_settings_original.json"),
    "After": os.path.join(sim, "simulation_settings.json"),
}
for label, path in settings.items():
    if not os.path.isfile(path):
        sys.exit(f"[{pid}] {label}: settings not found: {path}")
templates = {k: json.load(open(v, encoding="utf-8")) for k, v in settings.items()}

rows = []
# For each evaluation day: its single nutrition file (saved by InVivo), its
# meals, and the two scenarios with the same meals.
for day in DAYS:
    found = glob.glob(os.path.join(globals.invivo_dir(pid), "Days", day,
                                   f"UoMNutrition{pid}_*.csv"))
    if len(found) != 1:
        sys.exit(f"[{pid}] {day}: expected one nutrition file, found {len(found)}")
    cho, minutes = load_meals(found[0])
    # Date from the file name: the 8 digits before .csv.
    date = os.path.basename(found[0])[-12:-4]
    for label, template in templates.items():
        scenario, icr = build(template, cho, minutes)
        out_dir = os.path.join(sim, day, label)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "simulation_settings.json"), "w",
                  encoding="utf-8") as f:
            json.dump(scenario, f, indent=4)
    rows.append({"day": day, "date": date, "meals": len(cho),
                 "CHO_total_g": sum(cho), "carb_insulin_ratio": icr,
                 "times": " ".join(f"{t // 60:02d}:{t % 60:02d}" for t in minutes)})
    print(f"[{pid}] {day} ({date}): {len(cho)} meals, {sum(cho)} g, ICR {icr} g/U")

pd.DataFrame(rows).to_csv(os.path.join(sim, "meal_scenarios.csv"), index=False)
