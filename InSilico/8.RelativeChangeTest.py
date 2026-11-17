"""
8.RelativeChangeTest.py
Step 8 (InSilico): change of the simulated glucose within each hour.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Same as InVivo/8.RelativeChangeZenodo.py: subtracts the first value of
    each hour and keeps the last value, in mg/dL.

Inputs / Outputs
    BGHourInterpolated<id2><i>To<i+1>.csv
        -> BGHourRelativeChange<id2><i>To<i+1>.csv and ...lastValues.csv

Notes
    - Values are in mg/dL here (mmol/L in InVivo).
    - The steps of this chain are the InVivo steps applied to ONE simulated
      day, in mg/dL, with files named by the virtual patient (id2) inside
      processed/<id>/ of the participant.
"""

import datetime 
import pandas as pd
import os
from datetime import datetime,timedelta
import datetime 
from matplotlib import pyplot as plt
import numpy as np
import csv
# Silence the pandas warning about writing into a slice (dt is built from
# data[['Key']]).
pd.options.mode.chained_assignment = None  # default='warn'
import globals
# --- Configurable global variable ---
id=globals.id;
id2=globals.id2;
# path2: processed/<id>/.
path2=globals.fileToSave
fileToRead="BGHourInterpolated"+str(id2);
fileToSave="BGHourRelativeChange"+str(id2);
# -----------------------------------------------------------#
#             Substract the staring point
# -----------------------------------------------------------#

# Part 1: change within each hour. For each hour file and each day column
# BGValue<j>, subtract the first valid value of that hour, so every hour
# starts at 0. Result: RChBGValue<j>, in mg/dL here.
dmean = pd.DataFrame();
for i in range(24):
    data = pd.read_csv(str(path2)+str(fileToRead)+str(i)+str("To")+str(i+1)+".csv"); 
    # print(len(data.columns));
    dt = pd.DataFrame();
    dt=data[['Key']];
    # len(columns) - 2: the file has the saved index (Unnamed: 0), Key, and one
    # BGValue column per day.
    for j in range(len(data.columns)-2):
    #    dt1=data['BGValue'+str(j)].diff().to_frame(name='DBGValue'+str(j));
        # serie = data['BGValue'+str(j)].to_frame(name='RChBGValue'+str(j)).div(18.0182).squeeze();
        serie = data['BGValue'+str(j)].to_frame(name='RChBGValue'+str(j)).squeeze();
        # If the day has no value in this hour (first_valid_index is None), the
        # subtraction fails and the column is kept as it is (empty).
        try:
            first_val=serie.loc[serie.first_valid_index()];
            dt1=data['BGValue'+str(j)].to_frame(name='RChBGValue'+str(j))-first_val;
            # print(data['BGValue'+str(j)].to_frame(name='DBGValue'+str(j)).div(18.0182)-first_val);
        except:
            dt1=data['BGValue'+str(j)].to_frame(name='RChBGValue'+str(j));
            # dt1=data['BGValue'+str(j)].to_frame(name='RChBGValue'+str(j)).div(18.0182);
            # print("Variable missing");
        dt['RChBGValue'+str(j)] = dt1['RChBGValue'+str(j)].copy();
    dt.to_csv(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+".csv",index=False);


# -----------------------------------------------------------#
#             Obtaining the last point.
# -----------------------------------------------------------#

# Part 2: the last value of each hour = net change of glucose over that
# hour; one value per day.
for i in range(24):
    data = pd.read_csv(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+".csv"); 
    # print(data)
    dt=[];
    #2 for Ohio Dataset, 1 for Simglucose
    # len(columns) - 1: Key plus one RChBGValue column per day.
    for j in range(len(data.columns)-1):
        # print(j)
        # Last valid value of the hour; a blank if the day has no data in it.
        try:
            serie = data['RChBGValue'+str(j)].to_frame(name='RChBGLValue'+str(j)).squeeze();
            last_val=serie.loc[serie.last_valid_index()];
            # print(last_val);
            dt1=last_val;
        except:
            # print("No key");
            dt1=" ";
        dt.append(dt1); 
    # Saved as ...lastValues.csv: one row per day.
    dt=pd.DataFrame(dt, columns=['Last_values'])  
    dt.to_csv(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+"lastValues"+".csv",index=False);
    print(dt);
