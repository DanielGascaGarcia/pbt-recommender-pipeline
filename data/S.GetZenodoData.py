"""
S.GetZenodoData.py
Data stage, step 1 (public dataset): fetch the T1D-UOM dataset and place the
input files of every public participant in raw/<id>/.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Chooses the source of the data, in this order:
         - a path given with --local (a .zip or an unzipped folder);
         - an unzipped copy of the dataset in the project root
           (ManchesterCSCoordinatedDiabetesStudy-*), so no internet is needed;
         - otherwise, the Zenodo record pinned in globals.ZENODO_RECORD,
           downloaded once to data_cache/ and checked against the MD5
           checksum published by Zenodo.
    2. Indexes every file of the source by its name.
    3. For each participant of pairs.csv whose source is "zenodo", copies its
       four input files (UoMGlucose, UoMNutrition, UoMBolus, UoMBasal) into
       raw/<id>/.

Inputs
    globals.ZENODO_RECORD, globals.PAIRS_FILE, globals.ROOT, globals.raw_dir
    <ROOT>/pairs.csv                       participants and their source
    the dataset: --local path, local folder, or Zenodo record

Outputs
    <ROOT>/raw/<id>/UoM{Glucose,Nutrition,Bolus,Basal}<id>.csv
    <ROOT>/data_cache/<zip of the record>  (only when downloaded)

Notes
    - Files are matched by name only, so the folder layout inside the zip
      does not matter. A name found more than once is not copied (the script
      does not guess which copy is right) and is reported as a problem.
    - Any problem (missing or repeated file) ends the script with exit code 1
      after listing all of them.
    - The MD5 check applies to the downloaded zip only; a local folder or a
      --local path is used as it is.
    - Files already in raw/<id>/ are overwritten. S.CleanRawData.py then
      treats them as new originals (see its notes).
    - If pairs.csv has no "source" column, every ID is taken as public.
    - Participants of the clinical dataset are not on Zenodo; they come from
      S.ConvertClinicalData.py.
    - Only the Python standard library is used.

Usage (from the data folder, with the project root on PYTHONPATH)
    python S.GetZenodoData.py                  local folder if present, otherwise Zenodo
    python S.GetZenodoData.py --local <path>   a specific .zip or unzipped folder
"""

import glob
import hashlib
import json
import os
import shutil
import sys
import urllib.request
import zipfile

import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
# Zenodo record of the dataset version used in the paper, set in globals.py.
# Pinning a specific version keeps the analysis reproducible; "latest" would
# silently change the input data whenever a new version is published.
ZENODO_RECORD = globals.ZENODO_RECORD

HERE = globals.HERE
PAIRS_FILE = globals.PAIRS_FILE
ROOT = globals.ROOT               # project root (Code3/): input data shared by the modules
CACHE_DIR = f"{ROOT}/data_cache"   # downloaded zip is kept here to avoid re-downloading

# The pipeline only reads these four data categories (see 0.GeneratorExamplesZenodo.py).
KINDS = ["Glucose", "Nutrition", "Bolus", "Basal"]


# -----------------------------------------------------------#
# Helpers
# -----------------------------------------------------------#
def load_ids():
    """
    Return the participant IDs (column 'id') from pairs.csv whose source is
    'zenodo'. Participants from the clinical dataset are not on Zenodo and are skipped.
    """
    with open(PAIRS_FILE, encoding="utf-8") as f:
        lines = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
    header = [h.strip() for h in lines[0].split(",")]
    col_id = header.index("id")
    col_src = header.index("source") if "source" in header else None
    ids = []
    for l in lines[1:]:
        fields = [x.strip() for x in l.split(",")]
        if col_src is None or fields[col_src].lower() == "zenodo":
            ids.append(fields[col_id])
    return ids


def md5_of(path):
    """MD5 checksum of a file, read in chunks so large files do not fill memory."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_record_zip(record):
    """
    Download the zip file of a Zenodo record (or reuse the cached copy) and
    verify it against the MD5 checksum published by Zenodo.
    Returns the local path of the zip.
    """
    # 1) Ask the Zenodo API which files the record contains.
    api_url = f"https://zenodo.org/api/records/{record}"
    with urllib.request.urlopen(api_url) as r:
        meta = json.load(r)

    version = meta.get("metadata", {}).get("version", "unknown")
    files = meta.get("files", [])
    if isinstance(files, dict):            # newer API layout
        files = list(files.get("entries", {}).values())
    zips = [f for f in files if f["key"].endswith(".zip")]
    if len(zips) != 1:
        sys.exit(f"Expected exactly one zip in record {record}, found {len(zips)}.")

    key = zips[0]["key"]
    expected_md5 = zips[0].get("checksum", "").replace("md5:", "")
    print(f"Zenodo record {record}, version {version}: {key}")

    # 2) Reuse the cached zip if it is already there and intact.
    os.makedirs(CACHE_DIR, exist_ok=True)
    local_zip = os.path.join(CACHE_DIR, os.path.basename(key))
    if os.path.isfile(local_zip) and md5_of(local_zip) == expected_md5:
        print(f"Using cached copy: {local_zip}")
        return local_zip

    # 3) Otherwise download it and check the checksum.
    url = f"https://zenodo.org/records/{record}/files/{key}?download=1"
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, local_zip)
    if expected_md5 and md5_of(local_zip) != expected_md5:
        os.remove(local_zip)
        sys.exit("Checksum mismatch: the download is incomplete or corrupted. Try again.")
    print("Checksum OK.")
    return local_zip


def index_source(source):
    """
    Map every file name in the source (zip or folder) to where it lives.
    Files are matched by name only, so the internal folder layout does not matter.
    Returns {file_name: [locations]}.
    """
    index = {}
    if os.path.isfile(source) and source.lower().endswith(".zip"):
        with zipfile.ZipFile(source) as z:
            for member in z.namelist():
                if not member.endswith("/"):
                    index.setdefault(os.path.basename(member), []).append(member)
    elif os.path.isdir(source):
        for p in glob.glob(os.path.join(source, "**", "*"), recursive=True):
            if os.path.isfile(p):
                index.setdefault(os.path.basename(p), []).append(p)
    else:
        sys.exit(f"Source not found or not a .zip/folder: {source}")
    return index


def copy_file(source, location, dest_dir):
    """Copy one file from the zip (member name) or the folder (path) into dest_dir."""
    target = os.path.join(dest_dir, os.path.basename(location))
    if os.path.isfile(source):                       # zip source
        with zipfile.ZipFile(source) as z, z.open(location) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)
    else:                                            # folder source
        shutil.copy2(location, target)


# -----------------------------------------------------------#
# Main
# -----------------------------------------------------------#
# Choose the data source: a local zip/folder, or the pinned Zenodo record.
local_dirs = sorted(d for d in glob.glob(f"{ROOT}/ManchesterCSCoordinatedDiabetesStudy-*")
                    if os.path.isdir(d))
if len(sys.argv) > 2 and sys.argv[1] == "--local":
    source = sys.argv[2]
elif len(local_dirs) == 1:
    # Preferred over downloading: same files, no internet needed.
    # An unzipped copy of the dataset sits in the project root: no internet needed.
    source = local_dirs[0]
    print(f"Using local dataset folder: {source}")
elif len(local_dirs) > 1:
    sys.exit("Several dataset folders found; keep one or use --local <path>: "
             + ", ".join(os.path.basename(d) for d in local_dirs))
else:
    source = download_record_zip(ZENODO_RECORD)

# Map file names to their location in the zip or folder.
index = index_source(source)
problems = []

# For every participant in pairs.csv, copy its four input files into raw/{id}/.
for pid in load_ids():
    dest = globals.raw_dir(pid)
    os.makedirs(dest, exist_ok=True)
    for kind in KINDS:
        name = f"UoM{kind}{pid}.csv"
        hits = index.get(name, [])
        if len(hits) == 1:
            copy_file(source, hits[0], dest)
            print(f"{pid}: {name} -> {dest}")
        elif not hits:
            problems.append(f"{pid}: {name} not found")
        else:
            # Ambiguous: do not guess which copy is the right one.
            problems.append(f"{pid}: {name} found {len(hits)} times, not copied")

if problems:
    print("\nProblems:")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("\nAll files in place.")
