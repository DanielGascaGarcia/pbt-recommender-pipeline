"""
S.ConvertClinicalData.py
Data stage, step 2 (clinical dataset): convert the text exports of the
clinical dataset (one .txt per participant) into the four input files of the
T1D-UOM schema, so that both datasets go through the same pipeline.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Lists the .txt files directly in the source folder and keeps those
       named like the exports (xt_<...>_man0NN_ol_sleep.txt). Other files are
       listed and skipped; if a participant has more than one export, none of
       them is converted.
    2. Reads, from each export, only the rows of four sections, keeping the
       time stamp and the value(s):
           Glucose_concentration  -> UoMGlucose<id>.csv    bg_ts, value         (mmol/L)
           Enteral_bolus (meal)   -> UoMNutrition<id>.csv  meal_ts, carbs_g     (g)
           Insulin_bolus          -> UoMBolus<id>.csv      bolus_ts, bolus_dose (U)
           Insulin_infusion       -> UoMBasal<id>.csv      basal_ts, basal_dose,
                                                           insulin_kind         (U/h)
    3. Drops meal entries with a negative carbohydrate value (corrections in
       the export, not meals) and writes the four files.
    4. With --check, compares each converted file with the one in raw/<id>/.

Inputs
    globals.ROOT, globals.raw_dir
    "Sleep XT files/" in the project root, or the folder in the CLINICAL_DATA
    environment variable (only the .txt files directly in it)

Outputs
    converted/<id>/UoM*.csv     default (raw/ is not touched)
    raw/<id>/UoM*.csv           with --to-raw

Notes
    - The participant ID comes from the file name: "..._man010_..." -> Mann10.
    - Time stamps (dd/mm/yyyy hh:mm) and values are copied as text, so
      nothing is rounded or reformatted.
    - The header of the export (ID, weight, etc.) and every other section are
      ignored.
    - A meal row whose carbohydrate value is not a number is also dropped,
      because the >= 0 test is False for it.
    - --check compares the files as text, after stripping spaces and the
      blank rows left by spreadsheet editing in the files made by hand. The
      conversion reproduces those hand-made files exactly (48 of 48).
    - --to-raw builds the raw/ root from globals.raw_dir("x") by removing its
      last two characters, so it assumes raw_dir returns ".../raw/<id>".
    - Characters that cannot be decoded as UTF-8 are replaced, not fatal.
    - The clinical dataset is available on request and is not redistributed.

Usage (from the data folder, with the project root on PYTHONPATH)
    python S.ConvertClinicalData.py              convert into converted/<id>/
    python S.ConvertClinicalData.py --to-raw     write into raw/<id>/
    python S.ConvertClinicalData.py --check      convert and compare with raw/<id>/
"""

import glob
import os
import re
import sys

import pandas as pd

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
SOURCE = os.environ.get("CLINICAL_DATA", f"{globals.ROOT}/Sleep XT files")
CONVERTED = f"{globals.ROOT}/converted"

# section of the export -> (file kind, output columns, number of fields kept)
SECTIONS = {
    "Glucose_concentration": ("Glucose", ["bg_ts", "value"], 1),
    "Enteral_bolus (meal)": ("Nutrition", ["meal_ts", "carbs_g"], 1),
    "Insulin_bolus": ("Bolus", ["bolus_ts", "bolus_dose"], 1),
    "Insulin_infusion": ("Basal", ["basal_ts", "basal_dose", "insulin_kind"], 2),
}
ROW = re.compile(r"^\s*(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\t(.*)$")


# -----------------------------------------------------------#
# Helpers
# -----------------------------------------------------------#
def participant_id(path):
    m = re.search(r"man0*(\d+)", os.path.basename(path), re.IGNORECASE)
    return f"Mann{int(m.group(1)):02d}" if m else None


def parse(path):
    """Rows of the four sections used by the pipeline, in file order."""
    out = {k: [] for k in SECTIONS}
    section = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if "****" in line:
                name = line.split("*")[0].strip()
                section = name if name in SECTIONS else None
                continue
            if section is None:
                continue
            m = ROW.match(line)
            if m:
                fields = [x.strip() for x in m.group(2).split("\t")]
                keep = SECTIONS[section][2]
                out[section].append([m.group(1)] + fields[:keep])
    return out


def convert(path, dest_root):
    pid = participant_id(path)
    if pid is None:
        print(f"{os.path.basename(path)}: no participant ID in the file name; skipped")
        return None
    dest = os.path.join(dest_root, pid)
    os.makedirs(dest, exist_ok=True)
    for section, rows in parse(path).items():
        kind, cols, _ = SECTIONS[section]
        df = pd.DataFrame(rows, columns=cols)
        if kind == "Nutrition":
            # Negative carbohydrate entries are corrections in the export, not meals.
            df = df[pd.to_numeric(df["carbs_g"], errors="coerce") >= 0]
        df.to_csv(os.path.join(dest, f"UoM{kind}{pid}.csv"), index=False)
    return pid


def compare(pid):
    """Compare converted/<pid>/ with raw/<pid>/, file by file, as text."""
    res = []
    for kind, cols, _ in SECTIONS.values():
        name = f"UoM{kind}{pid}.csv"
        a, b = os.path.join(CONVERTED, pid, name), os.path.join(globals.raw_dir(pid), name)
        if not os.path.isfile(b):
            res.append(f"{kind}: no file in raw/")
            continue
        x = pd.read_csv(a, dtype=str).fillna("")
        y = pd.read_csv(b, dtype=str).fillna("")
        y.columns = [c.strip() for c in y.columns]
        y = y[[c for c in cols if c in y.columns]].apply(lambda s: s.str.strip())
        y = y[(y != "").any(axis=1)].reset_index(drop=True)   # blank rows left by spreadsheet editing
        if list(x.columns) != list(y.columns):
            res.append(f"{kind}: columns differ {list(y.columns)}")
        elif x.equals(y):
            res.append(f"{kind}: identical ({len(x)} rows)")
        else:
            res.append(f"{kind}: DIFFERENT ({len(x)} converted vs {len(y)} in raw)")
            m = x.merge(y, how="outer", indicator=True)
            only_c = m[m._merge == "left_only"].drop(columns="_merge")
            only_r = m[m._merge == "right_only"].drop(columns="_merge")
            res.append(f"    only in converted: {len(only_c)} rows; only in raw: {len(only_r)} rows")
            for label, part in (("converted", only_c), ("raw", only_r)):
                for _, r in part.head(5).iterrows():
                    res.append(f"      {label:9} " + ", ".join(str(v) for v in r.values))
    return res


# -----------------------------------------------------------#
# Main
# -----------------------------------------------------------#
# Only the exports directly in the source folder are read; subfolders
# (copies, test files) are ignored.
files = sorted(glob.glob(os.path.join(SOURCE, "*.txt")))
# One export per participant, named like xt_<...>_man010_ol_sleep.txt.
# Other .txt files (copies, test files, other studies) are listed and skipped.
valid = re.compile(r"^xt_.*_man0*\d+_ol_sleep\.txt$", re.IGNORECASE)
skipped = [f for f in files if not valid.match(os.path.basename(f))]
files = [f for f in files if valid.match(os.path.basename(f))]
by_id = {}
for f in files:
    by_id.setdefault(participant_id(f), []).append(f)
dupes = {k: v for k, v in by_id.items() if len(v) > 1}
for f in skipped:
    print(f"skipped (name not recognised): {f}")
for k, v in dupes.items():
    print(f"skipped {k}: {len(v)} exports found, keep only one: {v}")
files = [v[0] for k, v in by_id.items() if k not in dupes]
if not files:
    sys.exit(f"No usable .txt files found in {SOURCE}")
# --to-raw: write straight into raw/; otherwise into converted/ for checking.
dest_root = globals.raw_dir("x")[:-2] if "--to-raw" in sys.argv else CONVERTED
for f in files:
    pid = convert(f, dest_root)
    if pid is None:
        continue
    print(f"{pid}: {os.path.basename(f)} -> {os.path.join(dest_root, pid)}")
    if "--check" in sys.argv:
        for line in compare(pid):
            print("    " + line)
