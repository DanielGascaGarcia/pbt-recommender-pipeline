"""
0.GeneratorExamplesZenodo.py
Step 0 (InVivo): split the four input files of one participant into one file
per calendar day, the unit every later step works on.

Created: March 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each of UoMGlucose, UoMNutrition, UoMBolus and UoMBasal:
        1. reads the time stamp of every row (dd/mm/yyyy hh:mm, with or
           without seconds);
        2. groups the rows by calendar date;
        3. writes one file per date with the time of day as Key (HH:MM:SS)
           and the value column(s).
    Nutrition is reduced to Key and CHO, locating the carbohydrate column by
    its name (carbs_g), because the two datasets store meals with different
    columns.

Inputs
    globals.id, globals.filetoread1 (raw/<id>/), globals.fileToSave
    raw/<id>/UoM{Glucose,Nutrition,Bolus,Basal}<id>.csv

Outputs (in processed/<id>/)
    UoMGlucose<id>_<YYYYMMDD>.csv     Key, BGValue
    UoMNutrition<id>_<YYYYMMDD>.csv   Key, CHO
    UoMBolus<id>_<YYYYMMDD>.csv       Key, bolus_dose
    UoMBasal<id>_<YYYYMMDD>.csv       Key, basal_dose, insulin_kind

Notes
    - Rows with fewer fields than the output columns are skipped silently
      (for Basal, a row without insulin_kind would be skipped).
    - Rows whose time stamp cannot be read are printed and skipped.
    - Values are copied as text; nothing is rounded or converted. Glucose
      stays in mmol/L.
    - Every date with data gets a file; which dates are analysed is decided
      later by globals.day_split (4.MealBolusDetection, 5.MergeBGClean).
"""

import csv
import os
from collections import defaultdict
from datetime import datetime
import globals
# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#


# --- Configurable global variable ---
# id: participant whose files are split (PATIENT_ID, set by the orchestrator).
id = globals.id;

# --- Folder paths ---
# filetoread: raw/<id>/ (the four input files).
# fileToSave: processed/<id>/ (one file per day and type).
filetoread = globals.filetoread1;
fileToSave = globals.fileToSave;

# Ensure output directory exists
os.makedirs(fileToSave, exist_ok=True)

# -----------------------------------------------------------#
# Utility function: parse datetimes flexibly
# -----------------------------------------------------------#
def parse_datetime(ts_str):
    # Formats accepted: without seconds, with seconds, and with two spaces before
    # the time (written by some exports). The first one that reads the text wins.
    ts_str = ts_str.strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y  %H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    print(f"Could not parse datetime: {ts_str}")
    return None

# -----------------------------------------------------------#
# General-purpose processor for splitting files by date
# -----------------------------------------------------------#
def process_csv_by_date(input_path, output_prefix, headers, timestamp_index, row_processor):
    # data_by_date: date (YYYYMMDD) -> list of the output rows of that date.
    data_by_date = defaultdict(list)

    if os.path.isfile(input_path):
        with open(input_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            # Skip the header row of the input.
            header = next(reader, None)
            print(f"[{output_prefix}] Header: {header}")

            for row in reader:
                # A row with fewer fields than output columns is skipped.
                if len(row) < len(headers):
                    continue
                dt = parse_datetime(row[timestamp_index])
                if not dt:
                    continue
                # Date of the row -> which daily file; time of day -> Key.
                date_key = dt.strftime("%Y%m%d")
                formatted_ts = dt.strftime("%H:%M:%S")  # Only time portion
                # row_processor builds the output row (Key + value columns) from the time and
                # the original row.
                processed_row = row_processor(formatted_ts, row)
                data_by_date[date_key].append(processed_row)

        print(f"[{output_prefix}] Total unique dates: {len(data_by_date)}")

        # One file per date, in date order: <prefix><id>_<YYYYMMDD>.csv, with header.
        for date_key in sorted(data_by_date.keys()):
            filename = f"{output_prefix}{id}_{date_key}.csv"
            path = os.path.join(fileToSave, filename)
            with open(path, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data_by_date[date_key])
            print(f"[{output_prefix}] Saved: {path}")
    else:
        print(f"[{output_prefix}] File not found: {input_path}")

# -----------------------------------------------------------#
# Process Glucose
# -----------------------------------------------------------#
# Glucose: Key, BGValue (column 1 of the input, mmol/L).
process_csv_by_date(
    input_path=os.path.join(filetoread, f"UoMGlucose{id}.csv"),
    output_prefix="UoMGlucose",
    headers=["Key", "BGValue"],
    timestamp_index=0,
    row_processor=lambda ts, row: [ts, row[1].strip()]
)

# -----------------------------------------------------------#
# Process Nutrition
# -----------------------------------------------------------#
# The two datasets store meals differently:
#   T1D-UOM (Zenodo): meal_ts, meal_type, meal_tag, carbs_g, prot_g, fat_g, fibre_g
#   clinical dataset: meal_ts, carbs_g
# Only the time and the carbohydrates are used downstream (4.MealBolusDetection
# keeps the 4 largest meals by CHO), so the carbs column is located by NAME and
# the output always has the same two columns: Key, CHO.
# carbs_g is found by name; the clinical files have no meal_type/tag columns.
# Position of a column from its name, read from the header of the file
# (utf-8-sig removes a byte-order mark that would change the first name).
# Stops with a message if the column is not there.
def column_index(path, name):
    with open(path, newline='', encoding='utf-8-sig') as f:
        header = [h.strip() for h in next(csv.reader(f))]
    if name not in header:
        raise SystemExit(f"Column '{name}' not found in {path}; header is {header}")
    return header.index(name)

nutrition_path = os.path.join(filetoread, f"UoMNutrition{id}.csv")
if os.path.isfile(nutrition_path):
    carbs_col = column_index(nutrition_path, "carbs_g")
    process_csv_by_date(
        input_path=nutrition_path,
        output_prefix="UoMNutrition",
        headers=["Key", "CHO"],
        timestamp_index=0,
        row_processor=lambda ts, row: [ts, row[carbs_col].strip()]
    )
else:
    print(f"[UoMNutrition] File not found: {nutrition_path}")

# -----------------------------------------------------------#
# Process Bolus
# -----------------------------------------------------------#
# Bolus: Key, bolus_dose (column 1).
process_csv_by_date(
    input_path=os.path.join(filetoread, f"UoMBolus{id}.csv"),
    output_prefix="UoMBolus",
    headers=["Key", "bolus_dose"],
    timestamp_index=0,
    row_processor=lambda ts, row: [ts, row[1].strip()]
)

# -----------------------------------------------------------#
# Process Basal
# -----------------------------------------------------------#
# Basal: Key, basal_dose (column 1) and insulin_kind (column 2: R = pump
# rate, L = long-acting injection).
process_csv_by_date(
    input_path=os.path.join(filetoread, f"UoMBasal{id}.csv"),
    output_prefix="UoMBasal",
    headers=["Key", "basal_dose", "insulin_kind"],
    timestamp_index=0,
    row_processor=lambda ts, row: [ts, row[1].strip(), row[2].strip()]
)
