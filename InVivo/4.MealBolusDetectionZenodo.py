#Code: 4.MealBolusDetection.py
#Description: Read files of BG, meal and Bolus. Use top 4 meals by CHO per file.
#Created 29th March 2023
#Modified: 21 August 2025
#Author: mbaxdg6

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

start_index = 0
end_index = 45

# -----------------------------------------------------------#
# Collect BG files
# -----------------------------------------------------------#
filesBG = [
    file for file in os.listdir(filetoread)
    if file.startswith(f'UoMGlucose{id}_') and file.endswith('.csv')
]
filesBG.sort(key=lambda x: int(re.search(r'_(\d{8})', x).group(1)))
filesBG = filesBG[start_index:end_index]

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
    dataMeal_top4 = dataMeal.sort_values(by="CHO", ascending=False).head(4).reset_index(drop=True)

    for k in range(len(dataMeal_top4)):
        time_str = str(dataMeal_top4["Key"][k]).strip()
        hour, minute, second = map(int, time_str.split(':'))
        dtH1 = datetime(2010, 12, 1, hour, minute, second)
        dtH2 = dtH1 + timedelta(hours=6)

        # --- Next day condition ---
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
