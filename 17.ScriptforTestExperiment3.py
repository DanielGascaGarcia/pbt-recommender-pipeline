"""
17.ScriptforTestExperiment3.py
Launcher of the experiment-3 pipeline, run from the project root (Code3/).

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Runs one module, or the whole pipeline in demo mode. Each module runs
    from its own folder, with the project root on PYTHONPATH so that every
    script imports the single globals.py.
        data      input data -> raw/<id>/: T1D-UOM files from Zenodo,
                  clinical exports converted to the same format, then
                  repeated records removed
        invivo    real data -> composite day, guide curve, evaluation days,
                  virtual-patient matching
        insilico  basal recommendation and meal scenarios (after the
                  basal-only simulations have been run in Py-mgipsim)
        metrics   metrics, tables and figures of the before/after scenarios
                  (after the scenarios have been simulated in Py-mgipsim)

Outputs
    whatever each module writes; data and metrics also save their screen
    output to <module>/logs/<module>_<date>_<time>.txt

Notes
    - metrics empties results/metrics/ before each run (demo_output/results/
      in demo mode), so no table of an earlier run is left behind.
    - Demo mode replaces the data stage by data/S.GenerateSampleData.py and
      data/S.PrepareDemo.py and runs data -> invivo -> insilico -> metrics on
      participant 2308.
    - The Py-mgipsim steps are run separately, in the simulator environment.

Usage
    python 17.ScriptforTestExperiment3.py demo                  whole pipeline on the demo data
    python 17.ScriptforTestExperiment3.py                       menu (modules 1-4, 5 = demo)
    python 17.ScriptforTestExperiment3.py data                  prepare raw/ (before invivo)
    python 17.ScriptforTestExperiment3.py invivo                one module, all participants
    python 17.ScriptforTestExperiment3.py insilico Mann01 2308  one module, only these participants
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# module key -> (folder name, scripts to run in order, accepts participant IDs)
MODULES = {
    "data":     ("data",   ["S.GetZenodoData.py", "S.ConvertClinicalData.py --to-raw",
                              "S.CleanRawData.py"], False),
    "invivo":   ("InVivo",   ["17.RunAllZenodo.py", "S.BasalMatching.py"], True),
    "insilico": ("InSilico", ["17.ScriptforTestoPy-mgipsimForEGPTest.py"], True),
    "metrics":  ("metrics",  ["S.SyncSimulatorResults.py", "S.CollectScenarioResults.py", "S.MealCoverage.py", "S.InputDescriptives.py", "S.CurveAgreement.py", "S.TrimmingEffect.py", "S.PowerAnalysisTest.py",
                              "G.Figures.py", "G.CurveCheck.py", "G.ScenarioPlot.py",
                              "G.TrimmingEffect.py"], False),
}
ORDER = ["data", "invivo", "insilico", "metrics"]
# Demo mode: "python 17.ScriptforTestExperiment3.py demo" (or DEMO=1). The data stage first rebuilds
# sample_data/ from the full run (when it is present; otherwise the shipped
# sample_data/ is used), then places its py-mgipsim simulations where InSilico
# and metrics read them; every output goes to demo_output/, and the files of
# the full run are never touched.
DEMO = os.environ.get("DEMO", "0") == "1"


def set_demo():
    global DEMO
    DEMO = True
    os.environ["DEMO"] = "1"                 # inherited by every script run below
    MODULES["data"] = ("data", ["S.GenerateSampleData.py", "S.PrepareDemo.py"], False)


if DEMO:
    set_demo()
# Modules whose screen output is also saved to <module folder>/logs/
# <module>_<date>_<time>.txt, as InVivo and InSilico keep their own logs (one per
# participant and a summary) in InVivo/logs/ and InSilico/logs/.
LOGGED = {"data", "metrics"}
# Modules whose results/<module>/ folder is emptied before each run, so that no
# table or figure of an earlier run (for example of a participant no longer in
# the simulations) is left behind. metrics always runs on every participant.
CLEAN_RESULTS = {"metrics"}
NOTES = {
    "data":     "input data -> raw/ (Zenodo files, clinical exports, cleaning)",
    "invivo":   "real data -> composite day, guide curve, evaluation days",
    "insilico": "needs the basal-only simulations in simulator_runs/",
    "metrics":  "needs the scenario results in simulator_runs/ (checked against the settings)",
}


def find_folder(name):
    """Module folder in the root, matched without regard to case."""
    for entry in os.listdir(ROOT):
        if entry.lower() == name.lower() and os.path.isdir(os.path.join(ROOT, entry)):
            return os.path.join(ROOT, entry)
    return None


def run(key, ids):
    folder_name, scripts, takes_ids = MODULES[key]
    folder = find_folder(folder_name)
    if folder is None:
        print(f"Folder not found: {os.path.join(ROOT, folder_name)}")
        return 1
    missing = [s.split()[0] for s in scripts if not os.path.isfile(os.path.join(folder, s.split()[0]))]
    if missing:
        print("Script not found: " + ", ".join(os.path.join(folder, s) for s in missing))
        return 1
    if ids and not takes_ids:
        print(f"{folder_name} runs on every participant; the IDs given are ignored.")
        ids = []
    if key in CLEAN_RESULTS:
        # demo_output/results/ in demo mode: the results of the full run are never touched
        base = os.path.join(ROOT, "demo_output") if DEMO else ROOT
        shutil.rmtree(os.path.join(base, "results", key), ignore_errors=True)
        print(f"Cleared {os.path.relpath(os.path.join(base, 'results', key), ROOT)}/ (rebuilt in this run).")
    log = None
    if key in LOGGED:
        os.makedirs(os.path.join(folder, "logs"), exist_ok=True)
        log_path = os.path.join(folder, "logs", f"{key}_{datetime.now():%Y%m%d_%H%M%S}.txt")
        log = open(log_path, "w", encoding="utf-8")
    try:
        for script in scripts:
            cmd = [sys.executable] + script.split() + ids
            header = f"\n=== {folder_name}: {' '.join(cmd[1:])} ===\n"
            print(header)
            env = os.environ.copy()
            env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
            env["PBT_MODULE_DIR"] = folder
            if log is None:
                code = subprocess.run(cmd, cwd=folder, env=env).returncode
            else:
                # Same output on screen and in the log file.
                env["PYTHONUNBUFFERED"] = "1"
                log.write(header + "\n")
                p = subprocess.Popen(cmd, cwd=folder, env=env, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     encoding="utf-8", errors="replace")
                for line in p.stdout:
                    print(line, end="")
                    log.write(line)
                code = p.wait()
            if code != 0:
                return code
        return 0
    finally:
        if log is not None:
            log.close()
            print(f"\nLog: {log_path}")


def run_demo():
    """The whole pipeline on the demo data (2308): sample_data/ -> demo_output/."""
    set_demo()
    print(f"Interpreter: {sys.executable}   [DEMO: sample_data/ -> demo_output/]")
    code = 0
    for key in ORDER:                    # data -> invivo -> insilico -> metrics
        code = run(key, [])
        if code != 0:
            print(f"\nDemo stopped at {key}.")
            return code
    print("\nDemo finished. Results in demo_output/results/.")
    return code


def menu():
    print(f"Interpreter: {sys.executable}" + ("   [DEMO mode]" if DEMO else "") + "\n")
    print("Which module do you want to run?")
    for n, key in enumerate(ORDER, start=1):
        print(f"  {n}. {MODULES[key][0]:9} {NOTES[key]}")
    print(f"  {len(ORDER) + 1}. demo      whole pipeline on the demo data (2308), no simulator needed")
    print("  0. Exit")
    choice = input("\nOption: ").strip()
    if choice in ("", "0"):
        return 0
    if choice == str(len(ORDER) + 1) or choice.lower() == "demo":
        return run_demo()
    if not choice.isdigit() or not 1 <= int(choice) <= len(ORDER):
        print("Not a valid option.")
        return 1
    key = ORDER[int(choice) - 1]
    ids = []
    if MODULES[key][2]:
        typed = input("Participant IDs separated by spaces (Enter = all): ").strip()
        ids = typed.split()
    return run(key, ids)


args = sys.argv[1:]
if args and args[0].lower() in ("demo", "--demo"):
    sys.exit(run_demo())
if not args:
    code = menu()
elif args[0].lower() in MODULES:
    code = run(args[0].lower(), args[1:])
else:
    print("Usage: python 17.ScriptforTestExperiment3.py [demo|data|invivo|insilico|metrics] [IDs...]")
    code = 1
sys.exit(code)
