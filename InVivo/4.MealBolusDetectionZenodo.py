"""
4.MealBolusDetectionZenodo.py   (header of the original file reads 4.MealBolusDetection.py)
Step 4 (InVivo, meal-based branch): remove the glucose readings that follow
the main meals of each analysis day.

Created: 29 March 2023
Modified: 21 August 2025
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Keeps only the analysis days given by globals.day_split (up to 45
       days; the next 2 are reserved for the simulated evaluation).
    2. Writes a working copy of each daily glucose file (prefix "_") with
       columns Key, BGValue, Flag, ValueCh, BGValue2.
    3. For each day with a meal file, takes its 4 largest meals by
       carbohydrate (CHO) and blanks BGValue (Flag = 5) from the meal time
       to 6 h after it.
    4. If the 6-h window passes midnight, the part after 00:00 is blanked in
       the working copy of the next calendar day, when that file exists.

Inputs
    globals.id, globals.fileToSave, globals.day_split
    processed/<id>/UoMGlucose<id>_<date>.csv, UoMNutrition<id>_<date>.csv,
    UoMBolus<id>_<date>.csv   (0.GeneratorExamplesZenodo.py)

Outputs (in processed/<id>/)
    _UoMGlucose<id>_<date>.csv   one per analysis day
        BGValue    glucose after removal (NaN inside the meal windows)
        BGValue2   glucose before removal
        Flag       5 inside a meal window, 0 otherwise
        ValueCh    int(BGValue2) inside a meal window, 0 otherwise

Notes
    - Only the 4 largest meals of each day open a window; smaller meals do
      not. Across the analysis days they hold 93% of the recorded
      carbohydrate (S.MealCoverage.py).
    - Days without a meal file keep all their readings.
    - The window after midnight is applied only to the next calendar day
      (date + 1) and only if it is an analysis day; after a gap in the record
      nothing is carried.
    - ValueCh stores int(), which truncates the mmol/L value; the column is
      not used by later steps.
    - Bolus files are listed but not used.
    - Times are compared as "HH:MM:SS" text, which orders correctly.
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
import re
import globals

# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
id = globals.id

filetoread = globals.fileToSave;
fileToSave = globals.fileToSave;

# Days come from globals.day_split, shared with 5.MergeBGClean.
# Analysis and reserved days come from globals.day_split, shared with 5.MergeBGClean.
analysis_dates, reserved_dates = globals.day_split(id)
keep = set(analysis_dates)

# -----------------------------------------------------------#
# Collect BG files
# -----------------------------------------------------------#
filesBG = [
    file for file in os.listdir(filetoread)
    if file.startswith(f'UoMGlucose{id}_') and file.endswith('.csv')
]
filesBG.sort(key=lambda x: int(re.search(r'_(\d{8})', x).group(1)))
filesBG = [f for f in filesBG if re.search(r'_(\d{8})', f).group(1) in keep]

# Collect Bolus files
filesBolus = [
    file for file in os.listdir(filetoread)
    if file.startswith(f'UoMBolus{id}_') and file.endswith('.csv')
]
filesBolus.sort(key=lambda x: int(re.search(r'_(\d{8})', x).group(1)))

# Collect Meal files
filesMeals = [
    file for file in os.listdir(filetoread)
    if file.startswith(f'UoMNutrition{id}_') and file.endswith('.csv')
]
filesMeals.sort(key=lambda x: int(re.search(r'_(\d{8})', x).group(1)))

# -----------------------------------------------------------#
# Main program - process each BG file (create processed with "_")
# -----------------------------------------------------------#
for filename in filesBG:
    file_path = os.path.join(filetoread, filename)
    dataBG = pd.read_csv(file_path)

    out_file = os.path.join(filetoread, "_" + filename)
    with open(out_file, 'w') as fout:
        for l in range(len(dataBG)):
            BGdt = datetime(2010, 12, 1,
                            int(dataBG["Key"][l][0:2]),
                            int(dataBG["Key"][l][3:5]),
                            int(dataBG["Key"][l][6:9]))
            fout.write(f"{BGdt.strftime('%H:%M:%S')},{dataBG['BGValue'][l]},0,0,{dataBG['BGValue'][l]}\n")

    df = pd.read_csv(out_file, header=None)
    df.rename(columns={0: 'Key', 1: 'BGValue', 2: 'Flag',
                       3: 'ValueCh', 4: 'BGValue2'}, inplace=True)
    df.to_csv(out_file, index=False)

# -----------------------------------------------------------#
# Match BG with Meals (only top 4 meals)
# -----------------------------------------------------------#
for bg_file in filesBG:
    match = re.search(r'_(\d{8})', bg_file)
    if not match:
        print(f"Could not extract date from BG filename: {bg_file}")
        continue

    date_str = match.group(1)
    nutrition_filename = f'UoMNutrition{id}_{date_str}.csv'

    if nutrition_filename not in filesMeals:
        print(f"Matching Nutrition file not found for: {bg_file}")
        continue

    # Paths
    bg_proc_path = os.path.join(filetoread, "_" + bg_file)
    nutrition_path = os.path.join(filetoread, nutrition_filename)

    dataBG_proc = pd.read_csv(bg_proc_path)
    dataMeal = pd.read_csv(nutrition_path)

    # Keep only top 4 meals by CHO
    # The 4 largest meals by carbohydrate open a 6-h removal window each.
    dataMeal_top4 = dataMeal.sort_values(by="CHO", ascending=False).head(globals.N_MEALS).reset_index(drop=True)

    for k in range(len(dataMeal_top4)):
        time_str = str(dataMeal_top4["Key"][k]).strip()
        hour, minute, second = map(int, time_str.split(':'))
        dtH1 = datetime(2010, 12, 1, hour, minute, second)
        dtH2 = dtH1 + timedelta(hours=globals.MEAL_WINDOW_HOURS)

        # --- Next day condition ---
        # Window passes midnight: blank 00:00 -> end of window in the next day's copy.
        if dtH2 > datetime(2010, 12, 1, 23, 59, 59):
            dtH3 = datetime(2010, 12, 1, 0, 0, 0)
            dtH4 = dtH2
            print("Next day of:", bg_file)

            current_date = datetime.strptime(date_str, "%Y%m%d")
            next_date = current_date + timedelta(days=1)
            next_date_str = next_date.strftime("%Y%m%d")
            next_day_bg_file = f'_UoMGlucose{id}_{next_date_str}.csv'
            next_day_path = os.path.join(filetoread, next_day_bg_file)

            if os.path.exists(next_day_path):
                dataBG1 = pd.read_csv(next_day_path)
                for l in range(len(dataBG1)):
                    BGdt = datetime(2010, 12, 1,
                                    int(dataBG1["Key"][l][0:2]),
                                    int(dataBG1["Key"][l][3:5]),
                                    int(dataBG1["Key"][l][6:9]))
                    if dtH3.strftime('%H:%M:%S') <= BGdt.strftime('%H:%M:%S') <= dtH4.strftime('%H:%M:%S'):
                        dataBG1.loc[l, 'Flag'] = 5
                        dataBG1.loc[l, 'ValueCh'] = int(dataBG1.loc[l, 'BGValue2'])
                        dataBG1.loc[l, 'BGValue'] = np.nan
                dataBG1.to_csv(next_day_path, index=False)
            else:
                print(f"Next day BG file not found: {next_day_bg_file}")

            dtH2 = datetime(2010, 12, 1, 23, 59, 59)

        # --- Same-day condition ---
        # Same day: blank from the meal time to the end of the window (or 23:59:59).
        for l in range(len(dataBG_proc)):
            BGdt = datetime(2010, 12, 1,
                            int(dataBG_proc["Key"][l][0:2]),
                            int(dataBG_proc["Key"][l][3:5]),
                            int(dataBG_proc["Key"][l][6:9]))
            if dtH1.strftime('%H:%M:%S') <= BGdt.strftime('%H:%M:%S') <= dtH2.strftime('%H:%M:%S'):
                dataBG_proc.loc[l, 'Flag'] = 5
                dataBG_proc.loc[l, 'ValueCh'] = int(dataBG_proc.loc[l, 'BGValue2'])
                dataBG_proc.loc[l, 'BGValue'] = np.nan

    # Save updated BG file (processed)
    dataBG_proc.to_csv(bg_proc_path, index=False)
