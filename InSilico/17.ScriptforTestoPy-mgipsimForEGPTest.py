"""
17.ScriptforTestoPy-mgipsimForEGPTest.py
InSilico orchestrator: run the in-silico steps for every participant (or the
ones given). The simulator itself (Py-mgipsim, Python 3.12) is run
separately.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each pair (id, id2) of pairs.csv:
        1. deletes processed/<id>/ (rebuilt from the simulations);
        2. rebuilds the working copy InSilico/simulations/<id>/Simulation_<id2>/
           from the basal-only run kept in simulator_runs/<id>/Simulation_<id2>/
           (simulation_settings.json, state_results.xlsx) and keeps the
           starting settings as simulation_settings_original.json;
        3. runs the scripts of SCRIPTS in order (steps 0-15 and
           S.BuildMealScenarios.py), with PATIENT_ID and VIRTUAL_ID set and
           the Agg backend.
    Writes a log per participant and a summary.

Inputs
    globals.PAIRS_FILE, globals.simulator_runs_root, globals.sims_root
    simulator_runs/<id>/Simulation_<id2>/   basal-only run

Outputs
    InSilico/simulations/<id>/...   recommendation and scenario settings
    logs/<stamp>_insilico_<id>.log, logs/<stamp>_insilico_summary.csv

Notes
    - simulator_runs/ is never modified here; it is the archive of what
      entered and left Py-mgipsim.
    - The scenario results are brought in afterwards by
      metrics/S.SyncSimulatorResults.py, which uses a result only if the
      settings stored with it match the ones written here.
    - A participant without a basal-only run is reported and skipped.

Usage (normally through 17.ScriptforTestExperiment3.py insilico [IDs])
    python 17.ScriptforTestoPy-mgipsimForEGPTest.py            all pairs
    python 17.ScriptforTestoPy-mgipsimForEGPTest.py 2308 2309  only these
"""

import csv
import datetime
import os
import shutil
import subprocess
import sys

# HERE: the InSilico folder (every step runs from it); logs go to
# InSilico/logs/.
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(HERE, "logs")

# pairs.csv: the single list of pairs, kept in the project root
# (sample_data/pairs_demo.csv in demo mode).
import globals
PAIRS_FILE = globals.PAIRS_FILE if os.path.isfile(globals.PAIRS_FILE) else None

# Steps in order. The numbers follow the InVivo steps; the missing ones
# (1, 2, 4, 11) are InVivo steps not needed in silico.
SCRIPTS = [
    "0.GeneratorExamplesPy-mgipsimForEGPtest.py",
    "3.PivotGeneratorZenodo.py",
    "5.MergeBGCompletePy-mgipsimTest.py",
    "5.FillGapsBasalTest.py",
    "6.SimulationBasalAutomatedTest.py",
    "6.SplitHoursTest.py",
    "7.InterpolationBGHourlyTest.py",
    "8.RelativeChangeTest.py",
    "9.BoxplotTest.py",
    "10.PivotGeneratormediansTest.py",
    "12.MergeRChBasalNoActTest.py",
    "13.InterpolationRChTest.py",
    "14.SimulationBolusCHOPy-mgipsimTest.py",
    "15.GeneratorFileToPy-mgipsimTest.py",
    # Before/after meal scenarios of the two evaluation days (Day1, Day2).
    "S.BuildMealScenarios.py",
]


def load_pairs():
    """[(id, id2)] from pairs.csv, skipping comment lines."""
    if PAIRS_FILE is None:
        sys.exit("pairs.csv not found in the project root.")
    with open(PAIRS_FILE, newline="", encoding="utf-8") as f:
        # Lines starting with # are comments; the rest is read as a CSV with the
        # header id,id2,source.
        rows = (line for line in f if line.strip() and not line.lstrip().startswith("#"))
        return [(r["id"].strip(), r["id2"].strip()) for r in csv.DictReader(rows)]


def run_pair(pid, vid, log_path):
    # Start from a clean processed/<id>/, as InVivo does: every intermediate
    # file is rebuilt from the simulations in simulations/<id>/, which are
    # not touched. Same path as globals.processed_dir (demo_output/ in demo mode).
    out = "demo_output" if os.environ.get("DEMO", "0") == "1" else "."
    shutil.rmtree(os.path.join(HERE, out, "processed", pid), ignore_errors=True)
    # The working copy InSilico/simulations/<id>/ is rebuilt from the basal-only
    # run kept in simulator_runs/<id>/Simulation_<id2>/ (never modified here).
    src = os.path.join(globals.simulator_runs_root(), pid, f"Simulation_{vid}")
    files = [f for f in ("simulation_settings.json", "state_results.xlsx")
             if os.path.isfile(os.path.join(src, f))]
    if len(files) < 2:
        return f"no basal-only run in {src} (simulation_settings.json and state_results.xlsx)"
    work = os.path.join(globals.sims_root(), pid)
    shutil.rmtree(work, ignore_errors=True)
    dest = os.path.join(work, f"Simulation_{vid}")
    os.makedirs(dest)
    for f in files:
        shutil.copy2(os.path.join(src, f), dest)
    # starting profile kept by step 15, read by step 0
    shutil.copy2(os.path.join(src, "simulation_settings.json"),
                 os.path.join(dest, "simulation_settings_original.json"))
    # Environment of every step: the pair (read by globals.py), the Agg backend
    # and UTF-8 output.
    env = os.environ.copy()
    env["PATIENT_ID"] = pid
    env["VIRTUAL_ID"] = vid
    env["MPLBACKEND"] = "Agg"          # plt.show() does not block the run
    env["PYTHONIOENCODING"] = "utf-8"
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"Interpreter: {sys.executable}\nPair: {pid} -> {vid}\n\n")
        # The output of each step goes to the participant's log; the first failure
        # stops this participant.
        for script in SCRIPTS:
            log.write(f"===== {script} =====\n")
            log.flush()
            result = subprocess.run([sys.executable, script], cwd=HERE, env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                return f"failed at {script} (exit {result.returncode})"
    return "ok"


# Main part: check the scripts, read the pairs (only the IDs given, if any),
# run each pair, write the summary; exit code 1 if any participant failed.
print(f"Interpreter: {sys.executable}")
missing = [s for s in SCRIPTS if not os.path.isfile(os.path.join(HERE, s))]
if missing:
    sys.exit("Scripts not found next to the orchestrator: " + ", ".join(missing))

pairs = load_pairs()
if sys.argv[1:]:
    wanted = set(sys.argv[1:])
    pairs = [p for p in pairs if p[0] in wanted]
if not pairs:
    sys.exit("No participants to run (check pairs.csv or the arguments given).")

os.makedirs(LOG_DIR, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
summary = []
# Each participant is independent: a failure is recorded and the next one
# is run.
for pid, vid in pairs:
    print(f"\n--- {pid} -> {vid} ---")
    status = run_pair(pid, vid, os.path.join(LOG_DIR, f"{stamp}_insilico_{pid}.log"))
    print(status)
    summary.append((pid, vid, status))

path = os.path.join(LOG_DIR, f"{stamp}_insilico_summary.csv")
with open(path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "id2", "status"])
    w.writerows(summary)
n_ok = sum(1 for s in summary if s[2] == "ok")
print(f"\n{n_ok}/{len(summary)} participants ok. Summary: {path}")
if n_ok != len(summary):
    sys.exit(1)
