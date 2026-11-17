"""
globals.py
Configuration of the whole experiment-3 pipeline: one file, in the project
root (Code3/), imported by every module (data/, InVivo/, InSilico/, metrics/).

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Sets the paths, the participant of the run and the shared constants:
        ROOT, HERE       project root and folder of the module being run
                         (PBT_MODULE_DIR, set by the launcher)
        PAIRS_FILE       pairs.csv (sample_data/pairs_demo.csv in demo mode)
        id, id2          participant and virtual patient of the run
                         (PATIENT_ID, VIRTUAL_ID; defaults 2308, Patient_5)
        raw_dir, processed_dir, invivo_dir, sim_dir, sims_root,
        simulator_runs_root   folders of each stage
        path3, path4     results/<module>/figures/ and tables/
        path             virtual-patient files of Py-mgipsim (PYMGIPSIM_PATIENTS)
        ZENODO_RECORD    Zenodo record of the T1D-UOM version used
        MAX_ANALYSIS_DAYS, RESERVED_DAYS, day_split   days used per participant
        N_MEALS, MEAL_WINDOW_HOURS, LEAD_HOURS, NEGATIVE_RATE_SHIFT_MIN,
        MIN_HIGH_REL_HOURS   method parameters shared by the scripts
        FIGURE_TITLES    titles off for the manuscript figures
        MGDL_PER_MMOL    18.0182, the single unit conversion factor

Notes
    - Demo mode (DEMO=1): inputs from sample_data/, every output under
      demo_output/; the files of the full run are never touched.
    - The Agg backend is set here, so no script opens a figure window.
    - processed/<id>/ is created only in InVivo and InSilico.
    - Same structure as the packages of papers 1 and 2: paths relative to
      this file, participant chosen by environment variable.
"""

# -----------------------------------------------------------#
# Imports and module folder
# -----------------------------------------------------------#
import os
import matplotlib
# Agg draws figures to files only (no window). Set before any script imports
# pyplot, so long runs never stop on a figure window waiting to be closed.
matplotlib.use("Agg")

# Project root (Code3/): this file, pairs.csv, raw/, py-mgipsim/, results/.
# Taken from the location of this file, so the package runs wherever it is
# cloned. Backslashes become slashes so the same paths work on Windows and Linux.
ROOT = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

# Module folder of the script being run: set by 17.ScriptforTestExperiment3.py, otherwise the folder
# the script is run from when that is a folder of the project.
# Order of preference:
#   1. PBT_MODULE_DIR, set by the launcher (or by the module orchestrators);
#   2. the current folder, if it is a folder directly inside the root
#      (a script run by hand from InVivo/, for example);
#   3. the root itself.
_cwd = os.path.abspath(os.getcwd())
# (compared without regard to case: Windows paths may differ only in case,
# for example code3 and Code3)
HERE = os.environ.get("PBT_MODULE_DIR") or (
    _cwd if os.path.normcase(os.path.dirname(_cwd)) == os.path.normcase(ROOT) else ROOT)
HERE = os.path.abspath(HERE).replace("\\", "/")


# --- Input dataset ---
# Zenodo record of the T1D-UOM dataset version used in the paper: the number at
# the end of https://zenodo.org/records/<ID>. Pinning a version keeps the
# analysis reproducible. data/S.GetZenodoData.py downloads it only when no
# unzipped ManchesterCSCoordinatedDiabetesStudy-* folder is in the project root.
ZENODO_RECORD = "17361905"   # T1D-UOM V1.0.4 (doi:10.5281/zenodo.17361905)

# --- Demo mode (sample data in, separate output folder) ---
# DEMO=1 is set by the launcher ("demo") and inherited by every script.
DEMO = os.environ.get("DEMO", "0") == "1"
_in = "sample_data" if DEMO else "raw"        # where the input files are read from
_out = "demo_output" if DEMO else "."         # prefix of every output folder
                                              # ("." = the normal folders)

# The single list of participant pairs (real participant -> virtual patient).
# In demo mode, the list of the demo participant(s) in sample_data/.
PAIRS_FILE = f"{ROOT}/sample_data/pairs_demo.csv" if DEMO else f"{ROOT}/pairs.csv"

# --- Participant pair: real participant -> virtual patient ---
# Set by 17.RunAllZenodo.py; defaults keep single-participant runs working.
# The orchestrators run every step once per row of pairs.csv, passing the pair
# through PATIENT_ID and VIRTUAL_ID; each step reads it here.
_pid = os.environ.get("PATIENT_ID", "2308")
# T1D-UOM IDs are numbers (2308) and clinical IDs are text (Mann01): numbers
# are kept as int because the file names and earlier code use them that way.
id = int(_pid) if _pid.isdigit() else _pid
id2 = os.environ.get("VIRTUAL_ID", "Patient_5")


def raw_dir(pid):
    """Input files of a participant, in the project root (Code3/raw/<id>/)."""
    return f"{ROOT}/{_in}/{pid}/"


def processed_dir(pid):
    """Intermediate files of a participant, inside the module being run
    (InVivo/processed/<id>/ or InSilico/processed/<id>/)."""
    return f"{HERE}/{_out}/processed/{pid}/"


# --- Paths used by the scripts (same variable names as before) ---
# The names (filetoread1, fileToSave, path3, path4...) are kept from the
# original scripts, so every step reads its paths without being rewritten.
filetoread1 = raw_dir(id)                 # UoM*{id}.csv from the T1D-UOM Zenodo record
fileToSave = processed_dir(id)            # all intermediate and final CSVs of this participant
# Final figures and tables of every module go to one results/ folder in the
# project root, with a subfolder per module (results/invivo/, results/insilico/,
# results/metrics/), named after the folder that holds this globals.py.
# (In practice: named after HERE, the module folder being run, in lower case.)
MODULE = os.path.basename(HERE).lower()
path3 = f"{ROOT}/{_out}/results/{MODULE}/figures/"
path4 = f"{ROOT}/{_out}/results/{MODULE}/tables/"

# Virtual patient JSONs inside the py-mgipsim installation (Python 3.12 environment)
# Default: the py-mgipsim clone next to the InVivo and InSilico folders
# (Code3/py-mgipsim/). If it is installed elsewhere, set PYMGIPSIM_PATIENTS
# to its Patients/ folder instead of editing this file.
path = os.environ.get(
    "PYMGIPSIM_PATIENTS",
    f"{ROOT}/py-mgipsim/pymgipsim/VirtualPatient/Models/T1DM/ExtHovorka/Patients/",
)

# Metrics files
# (names read by the metrics scripts; all inside the tables folder)
folder_path = path4
file_path = f"{path4}file.xlsx"
file_name = "Day2.xlsx"

# --- Days used per participant ---
# Up to MAX_ANALYSIS_DAYS days are analysed and the RESERVED_DAYS days that
# follow are kept for the later steps. With fewer days the analysis window
# shrinks so that the reserved days are always available:
#   57 days -> 45 + 2,  47 -> 45 + 2,  30 -> 28 + 2.
# 4.MealBolusDetection and 5.MergeBGClean take their days from here, so they
# always use the same set. The basal profile (4.MergeBasal) is used only for
# matching to the virtual patient and keeps its own rule: its first 45 files.
MAX_ANALYSIS_DAYS = 45
RESERVED_DAYS = 2


def _dates(folder, prefix):
    """Dates (YYYYMMDD) of the per-day files in a folder whose name starts
    with prefix and ends in _YYYYMMDD.csv, sorted from first to last.
    Empty list if the folder does not exist yet."""
    import re
    if not os.path.isdir(folder):
        return []
    out = []
    for f in os.listdir(folder):
        m = re.search(r'_(\d{8})\.csv$', f)   # the 8 digits of the date before .csv
        if f.startswith(prefix) and m:
            out.append(m.group(1))
    return sorted(out)


def day_split(pid):
    """(analysis_dates, reserved_dates) for a participant, as YYYYMMDD strings,
    from the per-day glucose files in processed/<pid>/."""
    dates = _dates(processed_dir(pid), f"UoMGlucose{pid}_")
    # Number of analysis days: at most MAX_ANALYSIS_DAYS, and always leaving
    # RESERVED_DAYS after them (never negative, if there are very few days).
    n = max(0, min(MAX_ANALYSIS_DAYS, len(dates) - RESERVED_DAYS))
    # First n days -> analysis; the next RESERVED_DAYS -> evaluation days.
    return dates[:n], dates[n:n + RESERVED_DAYS]


# --- In-silico stage ---
def simulator_runs_root():
    """simulator_runs/: what goes into and comes out of py-mgipsim, kept by the
    user and never modified by the pipeline (demo_output/simulator_runs/ in demo
    mode). Per participant, simulator_runs/<id>/Simulation_<id2>/ holds the
    basal-only run (simulation_settings.json, state_results.xlsx) and
    Day1|Day2/Before|After/ with the settings and results of each scenario."""
    return f"{ROOT}/{_out}/simulator_runs/"


def sims_root():
    """Working copy of the simulations (InSilico/simulations/, or
    InSilico/demo_output/simulations/ in demo mode), rebuilt by InSilico from
    simulator_runs/ on every run and read by metrics."""
    return f"{ROOT}/InSilico/{_out}/simulations/"


def sim_dir(vid, pid):
    """Simulation_<id2>/ of one real participant: simulation_settings.json and
    state_results.xlsx written by py-mgipsim (used from InSilico/).
    One folder per participant, because two participants can share the same
    virtual patient (for example Patient_2)."""
    return f"{sims_root()}{pid}/Simulation_{vid}/"


def invivo_dir(pid):
    """Outputs of the InVivo module for the same participant, for example
    Days/Day1 and Days/Day2 (used from InSilico/)."""
    return f"{ROOT}/InVivo/{_out}/processed/{pid}/"


# processed/<id>/ is only used by the modules that process participants
# (InVivo, InSilico); data/ and metrics/ write only to results/<module>/.
# The folders are created as soon as globals.py is imported, so no script
# has to create them before saving.
for _d in ((fileToSave, path3, path4) if MODULE in ("invivo", "insilico")
           else (path3, path4)):
    os.makedirs(_d, exist_ok=True)


# -----------------------------------------------------------#
# Method parameters
# -----------------------------------------------------------#
# Set once here and read by every script that uses them, so the steps that
# share a parameter cannot disagree.
N_MEALS = 4                     # largest meals per day: excluded in InVivo (4.MealBolusDetection)
                                # and simulated in the scenarios (S.SaveReservedDays, S.BuildMealScenarios)
MEAL_WINDOW_HOURS = 6           # glucose removed after each of those meals (4.MealBolusDetection)
LEAD_HOURS = 2                  # each basal correction is placed this many hours before the
                                # deviation it corrects, where it was sized (InSilico step 14)
NEGATIVE_RATE_SHIFT_MIN = 120   # a reduction larger than the rate is subtracted this many
                                # minutes earlier, bounded at zero (InSilico step 14)
MIN_HIGH_REL_HOURS = 6          # minimum high-reliability hours to centre the curves on them
                                # (G.CurveCheck, S.CurveAgreement); with fewer, the curves
                                # are centred on all hours instead


# Participant shown in the illustrative figures of the manuscript
# (Figure 1, InVivo/12.MergeRChBasalNoActZenodo.py; Day1/Day2, metrics/G.Figures.py).
ILLUSTRATIVE_ID = "2308"


# Figure titles: journals put them in the caption, so they are off for the
# figures of the manuscript. Set to True to draw them when reviewing plots.
FIGURE_TITLES = False

# -----------------------------------------------------------#
# Unit conversion
# -----------------------------------------------------------#
# Glucose conversion between mmol/L and mg/dL, used by every script of this
# pipeline: mg/dL = mmol/L * MGDL_PER_MMOL. The reported values were produced
# with this factor.
MGDL_PER_MMOL = 18.0182
