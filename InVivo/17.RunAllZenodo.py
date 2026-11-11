"""
17.RunAllZenodo.py
InVivo orchestrator: run the InVivo steps for every participant (or the
ones given), one process per script, with a log per participant.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each participant of pairs.csv (or the IDs given):
        1. checks that its four input files are in raw/<id>/ (prepared by
           the data stage: python 17.ScriptforTestExperiment3.py data);
        2. deletes and recreates processed/<id>/;
        3. runs the scripts of SCRIPTS in order, with PATIENT_ID and
           VIRTUAL_ID set and the Agg backend (plt.show() does not block);
        4. checks that the expected outputs exist and are not empty.
    Writes a log per participant and a summary.

Inputs
    globals.PAIRS_FILE (pairs.csv, or sample_data/pairs_demo.csv in demo
    mode), globals.raw_dir, globals.processed_dir

Outputs
    processed/<id>/...   (outputs of the steps)
    logs/<stamp>_<id>.log, logs/<stamp>_summary.csv

Notes
    - 14.SimulationBolusCHOPy-mgipsimZenodo.py is not run here: the basal
      recommendation is produced in the in-silico stage.
    - S.SaveReservedDays.py copies the two days after the analysis window to
      processed/<id>/Days/Day1 and Day2.
    - A participant without its input files is skipped; the run ends with
      exit code 1 if any participant is not "ok".
    - processed/<id>/ is deleted at the start of each participant; raw data
      live elsewhere and are not touched.

Usage (normally through 17.ScriptforTestExperiment3.py invivo [IDs])
    python 17.RunAllZenodo.py               all participants in pairs.csv
    python 17.RunAllZenodo.py zenodo        only public participants
    python 17.RunAllZenodo.py clinical      only clinical participants
    python 17.RunAllZenodo.py 2308 2309     only the IDs given
"""

import csv
import datetime
import os
import shutil
import subprocess
import sys

import globals

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS_FILE = globals.PAIRS_FILE      # pairs.csv, or sample_data/pairs_demo.csv in demo mode
LOG_DIR = os.path.join(HERE, "logs")

SCRIPTS = [
    "0.GeneratorExamplesZenodo.py",
    "3.PivotGeneratorZenodo.py",
    "3.PivotGeneratorBasalZenodo.py",
    "4.MealBolusDetectionZenodo.py",
    "4.MergeBasalZenodo.py",
    "5.MergeBGCleanZenodo.py",
    "5.FillGapsBasalZenodo.py",
    "6.SimulationBasalAutomatedZenodo.py",
    "6.SplitHoursZenodo.py",
    "7.InterpolationBGHourlyZenodo.py",
    "8.RelativeChangeZenodo.py",
    "9.BoxplotZenodo.py",
    "10.PivotGeneratormediansZenodo.py",
    "12.MergeRChBasalNoActZenodo.py",
    "13.InterpolationRChZenodo.py",
    # 14.SimulationBolusCHOPy-mgipsimZenodo.py is NOT run here: the basal
    # recommendation is produced in the in-silico stage (py-mgipsim).
    "0.InterpolationBGHourlyDataZenodo.py",
    # Copies the two days that follow the analysis window (globals.day_split)
    # to processed/{id}/Days/Day1 and Day2, for the later steps.
    "S.SaveReservedDays.py",
]


# -----------------------------------------------------------#
# Helpers
# -----------------------------------------------------------#
def load_pairs():
    """Return [(id, id2, source)] from pairs.csv, skipping comments."""
    pairs = []
    with open(PAIRS_FILE, newline="", encoding="utf-8") as f:
        rows = (line for line in f if line.strip() and not line.lstrip().startswith("#"))
        for row in csv.DictReader(rows):
            source = (row.get("source") or "").strip().lower()
            pairs.append((row["id"].strip(), row["id2"].strip(), source))
    return pairs


def raw_files_present(pid):
    """True if the four input files the pipeline reads are already in raw/{id}/."""
    return all(os.path.isfile(f"{globals.raw_dir(pid)}UoM{k}{pid}.csv")
               for k in ("Glucose", "Nutrition", "Bolus", "Basal"))


def ensure_input_data(pairs):
    """The input files are prepared by the data module (python 17.ScriptforTestExperiment3.py data):
    Zenodo download, conversion of the clinical exports and cleaning. Here we
    only check that they are there; participants without them are skipped."""
    missing = [p for p, _, _ in pairs if not raw_files_present(p)]
    if missing:
        print(f"Input files missing in raw/ for: {', '.join(missing)}. "
              "Run 'python 17.ScriptforTestExperiment3.py data' first; these participants will be skipped.")


def expected_outputs(pid):
    d = globals.processed_dir(pid)
    return [
        f"{d}BGwNMLeftJoined{pid}.csv",
        f"{d}Boxplot{pid}0-24total.csv",
        f"{d}BGHourRelativeChange{pid}0To24medians_wCN.csv",
        f"{d}SampleJoined{pid}.csv",
        f"{d}BGwNMLeftJoinedHourlyInterpolated{pid}.csv",
        f"{d}Days/reserved_days.csv",
    ]


def preflight(pid, vid):
    """Fail early with a clear message instead of deep inside a script."""
    problems = []
    raw = f"{globals.raw_dir(pid)}UoMGlucose{pid}.csv"
    if not os.path.isfile(raw):
        problems.append(f"raw glucose file not found: {raw}")
    return problems


def run_participant(pid, vid, log_path):
    # Start from a clean processed/{id}/ (raw data lives elsewhere, so this is safe)
    out_dir = globals.processed_dir(pid)
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)

    env = os.environ.copy()
    env["PATIENT_ID"] = pid
    env["VIRTUAL_ID"] = vid
    env["MPLBACKEND"] = "Agg"          # plt.show() no longer blocks
    env["PYTHONIOENCODING"] = "utf-8"  # some scripts print non-ASCII characters

    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"Interpreter: {sys.executable}\nPair: {pid} -> {vid}\n\n")
        for script in SCRIPTS:
            log.write(f"===== {script} =====\n")
            log.flush()
            result = subprocess.run(
                [sys.executable, script],
                cwd=HERE, env=env,
                stdout=log, stderr=subprocess.STDOUT,
            )
            if result.returncode != 0:
                return f"failed at {script} (exit {result.returncode})"
    missing = [p for p in expected_outputs(pid)
               if not os.path.isfile(p) or os.path.getsize(p) == 0]
    if missing:
        return "finished but missing/empty: " + ", ".join(os.path.basename(m) for m in missing)
    return "ok"


# -----------------------------------------------------------#
# Main
# -----------------------------------------------------------#
print(f"Interpreter: {sys.executable}")

missing_scripts = [s for s in SCRIPTS if not os.path.isfile(os.path.join(HERE, s))]
if missing_scripts:
    sys.exit("Scripts not found next to the orchestrator: " + ", ".join(missing_scripts))

pairs = load_pairs()
args = sys.argv[1:]
if args == ["zenodo"] or args == ["clinical"]:
    pairs = [p for p in pairs if p[2] == args[0]]
elif args:
    wanted = set(args)
    pairs = [p for p in pairs if p[0] in wanted]
if not pairs:
    sys.exit("No participants to run (check pairs.csv or the arguments given).")

ensure_input_data(pairs)

os.makedirs(LOG_DIR, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
summary = []

for pid, vid, _ in pairs:
    print(f"\n--- {pid} -> {vid} ---")
    problems = preflight(pid, vid)
    if problems:
        status = "skipped: " + "; ".join(problems)
    else:
        log_path = os.path.join(LOG_DIR, f"{stamp}_{pid}.log")
        status = run_participant(pid, vid, log_path)
    print(status)
    summary.append((pid, vid, status))

summary_path = os.path.join(LOG_DIR, f"{stamp}_summary.csv")
with open(summary_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "id2", "status"])
    w.writerows(summary)

n_ok = sum(1 for s in summary if s[2] == "ok")
print(f"\n{n_ok}/{len(summary)} participants ok. Summary: {summary_path}")
if n_ok != len(summary):
    sys.exit(1)
