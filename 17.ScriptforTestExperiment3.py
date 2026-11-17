"""
17.ScriptforTestExperiment3.py
Launcher of the experiment 3 (paper 3) pipeline: the recommender of the
Personalised Basal Tuner and its in silico evaluation. Run from the project
root.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Decides what to run: one module (from the command line or the menu),
       or the whole pipeline in demo mode.
    2. Demo mode: replaces the data stage by the demo stage, which prepares
       participant 2308 from sample_data/; every output goes to demo_output/.
    3. For each module, in order: checks that its folder and scripts exist,
       empties results/metrics/ before metrics, and runs its scripts from the
       module folder with the project root on PYTHONPATH, so that every script
       imports the single globals.py.
    4. Stops at the first script that fails: each module reads what the one
       before it wrote, so carrying on would use an incomplete set.
    5. Prints a summary of what ran and what failed.

Modules
    data      input data -> raw/<id>/: T1D-UOM files from Zenodo, clinical
              exports converted to the same format, then repeated records
              removed
    invivo    real data -> composite day, guide curve, evaluation days,
              virtual-patient matching
    insilico  basal recommendation and meal scenarios (after the basal-only
              simulations have been run in Py-mgipsim)
    metrics   metrics, tables and figures of the before/after scenarios
              (after the scenarios have been simulated in Py-mgipsim)

Outputs
    whatever each module writes; data and metrics also save their screen
    output to <module>/logs/<module>_<date>_<time>.txt

Notes
    - The Py-mgipsim steps are run separately, in the simulator environment.
    - invivo and insilico accept participant IDs; data and metrics always run
      on every participant.

Usage
    python 17.ScriptforTestExperiment3.py demo                  whole pipeline on the demo data
    python 17.ScriptforTestExperiment3.py                       menu (modules 1-4, 5 = demo)
    python 17.ScriptforTestExperiment3.py data                  prepare raw/ (before invivo)
    python 17.ScriptforTestExperiment3.py invivo                one module, all participants
    python 17.ScriptforTestExperiment3.py insilico Mann01 2308  one module, only these participants
"""

# ------------------------------------------------------------------ #
# Imports
# ------------------------------------------------------------------ #
# Only the standard library: the launcher must run before anything else is
# installed or prepared, and must not depend on the pipeline's packages.
import os                        # paths, folders, environment variables
import shutil                    # rmtree: empties results/metrics/ before a run
import subprocess                # runs each script as a separate Python process
import sys                       # command-line arguments, interpreter, exit code
from datetime import datetime    # date and time in the name of each log file

# Project root = the folder that holds this launcher (and globals.py,
# pairs.csv, the module folders). Taken from the file itself, not from the
# current directory, so the launcher works wherever it is called from.
ROOT = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ #
# Modules
#
# DATA      input data -> raw/. Everything else depends on it.
# INVIVO    real data -> composite day, guide curve, evaluation days and
#           the virtual-patient matching (17.RunAllZenodo.py runs steps 0-13)
# INSILICO  the same steps on the basal-only simulation, the recommended
#           basal profile and the meal scenarios
# METRICS   reads the simulated scenarios; must run last
#
# Each list holds the scripts of one module, in the order they are run.
# A script name may carry fixed arguments after a space (see
# "S.ConvertClinicalData.py --to-raw"): the launcher splits the string, so
# the first word is the script and the rest are passed to it.
# ------------------------------------------------------------------ #
DATA = [
    "S.GetZenodoData.py",                  # downloads the T1D-UOM participants (ZENODO_RECORD in globals.py)
    "S.ConvertClinicalData.py --to-raw",   # converts the clinical exports to the T1D-UOM file format
    "S.CleanRawData.py",                   # removes blank rows, copies and repeated records (keeps originals)
]

INVIVO = [
    "17.RunAllZenodo.py",    # orchestrator of InVivo: steps 0-13 for every participant in pairs.csv
    "S.BasalMatching.py",    # daily basal and bolus per participant -> Table 1 and virtual patient
]

INSILICO = [
    "17.ScriptforTestoPy-mgipsimForEGPTest.py",   # orchestrator of InSilico: steps 0-15 on the
                                                  # simulated day, then the meal scenarios
]

METRICS = [
    "S.SyncSimulatorResults.py",     # keeps only results simulated with the current settings
    "S.CollectScenarioResults.py",   # metrics of every participant and day
    "S.MealCoverage.py",             # descriptive tables
    "S.InputDescriptives.py",
    "S.CurveAgreement.py",
    "S.TrimmingEffect.py",
    "S.PowerAnalysisTest.py",        # planned paired t test
    "G.Figures.py",                  # figures of the article
    "G.CurveCheck.py",               # per-participant checks
    "G.ScenarioPlot.py",
    "G.TrimmingEffect.py",
]
# Convention of the file names: S. = script that computes and saves tables,
# G. = script that draws figures; numbered scripts (0., 1., ... 17.) are the
# steps of the method, in order.

# Demo stage: replaces DATA in demo mode.
DEMO_DATA = [
    "S.GenerateSampleData.py",   # rebuilds sample_data/ from the full run, when that run is present
    "S.PrepareDemo.py",          # places the demo's simulator runs where InSilico and metrics read them
]

# module key -> (folder name, scripts in order, accepts participant IDs)
# The key is what is typed on the command line (lower case); the folder name
# is the folder on disk (InVivo and InSilico keep their capital letters).
MODULES = {
    "data":     ("data",     DATA,     False),
    "invivo":   ("InVivo",   INVIVO,   True),
    "insilico": ("InSilico", INSILICO, True),
    "metrics":  ("metrics",  METRICS,  False),
}
# Order of the pipeline: used by the menu numbering and by demo mode, which
# runs the four modules one after another.
ORDER = ["data", "invivo", "insilico", "metrics"]

# Modules whose screen output is also saved to <module folder>/logs/;
# InVivo and InSilico keep their own logs (one per participant).
LOGGED = {"data", "metrics"}

# Modules whose results/<module>/ is emptied before each run, so that no
# table or figure of an earlier run (for example, of a participant no longer
# in the simulations) is left behind. metrics always runs on every participant.
# (InVivo and InSilico are not here: they can run on a few participants, and
# emptying their results would delete the tables of the others.)
CLEAN_RESULTS = {"metrics"}

# One line per module, shown next to it in the menu.
NOTES = {
    "data":     "input data -> raw/ (Zenodo files, clinical exports, cleaning)",
    "invivo":   "real data -> composite day, guide curve, evaluation days",
    "insilico": "needs the basal-only simulations in simulator_runs/",
    "metrics":  "needs the scenario results in simulator_runs/ (checked against the settings)",
}

# ------------------------------------------------------------------ #
# What to run
# ------------------------------------------------------------------ #
# Demo mode is chosen with "demo" on the command line, option 5 of the menu,
# or DEMO=1 in the environment.
demo = os.environ.get("DEMO", "0") == "1"   # True only if DEMO=1 was already set
to_run = []                                 # module keys to run, in order
ids = []                                    # participant IDs (empty = all participants)
args = sys.argv[1:]                         # what was typed after the script name

# Show which Python is running: the pipeline needs its own environment
# (Python 3.9.12, pbt_test), not the simulator's (Python 3.12).
print(f"Interpreter: {sys.executable}" + ("   [DEMO mode]" if demo else "") + "\n")

# Case 1: "demo" (or "--demo") -> the four modules, in order, on the demo data.
if args and args[0].lower() in ("demo", "--demo"):
    demo = True
    to_run = list(ORDER)
# Case 2: a module name -> that module only; anything after it is taken as
# participant IDs (for example: insilico Mann01 2308).
elif args and args[0].lower() in MODULES:
    to_run = [args[0].lower()]
    ids = args[1:]
# Case 3: something else was typed -> show how to call it and stop.
elif args:
    print("Usage: python 17.ScriptforTestExperiment3.py [demo|data|invivo|insilico|metrics] [IDs...]")
    sys.exit(1)
# Case 4: nothing was typed -> interactive menu.
else:
    print("Which module do you want to run?")
    # Options 1-4: the modules, numbered in pipeline order.
    for n, key in enumerate(ORDER, start=1):
        print(f"  {n}. {MODULES[key][0]:9} {NOTES[key]}")
    # Option 5: the demo (its number follows the last module).
    print(f"  {len(ORDER) + 1}. demo      whole pipeline on the demo data (2308), no simulator needed")
    print("  0. Exit")
    choice = input("\nOption: ").strip()
    # Enter or 0 -> leave without running anything (exit code 0: not an error).
    if choice in ("", "0"):
        sys.exit(0)
    # 5 (or the word "demo") -> demo mode.
    if choice == str(len(ORDER) + 1) or choice.lower() == "demo":
        demo = True
        to_run = list(ORDER)
    # 1-4 -> one module.
    elif choice.isdigit() and 1 <= int(choice) <= len(ORDER):
        to_run = [ORDER[int(choice) - 1]]
        # Only InVivo and InSilico accept IDs, so only they ask for them.
        if MODULES[to_run[0]][2]:
            ids = input("Participant IDs separated by spaces (Enter = all): ").strip().split()
    # Anything else -> stop.
    else:
        print("Not a valid option.")
        sys.exit(1)

# ------------------------------------------------------------------ #
# Demo mode
# ------------------------------------------------------------------ #
# The data stage first rebuilds sample_data/ from the full run (when it is
# present; otherwise the shipped sample_data/ is used), then places its
# Py-mgipsim simulations where InSilico and metrics read them. Every output
# goes to demo_output/; the files of the full run are never touched.
if demo:
    # Setting it in os.environ here means every script started below inherits
    # it; globals.py reads DEMO and switches its input and output folders.
    os.environ["DEMO"] = "1"                 # inherited by every script run below
    # In demo mode the data module runs the demo scripts instead of the
    # download, conversion and cleaning (no clinical data is needed).
    MODULES["data"] = ("data", DEMO_DATA, False)
    print("========== DEMO MODE: participant 2308, sample_data/ -> demo_output/ ==========\n")

# ------------------------------------------------------------------ #
# Run the modules
# ------------------------------------------------------------------ #
failures = []    # (module, script, exit code) of what failed; at most one, since the run stops there
completed = []   # modules whose every script finished without error
logs = []        # paths of the log files written in this run

for key in to_run:
    folder_name, scripts, takes_ids = MODULES[key]
    print(f"\n{'=' * 58}")
    print(f"  Module {folder_name}")
    print(f"{'=' * 58}\n")

    # Module folder, matched without regard to case (InVivo / invivo).
    # (On Windows the folder may have been copied as "invivo"; on Linux the
    # case matters, so the folder is looked up instead of assumed.)
    folder = None
    for entry in os.listdir(ROOT):
        if entry.lower() == folder_name.lower() and os.path.isdir(os.path.join(ROOT, entry)):
            folder = os.path.join(ROOT, entry)
    if folder is None:
        print(f"  Folder not found: {os.path.join(ROOT, folder_name)}")
        failures.append((folder_name, "(folder)", 1))
        break

    # Fail early if a script is missing, rather than halfway through.
    # s.split()[0] keeps only the script name, without its fixed arguments.
    missing = [s.split()[0] for s in scripts if not os.path.isfile(os.path.join(folder, s.split()[0]))]
    if missing:
        for s in missing:
            print(f"  Script not found: {os.path.join(folder, s)}")
        failures.append((folder_name, ", ".join(missing), 1))
        break

    # data and metrics always run on every participant: IDs given for them
    # are ignored, with a message, instead of being passed to their scripts.
    module_ids = ids
    if ids and not takes_ids:
        print(f"  {folder_name} runs on every participant; the IDs given are ignored.")
        module_ids = []

    # -----------------------------------------------------------#
    # Empty results/<module>/ (demo_output/results/ in demo mode)
    # -----------------------------------------------------------#
    # Done before the module runs, so its results come only from this run.
    # ignore_errors=True: no error if the folder does not exist yet.
    if key in CLEAN_RESULTS:
        base = os.path.join(ROOT, "demo_output") if demo else ROOT
        shutil.rmtree(os.path.join(base, "results", key), ignore_errors=True)
        print(f"  Cleared {os.path.relpath(os.path.join(base, 'results', key), ROOT)}/ (rebuilt in this run).")

    # Log file of the module (data and metrics only): one per run, named by
    # date and time so earlier logs are never overwritten.
    log = None
    if key in LOGGED:
        os.makedirs(os.path.join(folder, "logs"), exist_ok=True)
        log_path = os.path.join(folder, "logs", f"{key}_{datetime.now():%Y%m%d_%H%M%S}.txt")
        log = open(log_path, "w", encoding="utf-8")
        logs.append(log_path)

    # Environment of the scripts: a copy of the current one, plus
    #   PYTHONPATH      the project root first, so "import globals" finds the
    #                   single globals.py from inside any module folder;
    #   PBT_MODULE_DIR  the module folder, which globals.py uses to place
    #                   processed/ and results/<module>/.
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env["PBT_MODULE_DIR"] = folder

    for script in scripts:
        # Command: this same Python + script + its fixed arguments + the IDs.
        # sys.executable makes every script run in the launcher's environment.
        cmd = [sys.executable] + script.split() + module_ids
        print(f"\n  -> {' '.join(cmd[1:])}\n")
        if log is None:
            # No log: the script writes straight to the screen.
            # cwd=folder: each script runs from its own module folder.
            code = subprocess.run(cmd, cwd=folder, env=env).returncode
        else:
            # Same output on screen and in the log file.
            # PYTHONUNBUFFERED=1: the script sends each line as soon as it is
            # printed, so the screen shows progress live instead of in blocks.
            env["PYTHONUNBUFFERED"] = "1"
            log.write(f"\n=== {folder_name}: {' '.join(cmd[1:])} ===\n\n")
            # stderr=STDOUT: errors and warnings go to the same stream, so the
            # log also keeps the traceback of a failure. errors="replace":
            # a character that cannot be decoded never stops the launcher.
            p = subprocess.Popen(cmd, cwd=folder, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True,
                                 encoding="utf-8", errors="replace")
            # Each line read from the script is printed and written to the log.
            for line in p.stdout:
                print(line, end="")
                log.write(line)
            code = p.wait()   # exit code of the script once it has finished
        # Exit code other than 0 = the script failed: stop this module.
        if code != 0:
            print(f"     FAILED (exit {code}) — stopping")
            failures.append((folder_name, script, code))
            break

    # Close the log (also after a failure, so its last lines are saved).
    if log is not None:
        log.close()
    # A failure also stops the modules that follow: they would read what this
    # one did not finish writing.
    if failures:
        break
    completed.append(folder_name)

# ------------------------------------------------------------------ #
# Summary — so a failure buried 200 lines up is not missed
# ------------------------------------------------------------------ #
print(f"\n{'=' * 58}")
print("  SUMMARY")
print(f"{'=' * 58}")
print(f"  Modules requested : {', '.join(MODULES[k][0] for k in to_run)}")
print(f"  Modules completed : {', '.join(completed) if completed else 'none'}")
for path in logs:
    print(f"  Log               : {path}")

if failures:
    print(f"\n  {len(failures)} failure(s):")
    for module, script, code in failures:
        print(f"    {module:<9} {script:<44} exit {code}")
    print("\n  The modules after a failure were not run: each one reads what the")
    print("  one before it wrote. Fix the error above and re-run.\n")
    # Exit code 1: whoever called the launcher (a terminal, a script, CI)
    # can tell that the run did not finish.
    sys.exit(1)

print("\n  No failures.")
if demo:
    print("\n  Demo run on participant 2308. Results in demo_output/results/.")
