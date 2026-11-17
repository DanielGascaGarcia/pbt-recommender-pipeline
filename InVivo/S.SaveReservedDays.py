"""
S.SaveReservedDays.py
InVivo, last step: copy the two days that follow the analysis window (the
simulated evaluation days) into their own folders.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each participant, globals.day_split gives the analysis days (up to
    45) and the RESERVED_DAYS days that follow them. Every per-day file of
    each reserved day (glucose, basal, bolus, nutrition, ...) is copied to

        processed/<id>/Days/Day1/   first reserved day
        processed/<id>/Days/Day2/   second reserved day

    The nutrition file is written with the meals of the simulation scenario
    only: the N_MEALS (4) meals with the most carbohydrate (CHO > 0; ties
    broken by the earlier time), ordered by time, as Key and CHO. The other
    files are copied as they are.

Inputs
    globals.day_split, globals.processed_dir, globals.id
    processed/<id>/UoM<Type><id>_<YYYYMMDD>.csv   (0.GeneratorExamplesZenodo.py)

Outputs
    processed/<id>/Days/Day<k>/UoM<Type><id>_<YYYYMMDD>.csv
    processed/<id>/Days/reserved_days.csv   (day, date, files copied)

Notes
    - The 4 meals of each day are the ones simulated in the scenarios; the
      same 4 are used before and after the basal adjustment.
    - A data type with no file on that date (basal files do not always cover
      the same dates as glucose) is reported and skipped.
    - processed/<id>/Days/ is rebuilt on every run.
    - The participant list IDS is only used when the script is run on its
      own without arguments.

Usage
    Run by 17.RunAllZenodo.py for each participant (PATIENT_ID is set).
    On its own (from the InVivo folder):
    python S.SaveReservedDays.py              all participants in IDS
    python S.SaveReservedDays.py Mann04 2301  only these
"""

import glob
import os
import shutil
import sys

import pandas as pd

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
# IDS: used only when the script is run on its own without arguments.
IDS = ["2301", "2304", "2307", "2308", "2309"] + [f"Mann{i:02d}" for i in range(1, 13)]
TYPES = ["Glucose", "Basal", "Bolus", "Nutrition"]
N_MEALS = globals.N_MEALS   # meals per day in the simulation scenario


# -----------------------------------------------------------#
# Helpers
# -----------------------------------------------------------#
def write_top_meals(src, dst, n=N_MEALS):
    """Nutrition file of the scenario: the n largest meals by CHO, by time."""
    d = pd.read_csv(src)
    d.columns = [c.strip() for c in d.columns]
    d["Key"] = d["Key"].astype(str).str.strip()
    d["CHO"] = pd.to_numeric(d["CHO"], errors="coerce")
    d = d[d["CHO"] > 0]
    # The n largest by CHO (ties: the earlier Key first), back in time order.
    top = (d.sort_values(["CHO", "Key"], ascending=[False, True], kind="stable")
             .head(n)
             .sort_values("Key", kind="stable"))
    top[["Key", "CHO"]].to_csv(dst, index=False)


def save_reserved(pid):
    folder = globals.processed_dir(pid)
    # Analysis days and the RESERVED_DAYS (2) days that follow (globals.day_split).
    analysis, reserved = globals.day_split(pid)
    if not reserved:
        print(f"[{pid}] no reserved days (only {len(analysis)} days of data)")
        return

    days_dir = os.path.join(folder, "Days")
    shutil.rmtree(days_dir, ignore_errors=True)   # rebuilt on every run
    log = []
    for k, date in enumerate(reserved, start=1):
        out = os.path.join(days_dir, f"Day{k}")
        os.makedirs(out, exist_ok=True)
        copied = []
        # The four main types; nutrition reduced to the scenario meals.
        for t in TYPES:
            src = os.path.join(folder, f"UoM{t}{pid}_{date}.csv")
            if os.path.isfile(src):
                if t == "Nutrition":
                    write_top_meals(src, os.path.join(out, os.path.basename(src)))
                else:
                    shutil.copy2(src, out)
                copied.append(t)
            else:
                print(f"[{pid}] Day{k} ({date}): no {t} file")
        # any other per-day file of that date (other data types)
        for src in glob.glob(os.path.join(folder, f"UoM*{pid}_{date}.csv")):
            name = os.path.basename(src)
            if not os.path.isfile(os.path.join(out, name)):
                shutil.copy2(src, out)
                copied.append(name)
        log.append({"day": f"Day{k}", "date": date, "copied": " ".join(copied)})
        print(f"[{pid}] Day{k} = {date}: {', '.join(copied) or 'nothing'}")

    # reserved_days.csv: which date is Day1 and Day2, and what was copied.
    pd.DataFrame(log).to_csv(os.path.join(days_dir, "reserved_days.csv"), index=False)
    print(f"[{pid}] analysis days: {len(analysis)} "
          f"({analysis[0]} to {analysis[-1]})")


# -----------------------------------------------------------#
# Main
# -----------------------------------------------------------#
# Who to process: the IDs given, else the participant of the orchestrator,
# else IDS.
if sys.argv[1:]:
    targets = sys.argv[1:]
elif "PATIENT_ID" in os.environ:          # called by 17.RunAllZenodo.py
    targets = [str(globals.id)]
else:
    targets = IDS
for pid in targets:
    save_reserved(pid)
