"""
8.RelativeChangeZenodo.py
Step 8 (InVivo, meal-based branch): compute, for each day and hour, how much
glucose changed within the hour.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. In each hourly file, subtracts from every day column its first valid
       reading of that hour (RChBGValue<j>), so each hour starts at 0.
    2. Takes the last valid value of each day column: the change within the
       hour for that day, in mmol/L.

Inputs
    globals.id, globals.fileToSave
    processed/<id>/BGHourInterpolated<id><i>To<i+1>.csv   (7.InterpolationBGHourlyZenodo.py)

Outputs
    processed/<id>/BGHourRelativeChange<id><i>To<i+1>.csv              changes, minute by minute
    processed/<id>/BGHourRelativeChange<id><i>To<i+1>lastValues.csv    one value per day

Notes
    - The first loop runs over len(columns) - 2 day columns because the
      hourly files carry the saved index and Key; the second loop uses
      len(columns) - 1 because its input has only Key and the day columns.
    - A day without any reading in the hour gives " " as its last value.
      When the file is read again, that line is taken as blank and skipped,
      so the remaining values move up: the rows of a lastValues file are not
      aligned with day numbers. The hourly distributions (9.Boxplot) and the
      counts per hour (10.PivotGeneratormedians) are not affected.
    - Values stay in mmol/L (the conversions to mg/dL are commented out).
"""

import datetime 
import pandas as pd
import os
from datetime import datetime,timedelta
import datetime 
from matplotlib import pyplot as plt
import numpy as np
import csv
pd.options.mode.chained_assignment = None  # default='warn'
import globals
id=globals.id;

path2= globals.fileToSave;
fileToRead="BGHourInterpolated"+str(id);
fileToSave="BGHourRelativeChange"+str(id);
# -----------------------------------------------------------#
#             Substract the staring point
# -----------------------------------------------------------#

# len(columns) - 2: the hourly files carry the saved index and Key.
dmean = pd.DataFrame();
for i in range(24):
    data = pd.read_csv(str(path2)+str(fileToRead)+str(i)+str("To")+str(i+1)+".csv"); 
    # print(len(data.columns));
    dt = pd.DataFrame();
    dt=data[['Key']];
    for j in range(len(data.columns)-2):
    #    dt1=data['BGValue'+str(j)].diff().to_frame(name='DBGValue'+str(j));
        # serie = data['BGValue'+str(j)].to_frame(name='RChBGValue'+str(j)).div(18.0182).squeeze();
        serie = data['BGValue'+str(j)].to_frame(name='RChBGValue'+str(j)).squeeze();
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

# Last valid value of each day = change within the hour; ' ' if the day has no reading.
for i in range(24):
    data = pd.read_csv(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+".csv"); 
    # print(data)
    dt=[];
    #2 for Ohio Dataset, 1 for Simglucose
    for j in range(len(data.columns)-1):
        # print(j)
        try:
            serie = data['RChBGValue'+str(j)].to_frame(name='RChBGLValue'+str(j)).squeeze();
            last_val=serie.loc[serie.last_valid_index()];
            # print(last_val);
            dt1=last_val;
        except:
            # print("No key");
            dt1=" ";
        dt.append(dt1); 
    dt=pd.DataFrame(dt, columns=['Last_values'])  
    dt.to_csv(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+"lastValues"+".csv",index=False);
    print(dt);
