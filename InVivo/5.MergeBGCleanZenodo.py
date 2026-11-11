"""
5.MergeBGCleanZenodo.py
Step 5 (InVivo, meal-based branch): join the cleaned daily glucose files of
one participant onto the minute grid, one day per column.

Created: 11 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Takes the working copies written by 4.MealBolusDetection
    (_UoMGlucose<id>_<date>.csv) of the analysis days, keeps Key and
    BGValue, and left-joins them, as BGValue0, BGValue1, ..., onto the
    1,440-minute grid of 3.PivotGenerator. Readings removed around meals are
    already NaN.

Inputs
    globals.id, globals.fileToSave, globals.day_split
    processed/<id>/PivotBG_wCN.csv
    processed/<id>/_UoMGlucose<id>_<date>.csv   (4.MealBolusDetectionZenodo.py)

Output
    processed/<id>/BGwNMLeftJoined<id>.csv
        (unnamed index), Key, BGValue0, BGValue1, ... (one column per day)

Notes
    - The file is saved WITH the pandas index, so it has two non-data
      columns ("Unnamed: 0" and Key) when read again. 6.SplitHours reads Key
      as the second field, 8.RelativeChange subtracts 2 from the column
      count, and 0.InterpolationBGHourlyData keeps only the BGValue* columns
      (before that fix, the index column entered its median).
    - Days are in date order (files sorted by the date in the name).
    - Keys are joined as full "HH:MM:SS"; CGM readings every 5 min leave most
      minutes of each day empty.
    - With fewer than 2 analysis days, output1 is never created and the
      final line fails with a NameError.
    - Working copies left from an earlier run are ignored: only the dates of
      globals.day_split are used.
"""

import datetime 
import pandas as pd
import os
from datetime import datetime,timedelta
import datetime 
from matplotlib import pyplot as plt
import numpy as np
import re
import globals
# Parameters


filesBG=[];
# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
# --- Configurable global variable ---
id=globals.id;

# --- Folder paths ---
filetoread = globals.fileToSave
PathToSave= globals.fileToSave
fileToSave="BGwNMLeftJoined"+str(id)+".csv";

# -----------------------------------------------------------#
#                  Files of BG
# -----------------------------------------------------------#

# Find and collect all matching BG files
for file in os.listdir(filetoread):
    if file.startswith(f'_UoMGlucose{id}_') and file.endswith('.csv'):
        filesBG.append(file)

# Sort files by the date part in filename (YYYYMMDD)
filesBG.sort(key=lambda x: int(re.search(r'_(\d{8})', x).group(1)))

# Only the analysis days of globals.day_split, the same set processed by
# 4.MealBolusDetection. Processed files left in the folder by an earlier run
# are ignored.
analysis_dates, _ = globals.day_split(id)
keep = set(analysis_dates)
filesBG = [f for f in filesBG if re.search(r'_(\d{8})', f).group(1) in keep]


# Left join: the 1,440 minutes are kept; minutes without a reading stay NaN.
if len(filesBG)>=2:
    # reading two csv files
    data1 = pd.read_csv(str(filetoread)+'PivotBG_wCN'+'.csv')
    data2 = pd.read_csv(str(filetoread)+filesBG[0],usecols = ['Key','BGValue']);
    data2.rename(columns = {'BGValue':'BGValue'+str(0)}, inplace = True);
    data1['Key']=data1['Key'].str.strip();
    data2['Key']=data2['Key'].str.strip();
    output1 = pd.merge(data1,data2,suffixes=('',''),on='Key',how='left');
    for j in range(len(filesBG)-1):
            data3 = pd.read_csv(str(filetoread)+filesBG[j+1],usecols = ['Key','BGValue']);
            data3.rename(columns = {'BGValue':'BGValue'+str(j+1)}, inplace = True);
            data3['Key']=data3['Key'].str.strip();
            output1 = pd.merge(output1,data3,suffixes=('',''),on='Key',how='left');
# Saving the result
# Saved WITH the index (column 'Unnamed: 0' when read again); see Notes.
output1.to_csv(str(PathToSave)+str(fileToSave));
