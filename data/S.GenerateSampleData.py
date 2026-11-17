"""
S.GenerateSampleData.py
Demo mode, step 0: build sample_data/, the input of the demo, from the full
run. It is the first step of every demo run, so the demo always uses the
current data and simulations.

Created: November 2026 (formerly S.BuildSampleData.py)
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each demo participant (default 2308, the illustrative participant of
    the manuscript, from the public T1D-UOM dataset, CC BY 4.0):
        1. copies raw/<id>/UoM{Glucose,Nutrition,Bolus,Basal}<id>.csv
           -> sample_data/<id>/;
        2. copies every .json, .xlsx and .csv of simulator_runs/<id>/ (the
           settings and results of the basal-only run and the four
           scenarios) -> sample_data/simulations/<id>/, keeping the folder
           layout;
        3. writes sample_data/pairs_demo.csv with its row of pairs.csv.

Inputs
    globals.ROOT
    <ROOT>/raw/<id>/, <ROOT>/simulator_runs/<id>/, <ROOT>/pairs.csv

Outputs
    <ROOT>/sample_data/<id>/UoM*.csv
    <ROOT>/sample_data/simulations/<id>/...
    <ROOT>/sample_data/pairs_demo.csv

Notes
    - The paths of the full run are written out here, because in demo mode
      globals points raw_dir, sims_root and PAIRS_FILE to the demo folders.
    - If the full run is not available (a copy of the code with only
      sample_data/), the sample_data/ shipped with the code is used
      unchanged and the script ends without error.
    - Participants of the clinical dataset cannot be redistributed and are
      refused.
    - sample_data/<id>/ and sample_data/simulations/<id>/ are deleted and
      written again on every run.

Usage: run by python 17.ScriptforTestExperiment3.py demo; on its own (from the
data folder, with the project root on PYTHONPATH):
    python S.GenerateSampleData.py            demo participant 2308
    python S.GenerateSampleData.py 2308 2309  other public participants
"""

import csv
import os
import shutil
import sys

import globals

# Paths of the full run, written out here because in demo mode globals points
# raw_dir, sims_root and PAIRS_FILE to the demo folders.
ROOT = globals.ROOT
RAW = os.path.join(ROOT, "raw")
SIMS = os.path.join(ROOT, "simulator_runs")
PAIRS = os.path.join(ROOT, "pairs.csv")
OUT = os.path.join(ROOT, "sample_data")
# KEEP: file types copied from the simulator runs. ids: the IDs given, or 2308.
KEEP = (".json", ".xlsx", ".csv")      # settings, simulator results, meal_scenarios.csv
ids = sys.argv[1:] or ["2308"]

# -----------------------------------------------------------#
# Full run or shipped sample_data/
# -----------------------------------------------------------#
# Everything the copy needs: pairs.csv, and raw/<id>/ and
# simulator_runs/<id>/ of each demo participant.
missing = [p for p in [PAIRS] + [os.path.join(RAW, i) for i in ids] + [os.path.join(SIMS, i) for i in ids]
           if not os.path.exists(p)]
if missing:
    # Without the full run, the sample_data/ shipped with the code is used as it is.
    if os.path.isfile(os.path.join(OUT, "pairs_demo.csv")):
        print("Full run not found here; using the sample_data/ shipped with the code.")
        sys.exit(0)
    sys.exit("Neither the full run (" + ", ".join(missing) + ") nor sample_data/ was found.")

# -----------------------------------------------------------#
# Copy the demo participant(s)
# -----------------------------------------------------------#
# pairs.csv by ID (comment lines skipped).
with open(PAIRS, newline="", encoding="utf-8") as f:
    lines = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
pairs = {r["id"].strip(): r for r in csv.DictReader(lines)}

rows = []
for pid in ids:
    row = pairs.get(pid)
    if row is None:
        sys.exit(f"{pid} is not in pairs.csv")
    # Only public participants: the clinical data cannot be redistributed.
    if row["source"].strip().lower() != "zenodo":
        sys.exit(f"{pid} belongs to the clinical dataset, which cannot be redistributed")
    # The four input files, into a clean sample_data/<id>/.
    dest = os.path.join(OUT, pid)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    for kind in ("Glucose", "Nutrition", "Bolus", "Basal"):
        shutil.copy2(os.path.join(RAW, pid, f"UoM{kind}{pid}.csv"), dest)
    # Every settings, result and scenario file of the simulator runs, keeping the
    # folder layout (Simulation_<id2>/Day1/Before/...).
    src = os.path.join(SIMS, pid)
    sim_dest = os.path.join(OUT, "simulations", pid)
    shutil.rmtree(sim_dest, ignore_errors=True)
    n = 0
    for d, _, files in os.walk(src):
        for name in files:
            if name.endswith(KEEP):
                target = os.path.join(sim_dest, os.path.relpath(d, src))
                os.makedirs(target, exist_ok=True)
                shutil.copy2(os.path.join(d, name), target)
                n += 1
    # Its row of pairs.csv, for pairs_demo.csv.
    rows.append({k: row[k].strip() for k in ("id", "id2", "source")})
    print(f"{pid}: 4 input files and {n} simulation files -> sample_data/")

# -----------------------------------------------------------#
# pairs_demo.csv
# -----------------------------------------------------------#
with open(os.path.join(OUT, "pairs_demo.csv"), "w", newline="", encoding="utf-8") as f:
    f.write("# Demo participant(s): public T1D-UOM data and their py-mgipsim simulations.\n")
    w = csv.DictWriter(f, fieldnames=["id", "id2", "source"])
    w.writeheader()
    w.writerows(rows)
print("Saved sample_data/pairs_demo.csv")
